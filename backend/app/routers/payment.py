import time
import re
import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from fastapi import APIRouter, HTTPException, status, Header, Request
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
from app.config import settings

router = APIRouter(prefix="/api", tags=["cbe_payment"])

# Safe regex validator
SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")

# In-memory transaction registry fallback
_local_transactions_db: Dict[str, Dict[str, Any]] = {}

@router.post("/initiate-cbe-payment", response_model=InitiateCBEPaymentResponse)
async def initiate_cbe_payment(payload: InitiateCBEPaymentRequest):
    """
    Accepts session_id, calculates the exact total_fee dynamically based on
    total formatted pages using the ETHIOFORMAT_RULES.md pricing formula
    (50 ETB base up to 20 pages + 1.50 ETB / extra page),
    creates a 'pending' record in Supabase / local registry,
    and returns the CBE account details + expected amount to the frontend.
    """
    if not SAFE_ID_REGEX.match(payload.session_id):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid session ID format."
        )

    session = storage_service.get_session(payload.session_id)
    if not session:
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
        "amount_paid": None,
        "transaction_ref": initial_txn_ref,
        "status": "pending",
        "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
        "cbe_account_name": settings.CBE_ACCOUNT_NAME,
        "payer_email": payload.student_email,
        "payer_name": payload.student_name,
        "payer_phone": payload.student_phone,
        "created_at": datetime.datetime.now(datetime.timezone.utc).isoformat()
    }

    # Store in Supabase 'transactions' table if available
    client = storage_service.supabase_client
    if client:
        try:
            client.table("transactions").insert({
                "session_id": payload.session_id,
                "amount_expected": amount_expected,
                "transaction_ref": initial_txn_ref,
                "status": "pending",
                "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
                "cbe_account_name": settings.CBE_ACCOUNT_NAME,
                "payer_email": payload.student_email,
                "payer_name": payload.student_name,
                "payer_phone": payload.student_phone
            }).execute()
        except Exception as e:
            print(f"[Supabase Transactions] Insert notice: {e}")

    _local_transactions_db[initial_txn_ref.upper()] = txn_record
    _local_transactions_db[payload.session_id] = txn_record

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
async def submit_cbe_transaction(payload: SubmitCBETransactionRequest):
    """
    Called by user from frontend to associate their entered CBE Transaction ID
    with the current session and check if it has already been approved by Webhook.
    """
    clean_ref = payload.transaction_ref.strip().upper()
    if not clean_ref or len(clean_ref) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Please provide a valid CBE Transaction ID (e.g., FT2609384729)."
        )

    session = storage_service.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    pricing = session.get("pricing", {})
    amount_expected = float(pricing.get("total_fee", settings.BASE_FEE_ETB))

    client = storage_service.supabase_client
    existing_status = "pending"
    download_url = None

    if client:
        try:
            query = client.table("transactions").select("*").eq("transaction_ref", clean_ref).execute()
            if query.data and len(query.data) > 0:
                rec = query.data[0]
                existing_status = rec.get("status", "pending")
                download_url = rec.get("download_url")
            else:
                client.table("transactions").insert({
                    "session_id": payload.session_id,
                    "amount_expected": amount_expected,
                    "transaction_ref": clean_ref,
                    "status": "pending",
                    "payer_name": payload.payer_name,
                    "payer_phone": payload.payer_phone
                }).execute()
        except Exception as e:
            print(f"[Supabase Transactions] Submit notice: {e}")

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

    if existing_status == "approved" or session.get("is_paid", False):
        updated_session = storage_service.mark_session_paid(payload.session_id, clean_ref)
        return SubmitCBETransactionResponse(
            status="approved",
            session_id=payload.session_id,
            transaction_ref=clean_ref,
            amount_expected=amount_expected,
            message="Payment successfully verified! Your formatted thesis is unlocked.",
            download_url=updated_session.get("download_url"),
            file_name=updated_session.get("download_filename", "Formatted_Thesis.docx")
        )

    return SubmitCBETransactionResponse(
        status="pending",
        session_id=payload.session_id,
        transaction_ref=clean_ref,
        amount_expected=amount_expected,
        message="Transaction ID registered. Waiting for CBE payment confirmation webhook..."
    )

@router.post("/payment/cbe-email-webhook", response_model=CBEWebhookResponse)
async def cbe_email_webhook(
    payload: CBEWebhookPayload,
    authorization: Optional[str] = Header(None)
):
    """
    Automated CBE Email Webhook Endpoint for Make.com / Mailhooks:
    1. Receives incoming CBE email JSON payload from Make.com Custom Mailhook / Gmail Forwarder.
    2. Extracts Transaction ID, Amount, Payer Name, Account Number, and Date/Time via Regex.
    3. Matches with 'pending' session in Supabase / database.
    4. Validates amount_paid >= amount_expected.
    5. Updates status to 'approved' and generates 24-hour Supabase Signed Download URL.
    """
    print("=" * 60)
    print(f"[Make.com Webhook] Incoming CBE Email Notification at {datetime.datetime.now(datetime.timezone.utc)}")
    print(f"[Make.com Webhook] Subject: {payload.subject}")
    print(f"[Make.com Webhook] Sender: {payload.from_email}")

    # Extract all fields
    raw_content = payload.body or payload.html or payload.text or payload.raw_content or ""
    parsed_meta = cbe_email_parser.parse_full_cbe_payload(
        raw_text=raw_content,
        subject=payload.subject
    )

    # Use extracted or passed values
    final_txn_ref = (payload.transaction_id or parsed_meta.get("transaction_ref") or "").strip().upper()
    final_amount = payload.amount if payload.amount is not None else parsed_meta.get("amount")
    payer_name = parsed_meta.get("payer_name")
    account_number = parsed_meta.get("account_number")
    date_time = parsed_meta.get("date_time")

    print(f"[Make.com Webhook] Parsed Results ->")
    print(f"  • Transaction Ref: {final_txn_ref}")
    print(f"  • Amount:          {final_amount} ETB")
    print(f"  • Payer Name:      {payer_name}")
    print(f"  • Account Number:  {account_number}")
    print(f"  • Date & Time:     {date_time}")
    print("=" * 60)

    if not final_txn_ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Could not detect a valid CBE Transaction Reference / FT Number in email payload."
        )

    if final_amount is None or final_amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Detected Transaction Ref '{final_txn_ref}' but could not extract a valid payment amount."
        )

    # Look up matching transaction in Supabase
    client = storage_service.supabase_client
    matched_session_id: Optional[str] = None
    expected_amount: float = 50.0

    if client:
        try:
            query = client.table("transactions").select("*").ilike("transaction_ref", final_txn_ref).execute()
            if query.data and len(query.data) > 0:
                matched_row = query.data[0]
                matched_session_id = matched_row.get("session_id")
                expected_amount = float(matched_row.get("amount_expected", 50.0))
        except Exception as e:
            print(f"[Supabase Webhook Query] Notice: {e}")

    # Fallback to local registry
    if not matched_session_id and final_txn_ref in _local_transactions_db:
        local_rec = _local_transactions_db[final_txn_ref]
        matched_session_id = local_rec.get("session_id")
        expected_amount = float(local_rec.get("amount_expected", 50.0))

    # Match by pending active session if not already registered by ref
    if not matched_session_id:
        for sid, sdata in storage_service._sessions.items():
            if not sdata.get("is_paid", False):
                pricing = sdata.get("pricing", {})
                req_fee = float(pricing.get("total_fee", 50.0))
                if abs(req_fee - final_amount) < 0.01:
                    matched_session_id = sid
                    expected_amount = req_fee
                    break

    if not matched_session_id:
        # Record unmatched transaction in Supabase for audit
        if client:
            try:
                client.table("transactions").insert({
                    "session_id": "unmatched_session",
                    "amount_expected": final_amount,
                    "amount_paid": final_amount,
                    "transaction_ref": final_txn_ref,
                    "status": "approved",
                    "payer_name": payer_name,
                    "raw_webhook_payload": payload.model_dump(by_alias=True)
                }).execute()
            except Exception as e:
                print(f"[Supabase] Unmatched record notice: {e}")

        return CBEWebhookResponse(
            status="unmatched_recorded",
            message=f"Transaction {final_txn_ref} with amount {final_amount} ETB recorded, waiting for user session link.",
            transaction_ref=final_txn_ref,
            amount_detected=final_amount
        )

    # Validate amount
    if final_amount < expected_amount:
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

    # Success: Mark session paid & generate 24h Supabase Signed URL
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
            print(f"[Supabase Webhook Update] Notice: {e}")

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

    print(f"[Make.com Webhook] Transaction {final_txn_ref} APPROVED for Session {matched_session_id}!")
    print(f"[Make.com Webhook] Generated Signed Download URL: {download_url}")

    return CBEWebhookResponse(
        status="success",
        message="CBE Payment confirmed and verified successfully! Formatted thesis unlocked.",
        transaction_ref=final_txn_ref,
        amount_detected=final_amount,
        matched_session_id=matched_session_id,
        download_url=download_url
    )

@router.get("/payment/status/{session_id}", response_model=CheckTransactionStatusResponse)
async def check_transaction_status(session_id: str):
    """
    Polling Endpoint for Frontend:
    Checks if payment for this session_id has been approved by the CBE Webhook.
    """
    if not SAFE_ID_REGEX.match(session_id):
        raise HTTPException(status_code=400, detail="Invalid session identifier.")

    session = storage_service.get_session(session_id)
    pricing = session.get("pricing", {}) if session else {}
    amount_expected = float(pricing.get("total_fee", settings.BASE_FEE_ETB))

    if session and session.get("is_paid", False):
        return CheckTransactionStatusResponse(
            status="approved",
            session_id=session_id,
            transaction_ref=session.get("tx_ref"),
            amount_expected=amount_expected,
            amount_paid=amount_expected,
            verified=True,
            download_url=session.get("download_url"),
            file_name=session.get("download_filename", "Formatted_Thesis.docx"),
            message="Payment approved! Your thesis is ready for download."
        )

    client = storage_service.supabase_client
    if client:
        try:
            query = client.table("transactions").select("*").eq("session_id", session_id).order("created_at", desc=True).limit(1).execute()
            if query.data and len(query.data) > 0:
                row = query.data[0]
                status_val = row.get("status", "pending")
                if status_val == "approved":
                    tx_ref = row.get("transaction_ref", "CBE-VERIFIED")
                    upd = storage_service.mark_session_paid(session_id, tx_ref)
                    return CheckTransactionStatusResponse(
                        status="approved",
                        session_id=session_id,
                        transaction_ref=tx_ref,
                        amount_expected=float(row.get("amount_expected", amount_expected)),
                        amount_paid=float(row.get("amount_paid", amount_expected)),
                        verified=True,
                        download_url=upd.get("download_url"),
                        file_name=upd.get("download_filename", "Formatted_Thesis.docx"),
                        message="Payment confirmed via CBE Webhook!"
                    )
                elif status_val == "failed":
                    return CheckTransactionStatusResponse(
                        status="failed",
                        session_id=session_id,
                        transaction_ref=row.get("transaction_ref"),
                        amount_expected=amount_expected,
                        verified=False,
                        message="Payment verification failed or insufficient amount transferred."
                    )
        except Exception as e:
            print(f"[Supabase Status Polling] Notice: {e}")

    if session_id in _local_transactions_db:
        loc = _local_transactions_db[session_id]
        if loc.get("status") == "approved":
            return CheckTransactionStatusResponse(
                status="approved",
                session_id=session_id,
                transaction_ref=loc.get("transaction_ref"),
                amount_expected=amount_expected,
                amount_paid=loc.get("amount_paid"),
                verified=True,
                download_url=loc.get("download_url"),
                file_name="Formatted_Thesis.docx",
                message="Payment approved!"
            )

    return CheckTransactionStatusResponse(
        status="pending",
        session_id=session_id,
        amount_expected=amount_expected,
        verified=False,
        message="Waiting for payment confirmation from CBE..."
    )

@router.get("/download/{session_id}")
async def download_formatted_file(session_id: str):
    """
    Secure file delivery endpoint for paid sessions.
    Strictly forbids access if session is unpaid.
    Guards against path traversal by validating session_id and resolving canonical paths.
    """
    if not SAFE_ID_REGEX.match(session_id):
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid session identifier.")

    session = storage_service.get_session(session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found or expired.")

    if not session.get("is_paid", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied. CBE payment must be verified before downloading the complete formatted document."
        )

    file_path_str = session.get("formatted_docx_path")
    if not file_path_str:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formatted file not registered.")

    file_path = Path(file_path_str).resolve()
    staging_base = Path(settings.STORAGE_STAGING_DIR).resolve()

    if not str(file_path).startswith(str(staging_base)) or not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formatted file not found on server.")

    original_name = session.get("original_filename", "Thesis.docx")
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', original_name)
    download_filename = f"Formatted_{safe_filename}" if not safe_filename.startswith("Formatted_") else safe_filename

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=download_filename,
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'}
    )
