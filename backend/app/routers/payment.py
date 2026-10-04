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
_last_imap_check_time: Dict[str, float] = {}

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
        safe_print(f"[CBE Payment] Reconstructing session metadata for '{payload.session_id}'...")
        session = {
            "session_id": payload.session_id,
            "original_filename": "Formatted_Thesis.docx",
            "total_pages": 20,
            "pricing": {"base_fee": 50.0, "incremental_fee": 0.0, "total_fee": 50.0, "currency": "ETB"},
            "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
            "cbe_account_name": settings.CBE_ACCOUNT_NAME,
            "is_paid": False
        }
        storage_service.register_session(payload.session_id, session)

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
        safe_print(f"[CBE Submit Txn] Reconstructing session metadata for '{payload.session_id}'...")
        session = {
            "session_id": payload.session_id,
            "original_filename": "Formatted_Thesis.docx",
            "total_pages": 20,
            "pricing": {"base_fee": 50.0, "incremental_fee": 0.0, "total_fee": 50.0, "currency": "ETB"},
            "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
            "cbe_account_name": settings.CBE_ACCOUNT_NAME,
            "is_paid": False
        }
        storage_service.register_session(payload.session_id, session)

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

    # 2. Check if pre-verified in Storage Service
    preverified = storage_service.get_preverified_transaction(clean_ref)
    if preverified:
        safe_print(f"[CBE Submit Txn] Instant match! Txn '{clean_ref}' was pre-verified in storage: {preverified}")
        existing_status = "approved"

    # 3. Check if this Txn ID was already pre-verified in Supabase
    if client and existing_status != "approved":
        try:
            query = client.table("transactions").select("*").ilike("transaction_ref", f"%{clean_ref}%").execute()
            if query.data and len(query.data) > 0:
                rec = query.data[0]
                rec_status = rec.get("status", "pending")
                if rec_status == "approved":
                    existing_status = "approved"
                    download_url = rec.get("download_url")
                    safe_print(f"[CBE Submit Txn] Found approved record in Supabase for '{clean_ref}'")
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

    # 4. Trigger immediate targeted on-demand Gmail IMAP check if configured
    if existing_status != "approved" and cbe_imap_service.is_configured():
        safe_print(f"[CBE Submit Txn] Triggering immediate targeted Gmail IMAP scan for '{clean_ref}'...")
        try:
            await asyncio.to_thread(cbe_imap_service.check_gmail_receipts, clean_ref)
            refreshed_session = storage_service.get_session(payload.session_id)
            if refreshed_session and refreshed_session.get("is_paid", False):
                existing_status = "approved"
                download_url = refreshed_session.get("download_url")
            elif _local_transactions_db.get(clean_ref, {}).get("status") == "approved":
                existing_status = "approved"
                download_url = _local_transactions_db[clean_ref].get("download_url")
            elif storage_service.get_preverified_transaction(clean_ref):
                existing_status = "approved"
        except Exception as e:
            safe_print(f"[IMAP on-demand check notice] {e}")

    # 5. If approved, mark session paid and return download URL
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

    txn_record = {
        "session_id": payload.session_id,
        "amount_expected": amount_expected,
        "transaction_ref": clean_ref,
        "status": "pending",
        "payer_name": payload.payer_name,
        "payer_phone": payload.payer_phone
    }
    _local_transactions_db[clean_ref] = txn_record
    _local_transactions_db[payload.session_id] = txn_record

    safe_print(f"[CBE Submit Txn] Transaction '{clean_ref}' registered with status 'pending'. Awaiting IMAP / Webhook receipt...")
    return SubmitCBETransactionResponse(
        status="pending",
        session_id=payload.session_id,
        transaction_ref=clean_ref,
        amount_expected=amount_expected,
        message="Transaction ID registered. Checking CBE receipts and awaiting confirmation..."
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

    extracted_txn = parsed_meta.get("transaction_ref") or payload.transaction_id
    extracted_amount = parsed_meta.get("amount") or payload.amount
    payer_name = parsed_meta.get("payer_name") or payload.sender or payload.from_

    safe_print(f"[CBE Webhook] Parsed: Txn='{extracted_txn}', Amount={extracted_amount} ETB, Payer='{payer_name}'")

    if not extracted_txn and not extracted_amount:
        safe_print("[CBE Webhook] ⚠️ Could not extract Transaction ID or Amount from webhook payload.")
        return CBEWebhookResponse(
            status="ignored",
            message="No CBE transaction reference or amount detected in payload.",
            transaction_ref=None,
            amount_detected=None
        )

    all_extracted_refs = parsed_meta.get("all_transaction_refs", [])
    if extracted_txn and extracted_txn not in all_extracted_refs:
        all_extracted_refs.append(extracted_txn)

    final_txn_ref = extracted_txn.strip().upper() if extracted_txn else f"TXN-UNKWN-{int(time.time())}"
    final_amount = float(extracted_amount) if extracted_amount else 50.0

    # Store all references in preverified cache
    for ref_cand in all_extracted_refs:
        storage_service.register_preverified_transaction(
            txn_ref=ref_cand.strip().upper(),
            data={
                "transaction_ref": ref_cand.strip().upper(),
                "amount": final_amount,
                "payer_name": payer_name,
                "source": "webhook",
                "subject": payload.subject,
                "body": raw_content[:400]
            }
        )

    client = storage_service.supabase_client
    matched_session_id: Optional[str] = None
    expected_amount: float = 50.0

    # Step 1: Query Supabase transactions table by transaction_ref
    if client:
        try:
            for ref_cand in all_extracted_refs:
                res = client.table("transactions").select("*").ilike("transaction_ref", f"%{ref_cand.strip().upper()}%").execute()
                if res.data and len(res.data) > 0:
                    matched_row = res.data[0]
                    matched_session_id = matched_row.get("session_id")
                    expected_amount = float(matched_row.get("amount_expected", 50.0))
                    final_txn_ref = ref_cand.strip().upper()
                    safe_print(f"[CBE Webhook] Matched session in Supabase with ref '{final_txn_ref}': {matched_session_id}")
                    break
        except Exception as e:
            safe_print(f"[Supabase Webhook Search] Notice: {e}")

    # Step 2: Check Local Disk & Memory Sessions
    if not matched_session_id:
        matched_sid = storage_service.find_session_by_txn_ref(final_txn_ref)
        if matched_sid:
            matched_session_id = matched_sid
            sess = storage_service.get_session(matched_sid)
            pricing = sess.get("pricing", {}) if sess else {}
            expected_amount = float(pricing.get("total_fee", 50.0))
            safe_print(f"[CBE Webhook] Matched session via disk/memory find_session_by_txn_ref: {matched_session_id}")

    # Step 3: Check in-memory transactions db
    if not matched_session_id:
        for sid, rec in _local_transactions_db.items():
            cand = rec.get("transaction_ref", "")
            if cand and (final_txn_ref in cand.upper() or cand.upper() in final_txn_ref):
                matched_session_id = rec.get("session_id")
                expected_amount = float(rec.get("amount_expected", 50.0))
                safe_print(f"[CBE Webhook] Matched session via _local_transactions_db: {matched_session_id}")
                break

    # Step 4: Fallback - Match single active unpaid session by amount
    if not matched_session_id:
        all_sessions = storage_service.get_all_sessions()
        unpaid = []
        for sid, sdata in all_sessions.items():
            if not sdata.get("is_paid", False):
                pricing = sdata.get("pricing", {})
                req_fee = float(pricing.get("total_fee", 50.0))
                if abs(req_fee - final_amount) < 0.01:
                    unpaid.append((sid, req_fee))

        if len(unpaid) == 1:
            matched_session_id = unpaid[0][0]
            expected_amount = unpaid[0][1]
            safe_print(f"[CBE Webhook] Matched single pending session by price ({final_amount} ETB): {matched_session_id}")

    if not matched_session_id:
        safe_print(f"[CBE Webhook] Txn {final_txn_ref} ({final_amount} ETB) registered as pre-verified.")
        return CBEWebhookResponse(
            status="success",
            message=f"CBE payment {final_txn_ref} pre-verified in registry.",
            transaction_ref=final_txn_ref,
            amount_detected=final_amount,
            matched_session_id=None,
            download_url=None
        )

    # Validate payment amount
    if final_amount < expected_amount:
        safe_print(f"[CBE Webhook] ❌ Underpayment: Expected {expected_amount} ETB, got {final_amount} ETB")
        return CBEWebhookResponse(
            status="failed",
            message=f"Underpayment detected. Expected {expected_amount:.2f} ETB, but received {final_amount:.2f} ETB.",
            transaction_ref=final_txn_ref,
            amount_detected=final_amount,
            matched_session_id=matched_session_id
        )

    # Unlock document and generate signed download URL
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
    Actively triggers on-demand targeted IMAP check if pending.
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

    submitted_ref = (session.get("transaction_ref") or session.get("tx_ref") or "") if session else ""

    # 2. Check preverified storage
    if submitted_ref:
        pre = storage_service.get_preverified_transaction(submitted_ref)
        if pre:
            updated = storage_service.mark_session_paid(session_id, submitted_ref)
            return CheckTransactionStatusResponse(
                status="approved",
                session_id=session_id,
                transaction_ref=submitted_ref,
                amount_expected=amount_expected,
                amount_paid=float(pre.get("amount", amount_expected)),
                verified=True,
                download_url=updated.get("download_url"),
                file_name=updated.get("download_filename", "Formatted_Thesis.docx"),
                message="Payment verified! Formatted thesis ready for download."
            )

    # 3. Check local in-memory transactions db
    if session_id in _local_transactions_db:
        rec = _local_transactions_db[session_id]
        if rec.get("status") == "approved":
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

    # 4. Check Supabase transactions table
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

    # 5. On-demand IMAP scan during polling (cooldown: 4 seconds)
    if submitted_ref and cbe_imap_service.is_configured():
        now = time.time()
        last_check = _last_imap_check_time.get(session_id, 0)
        if now - last_check >= 4.0:
            _last_imap_check_time[session_id] = now
            try:
                await asyncio.to_thread(cbe_imap_service.check_gmail_receipts, submitted_ref)
                refreshed = storage_service.get_session(session_id)
                if refreshed and refreshed.get("is_paid", False):
                    return CheckTransactionStatusResponse(
                        status="approved",
                        session_id=session_id,
                        transaction_ref=submitted_ref,
                        amount_expected=amount_expected,
                        amount_paid=amount_expected,
                        verified=True,
                        download_url=refreshed.get("download_url"),
                        file_name=refreshed.get("download_filename", "Formatted_Thesis.docx"),
                        message="Payment verified! Formatted thesis ready for download."
                    )
            except Exception as e:
                safe_print(f"[Polling IMAP check notice] {e}")

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
        is_approved = False
        if session_id in _local_transactions_db and _local_transactions_db[session_id].get("status") == "approved":
            is_approved = True
        elif session.get("transaction_ref") and storage_service.get_preverified_transaction(session.get("transaction_ref")):
            is_approved = True

        if not is_approved:
            raise HTTPException(
                status_code=403,
                detail="Payment required to download full formatted thesis."
            )

    docx_path = session.get("formatted_docx_path")
    target_path = Path(docx_path) if docx_path else (storage_service.get_session_dir(session_id) / "formatted_thesis.docx")

    if not target_path.exists() and storage_service.supabase_client:
        try:
            bucket = settings.SUPABASE_BUCKET_NAME
            filename_try = session.get("download_filename") or session.get("original_filename", "Formatted_Thesis.docx")
            if not filename_try.startswith("Formatted_"):
                filename_try = f"Formatted_{filename_try}"
            cloud_bytes = storage_service.supabase_client.storage.from_(bucket).download(f"theses/{session_id}/{filename_try}")
            if cloud_bytes:
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with open(target_path, "wb") as f_out:
                    f_out.write(cloud_bytes)
        except Exception as e:
            safe_print(f"[Supabase Download Fallback] Notice: {e}")

    if not target_path.exists():
        fallback_p = storage_service.get_session_dir(session_id) / "formatted_thesis.docx"
        if fallback_p.exists():
            target_path = fallback_p
        else:
            raise HTTPException(status_code=404, detail="Formatted file missing. Please regenerate.")

    filename = session.get("download_filename") or session.get("original_filename", "Formatted_Thesis.docx")
    if not filename.endswith(".docx"):
        filename = f"{filename}.docx"

    return FileResponse(
        path=str(target_path),
        filename=filename,
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document"
    )
