import time
import re
import asyncio
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Header
from fastapi.responses import FileResponse
from app.models.payment import (
    InitiateCBEPaymentRequest,
    InitiateCBEPaymentResponse,
    SubmitCBETransactionRequest,
    SubmitCBETransactionResponse,
    CBEWebhookPayload,
    CBEWebhookResponse,
    CheckTransactionStatusResponse
)
from app.services.storage_service import storage_service
from app.services.pricing_engine import PricingEngine
from app.services.cbe_email_parser import cbe_email_parser
from app.services.cbe_imap_service import cbe_imap_service, safe_print
from app.config import settings

router = APIRouter(prefix="/api", tags=["cbe_payment"])

# Safe alphanumeric + underscore validator
SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")

# In-memory transaction registry fallback
_local_transactions_db: Dict[str, Dict[str, Any]] = {}

@router.get("/cbe-details")
def get_cbe_details():
    """
    Returns the official Commercial Bank of Ethiopia (CBE) account details and IMAP status.
    """
    imap_status = cbe_imap_service.get_status_info()
    return {
        "status": "success",
        "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
        "cbe_account_name": settings.CBE_ACCOUNT_NAME,
        "imap_configured": imap_status["configured"],
        "imap_user": imap_status["user"]
    }

@router.post("/initiate-cbe-payment", response_model=InitiateCBEPaymentResponse)
@router.post("/payment/initiate-cbe", response_model=InitiateCBEPaymentResponse)
async def initiate_cbe_payment(payload: InitiateCBEPaymentRequest):
    """
    Accepts session_id, calculates the exact total_fee dynamically based on
    total formatted pages using the ETHIOFORMAT_RULES.md pricing formula
    (50 ETB base up to 20 pages + 1.50 ETB / extra page),
    creates a 'pending' record in Supabase / local registry,
    and returns the CBE account details + expected amount to the frontend.
    """
    safe_print(f"[CBE Payment] Initiate payment requested for session: {payload.session_id}")

    if not SAFE_ID_REGEX.match(payload.session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format."
        )

    session = storage_service.get_session(payload.session_id)
    if not session:
        safe_print(f"[CBE Payment] ❌ Session {payload.session_id} not found in storage.")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Session not found. Please upload and preview your document again."
        )

    total_pages = int(session.get("total_pages", 20))
    pricing_model = PricingEngine.calculate_pricing(total_pages)
    amount_expected = pricing_model.total_fee

    initial_txn_ref = payload.transaction_ref or f"PENDING-{payload.session_id[:10]}-{int(time.time())}"
    txn_record = {
        "session_id": payload.session_id,
        "amount_expected": amount_expected,
        "transaction_ref": initial_txn_ref,
        "status": "pending",
        "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
        "cbe_account_name": settings.CBE_ACCOUNT_NAME,
        "payer_email": payload.student_email,
        "payer_name": payload.student_name,
        "payer_phone": payload.student_phone,
        "created_at": time.time()
    }

    # Save to Supabase transactions table if table exists
    client = storage_service.supabase_client
    if client:
        try:
            client.table("transactions").upsert({
                "session_id": payload.session_id,
                "amount_expected": amount_expected,
                "transaction_ref": initial_txn_ref,
                "status": "pending",
                "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
                "cbe_account_name": settings.CBE_ACCOUNT_NAME,
                "payer_email": payload.student_email,
                "payer_name": payload.student_name,
                "payer_phone": payload.student_phone
            }, on_conflict="session_id").execute()
            safe_print(f"[CBE Payment] Registered pending txn in Supabase for session {payload.session_id}")
        except Exception as e:
            safe_print(f"[Supabase Transactions] Upsert notice: {e}")

    _local_transactions_db[initial_txn_ref.upper()] = txn_record
    _local_transactions_db[payload.session_id] = txn_record

    safe_print(f"[CBE Payment] Initiated: Session {payload.session_id} | Pages: {total_pages} | Expected: {amount_expected} ETB")

    return InitiateCBEPaymentResponse(
        status="pending",
        session_id=payload.session_id,
        amount_expected=amount_expected,
        currency="ETB",
        total_pages=total_pages,
        cbe_account_number=settings.CBE_ACCOUNT_NUMBER,
        cbe_account_name=settings.CBE_ACCOUNT_NAME,
        pricing_breakdown=pricing_model.model_dump(),
        instructions=(
            f"Please transfer exactly {amount_expected:.2f} ETB to Commercial Bank of Ethiopia (CBE) "
            f"Account: {settings.CBE_ACCOUNT_NUMBER} ({settings.CBE_ACCOUNT_NAME}). "
            f"After completing the transfer, enter the CBE Transaction ID (FT/TXN Ref) below to unlock your formatted thesis."
        )
    )

@router.post("/payment/submit-cbe-txn", response_model=SubmitCBETransactionResponse)
@router.post("/submit-cbe-transaction", response_model=SubmitCBETransactionResponse)
async def submit_cbe_transaction(payload: SubmitCBETransactionRequest):
    """
    Called by user from frontend to associate their entered CBE Transaction ID
    with the current session and trigger an immediate Gmail IMAP / webhook check.
    """
    clean_ref = payload.transaction_ref.strip().upper()
    safe_print(f"[CBE Submit Txn] User submitted Txn ID: '{clean_ref}' for Session: '{payload.session_id}' (Payer: {payload.payer_name})")

    if not clean_ref or len(clean_ref) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid CBE Transaction ID (e.g., FT2609384729)."
        )

    session = storage_service.get_session(payload.session_id)
    if not session:
        safe_print(f"[CBE Submit Txn] ❌ Session '{payload.session_id}' not found.")
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    # 1. Update session on disk with submitted transaction ID immediately
    storage_service.update_session_transaction(
        session_id=payload.session_id,
        transaction_ref=clean_ref,
        payer_name=payload.payer_name,
        payer_phone=payload.payer_phone
    )

    pricing = session.get("pricing", {})
    amount_expected = float(pricing.get("total_fee", settings.BASE_FEE_ETB))

    client = storage_service.supabase_client
    existing_status = "pending"
    download_url = None

    # 2. Check if this Txn ID was already pre-verified in Supabase
    if client:
        try:
            query = client.table("transactions").select("*").ilike("transaction_ref", clean_ref).execute()
            if query.data and len(query.data) > 0:
                rec = query.data[0]
                existing_status = rec.get("status", "pending")
                download_url = rec.get("download_url")
                safe_print(f"[CBE Submit Txn] Found record in Supabase for '{clean_ref}': Status='{existing_status}'")
            else:
                client.table("transactions").upsert({
                    "session_id": payload.session_id,
                    "amount_expected": amount_expected,
                    "transaction_ref": clean_ref,
                    "status": "pending",
                    "payer_name": payload.payer_name,
                    "payer_phone": payload.payer_phone
                }, on_conflict="session_id").execute()
        except Exception as e:
            safe_print(f"[Supabase Transactions] Submit notice: {e}")

    # Check local in-memory registry
    if clean_ref in _local_transactions_db and _local_transactions_db[clean_ref].get("status") == "approved":
        existing_status = "approved"
        download_url = _local_transactions_db[clean_ref].get("download_url")

    txn_record = {
        "session_id": payload.session_id,
        "amount_expected": amount_expected,
        "transaction_ref": clean_ref,
        "status": existing_status,
        "payer_name": payload.payer_name,
        "payer_phone": payload.payer_phone
    }
    _local_transactions_db[clean_ref] = txn_record
    _local_transactions_db[payload.session_id] = txn_record

    # 3. Trigger immediate on-demand Gmail IMAP check if configured
    if existing_status != "approved" and cbe_imap_service.is_configured():
        safe_print(f"[CBE Submit Txn] Triggering immediate on-demand Gmail IMAP scan for '{clean_ref}'...")
        try:
            await asyncio.to_thread(cbe_imap_service.check_gmail_receipts)
            refreshed_session = storage_service.get_session(payload.session_id)
            if refreshed_session and refreshed_session.get("is_paid", False):
                existing_status = "approved"
                download_url = refreshed_session.get("download_url")
            elif _local_transactions_db.get(clean_ref, {}).get("status") == "approved":
                existing_status = "approved"
                download_url = _local_transactions_db[clean_ref].get("download_url")
        except Exception as e:
            safe_print(f"[IMAP on-demand check notice] {e}")
    elif not cbe_imap_service.is_configured():
        safe_print(f"[CBE Submit Txn] Note: Gmail IMAP is not configured. Waiting for CBE Email Webhook / Make.com.")

    # 4. If approved, mark session paid and return download URL
    if existing_status == "approved" or session.get("is_paid", False):
        updated_session = storage_service.mark_session_paid(payload.session_id, clean_ref)
        safe_print(f"[CBE Submit Txn] ✅ Transaction '{clean_ref}' verified! Returning download URL.")
        return SubmitCBETransactionResponse(
            status="approved",
            session_id=payload.session_id,
            transaction_ref=clean_ref,
            amount_expected=amount_expected,
            message="Payment successfully verified! Your formatted thesis is unlocked.",
            download_url=updated_session.get("download_url"),
            file_name=updated_session.get("download_filename", "Formatted_Thesis.docx")
        )

    safe_print(f"[CBE Submit Txn] Transaction '{clean_ref}' registered with status 'pending'. Awaiting IMAP / Webhook receipt...")
    return SubmitCBETransactionResponse(
        status="pending",
        session_id=payload.session_id,
        transaction_ref=clean_ref,
        amount_expected=amount_expected,
        message="Transaction ID registered. Checking Gmail IMAP receipts and awaiting confirmation..."
    )

@router.post("/payment/cbe-email-webhook", response_model=CBEWebhookResponse)
@router.post("/cbe-email-webhook", response_model=CBEWebhookResponse)
async def cbe_email_webhook(
    payload: CBEWebhookPayload,
    authorization: Optional[str] = Header(None)
):
    """
    Automated CBE Email Webhook Endpoint for Make.com / Mailhooks / Zapier / Google Apps Script:
    1. Receives incoming CBE email JSON payload.
    2. Extracts Transaction ID, Amount, Payer Name, Account Number, and Date/Time via Regex.
    3. Matches with 'pending' session in Supabase / disk metadata / memory.
    4. Validates amount_paid >= amount_expected.
    5. Updates status to 'approved' and generates 24-hour Supabase Signed Download URL.
    """
    raw_content = payload.body or payload.html or payload.text or payload.raw_content or payload.message or ""
    safe_print(f"[CBE Webhook] Received webhook call! Subject='{payload.subject}', Payload Size={len(raw_content)} chars")

    parsed_meta = cbe_email_parser.parse_full_cbe_payload(
        raw_text=raw_content,
        subject=payload.subject
    )

    final_txn_ref = (payload.transaction_id or parsed_meta.get("transaction_ref") or "").strip().upper()
    final_amount = payload.amount if payload.amount is not None else parsed_meta.get("amount")
    payer_name = parsed_meta.get("payer_name")

    safe_print(f"[CBE Webhook] Parsed metadata -> Txn ID: '{final_txn_ref}', Amount: {final_amount} ETB, Payer: '{payer_name}'")

    if not final_txn_ref:
        safe_print(f"[CBE Webhook] ❌ Failed to detect Transaction Reference in payload. Raw snippet: {raw_content[:200]}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not detect a valid CBE Transaction Reference / FT Number in email payload."
        )

    if final_amount is None or final_amount <= 0:
        safe_print(f"[CBE Webhook] ❌ Detected Txn '{final_txn_ref}' but could not extract a valid amount.")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Detected Transaction Ref '{final_txn_ref}' but could not extract a valid payment amount."
        )

    client = storage_service.supabase_client
    matched_session_id: Optional[str] = None
    expected_amount: float = 50.0

    # 1. Query Supabase
    if client:
        try:
            query = client.table("transactions").select("*").ilike("transaction_ref", f"%{final_txn_ref}%").execute()
            if query.data and len(query.data) > 0:
                matched_row = query.data[0]
                matched_session_id = matched_row.get("session_id")
                expected_amount = float(matched_row.get("amount_expected", 50.0))
                safe_print(f"[CBE Webhook] Matched via Supabase transactions -> Session: {matched_session_id}")
        except Exception as e:
            safe_print(f"[CBE Webhook Supabase Query] Notice: {e}")

    # 2. Check Disk & Memory Sessions
    if not matched_session_id:
        clean_ref = re.sub(r'[^A-Z0-9]', '', final_txn_ref)
        matched_sid = storage_service.find_session_by_txn_ref(clean_ref)
        if matched_sid:
            matched_session_id = matched_sid
            sess = storage_service.get_session(matched_sid)
            pricing = sess.get("pricing", {}) if sess else {}
            expected_amount = float(pricing.get("total_fee", 50.0))
            safe_print(f"[CBE Webhook] Matched via Disk/Memory Session find_session_by_txn_ref -> Session: {matched_session_id}")

    # 3. Check single unpaid session amount match fallback
    if not matched_session_id:
        all_sessions = storage_service.get_all_sessions()
        unpaid_matching = []
        for sid, sdata in all_sessions.items():
            if not sdata.get("is_paid", False):
                pricing = sdata.get("pricing", {})
                req_fee = float(pricing.get("total_fee", 50.0))
                if abs(req_fee - final_amount) < 0.01:
                    unpaid_matching.append((sid, req_fee))

        if len(unpaid_matching) == 1:
            matched_session_id = unpaid_matching[0][0]
            expected_amount = unpaid_matching[0][1]
            safe_print(f"[CBE Webhook] Matched via single pending pricing amount match -> Session: {matched_session_id}")

    if not matched_session_id:
        safe_print(f"[CBE Webhook] Txn '{final_txn_ref}' ({final_amount} ETB) recorded as pre-verified. Waiting for user session link.")
        if client:
            try:
                client.table("transactions").upsert({
                    "session_id": "pre_verified",
                    "amount_expected": final_amount,
                    "amount_paid": final_amount,
                    "transaction_ref": final_txn_ref,
                    "status": "approved",
                    "payer_name": payer_name,
                    "raw_webhook_payload": payload.model_dump(by_alias=True)
                }, on_conflict="transaction_ref").execute()
            except Exception as e:
                safe_print(f"[Supabase] Unmatched record notice: {e}")

        return CBEWebhookResponse(
            status="unmatched_recorded",
            message=f"Transaction {final_txn_ref} with amount {final_amount} ETB recorded, waiting for user session link.",
            transaction_ref=final_txn_ref,
            amount_detected=final_amount
        )

    if final_amount < expected_amount:
        safe_print(f"[CBE Webhook] ❌ Underpayment for session {matched_session_id}: Expected {expected_amount} ETB, got {final_amount} ETB")
        if client:
            try:
                client.table("transactions").update({
                    "amount_paid": final_amount,
                    "status": "failed",
                    "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
                }).eq("transaction_ref", final_txn_ref).execute()
            except Exception:
                pass

        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Underpayment detected. Required: {expected_amount} ETB, Received: {final_amount} ETB."
        )

    updated_session = storage_service.mark_session_paid(matched_session_id, final_txn_ref)
    download_url = updated_session.get("download_url")

    if client:
        try:
            client.table("transactions").update({
                "amount_paid": final_amount,
                "status": "approved",
                "download_url": download_url,
                "payer_name": payer_name,
                "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                "raw_webhook_payload": payload.model_dump(by_alias=True)
            }).eq("session_id", matched_session_id).execute()
        except Exception as e:
            safe_print(f"[Supabase Webhook Update] Notice: {e}")

    _local_transactions_db[final_txn_ref] = {
        "session_id": matched_session_id,
        "amount_expected": expected_amount,
        "amount_paid": final_amount,
        "transaction_ref": final_txn_ref,
        "status": "approved",
        "download_url": download_url,
        "payer_name": payer_name
    }
    _local_transactions_db[matched_session_id] = _local_transactions_db[final_txn_ref]

    safe_print(f"[CBE Webhook] ✅ SUCCESS! Session {matched_session_id} unlocked with Txn {final_txn_ref} (Download: {download_url})")

    return CBEWebhookResponse(
        status="success",
        message="CBE Payment confirmed and verified successfully! Formatted thesis unlocked.",
        transaction_ref=final_txn_ref,
        amount_detected=final_amount,
        matched_session_id=matched_session_id,
        download_url=download_url
    )

@router.get("/payment/status/{session_id}", response_model=CheckTransactionStatusResponse)
@router.get("/cbe-transaction-status/{session_id}", response_model=CheckTransactionStatusResponse)
async def check_transaction_status(session_id: str):
    """
    Polling Endpoint for Frontend:
    Checks if payment for this session_id has been approved by the CBE IMAP poller / Webhook.
    """
    if not SAFE_ID_REGEX.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session identifier.")

    session = storage_service.get_session(session_id)
    pricing = session.get("pricing", {}) if session else {}
    amount_expected = float(pricing.get("total_fee", settings.BASE_FEE_ETB))

    # 1. Check if session itself is marked paid
    if session and session.get("is_paid", False):
        return CheckTransactionStatusResponse(
            status="approved",
            session_id=session_id,
            transaction_ref=session.get("tx_ref") or session.get("transaction_ref"),
            amount_expected=amount_expected,
            amount_paid=amount_expected,
            verified=True,
            download_url=session.get("download_url"),
            file_name=session.get("download_filename", "Formatted_Thesis.docx"),
            message="Payment verified! Formatted thesis ready for download."
        )

    # 2. Check local in-memory transactions db
    if session_id in _local_transactions_db:
        rec = _local_transactions_db[session_id]
        if rec.get("status") == "approved":
            # Sync to storage session
            updated = storage_service.mark_session_paid(session_id, rec.get("transaction_ref", "APPROVED"))
            return CheckTransactionStatusResponse(
                status="approved",
                session_id=session_id,
                transaction_ref=rec.get("transaction_ref"),
                amount_expected=float(rec.get("amount_expected", amount_expected)),
                amount_paid=float(rec.get("amount_paid", amount_expected)),
                verified=True,
                download_url=updated.get("download_url") or rec.get("download_url"),
                file_name=updated.get("download_filename", "Formatted_Thesis.docx"),
                message="Payment verified! Formatted thesis ready for download."
            )

    # 3. Check Supabase transactions table
    client = storage_service.supabase_client
    if client:
        try:
            res = client.table("transactions").select("*").eq("session_id", session_id).execute()
            if res.data and len(res.data) > 0:
                rec = res.data[0]
                status_val = rec.get("status", "pending")
                if status_val == "approved":
                    updated = storage_service.mark_session_paid(session_id, rec.get("transaction_ref", "APPROVED"))
                    return CheckTransactionStatusResponse(
                        status="approved",
                        session_id=session_id,
                        transaction_ref=rec.get("transaction_ref"),
                        amount_expected=float(rec.get("amount_expected", amount_expected)),
                        amount_paid=float(rec.get("amount_paid", amount_expected)),
                        verified=True,
                        download_url=updated.get("download_url") or rec.get("download_url"),
                        file_name=updated.get("download_filename", "Formatted_Thesis.docx"),
                        message="Payment verified! Formatted thesis ready for download."
                    )
        except Exception as e:
            safe_print(f"[Supabase Status Check Notice] {e}")

    # 4. If session has a transaction_ref, check if that transaction_ref is approved anywhere
    if session and (session.get("transaction_ref") or session.get("tx_ref")):
        submitted_ref = session.get("transaction_ref") or session.get("tx_ref")
        clean_submitted = re.sub(r'[^A-Z0-9]', '', submitted_ref.upper())
        if clean_submitted in _local_transactions_db and _local_transactions_db[clean_submitted].get("status") == "approved":
            updated = storage_service.mark_session_paid(session_id, submitted_ref)
            return CheckTransactionStatusResponse(
                status="approved",
                session_id=session_id,
                transaction_ref=submitted_ref,
                amount_expected=amount_expected,
                amount_paid=amount_expected,
                verified=True,
                download_url=updated.get("download_url"),
                file_name=updated.get("download_filename", "Formatted_Thesis.docx"),
                message="Payment verified! Formatted thesis ready for download."
            )
        if client:
            try:
                res = client.table("transactions").select("*").ilike("transaction_ref", f"%{submitted_ref}%").execute()
                if res.data and len(res.data) > 0:
                    rec = res.data[0]
                    if rec.get("status") == "approved":
                        updated = storage_service.mark_session_paid(session_id, submitted_ref)
                        return CheckTransactionStatusResponse(
                            status="approved",
                            session_id=session_id,
                            transaction_ref=submitted_ref,
                            amount_expected=amount_expected,
                            amount_paid=amount_expected,
                            verified=True,
                            download_url=updated.get("download_url") or rec.get("download_url"),
                            file_name=updated.get("download_filename", "Formatted_Thesis.docx"),
                            message="Payment verified! Formatted thesis ready for download."
                        )
            except Exception:
                pass

    return CheckTransactionStatusResponse(
        status="pending",
        session_id=session_id,
        amount_expected=amount_expected,
        verified=False,
        message="Awaiting CBE transfer verification..."
    )

@router.get("/download/{session_id}")
async def download_formatted_thesis(session_id: str):
    """
    Direct Secure Download Endpoint (Internal Fallback):
    Guarantees download if Supabase Storage is offline or experiencing network latency.
    """
    if not SAFE_ID_REGEX.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session ID.")

    session = storage_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Thesis session not found or expired.")

    if not session.get("is_paid", False):
        # Check local and database approvals
        is_approved = False
        if session_id in _local_transactions_db and _local_transactions_db[session_id].get("status") == "approved":
            is_approved = True

        client = storage_service.supabase_client
        if not is_approved and client:
            try:
                res = client.table("transactions").select("status").eq("session_id", session_id).execute()
                if res.data and res.data[0].get("status") == "approved":
                    is_approved = True
            except Exception:
                pass

        if not is_approved:
            raise HTTPException(
                status_code=403,
                detail="Payment required to download full formatted thesis."
            )

    docx_path = session.get("formatted_docx_path")
    if not docx_path or not Path(docx_path).exists():
        session_dir = storage_service.get_session_dir(session_id)
        candidate = session_dir / "formatted_thesis.docx"
        if candidate.exists():
            docx_path = str(candidate)
        else:
            raise HTTPException(status_code=404, detail="Formatted document file not found on disk.")

    original_filename = session.get("original_filename", "Formatted_Thesis.docx")
    if not original_filename.startswith("Formatted_"):
        original_filename = f"Formatted_{original_filename}"

    return FileResponse(
        path=docx_path,
        filename=original_filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
