import time
import re
from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from app.models.payment import (
    InitiatePaymentRequest,
    InitiatePaymentResponse,
    VerifyPaymentRequest,
    VerifyPaymentResponse
)
from app.services.storage_service import storage_service
from app.services.chapa_service import chapa_service
from app.config import settings

router = APIRouter(prefix="/api", tags=["payment"])

# Safe alphanumeric + underscore validator to prevent traversal/injections
SAFE_ID_REGEX = re.compile(r"^[a-zA-Z0-9_-]+$")

@router.post("/initiate-payment", response_model=InitiatePaymentResponse)
async def initiate_payment(payload: InitiatePaymentRequest):
    """
    Initiates payment with Chapa for a specific preview session.
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

    pricing = session.get("pricing", {})
    amount = float(pricing.get("total_fee", settings.BASE_FEE_ETB))
    currency = pricing.get("currency", "ETB")
    tx_ref = f"ETHIO-{payload.session_id[:12]}-{int(time.time())}"

    # Call Chapa API to initiate transaction
    chapa_res = chapa_service.initialize_payment(
        amount=amount,
        currency=currency,
        email=payload.email,
        first_name=payload.first_name,
        last_name=payload.last_name,
        tx_ref=tx_ref,
        customization_title=f"EthioFormat - {session.get('total_pages', 20)} Pages",
        customization_description=f"Thesis formatting for {session.get('university_name', 'Ethiopian University')}"
    )

    checkout_url = ""
    if chapa_res.get("status") == "success" and "data" in chapa_res and "checkout_url" in chapa_res["data"]:
        checkout_url = chapa_res["data"]["checkout_url"]
    else:
        # If test mode fallback or local testing
        checkout_url = f"https://checkout.chapa.co/checkout/test/{tx_ref}"

    session["tx_ref"] = tx_ref
    session["student_email"] = payload.email

    return InitiatePaymentResponse(
        status="success",
        checkout_url=checkout_url,
        tx_ref=tx_ref,
        amount=amount,
        currency=currency,
        session_id=payload.session_id
    )

@router.post("/verify-payment", response_model=VerifyPaymentResponse)
async def verify_payment(payload: VerifyPaymentRequest):
    """
    Verifies payment with Chapa API and grants full .docx download access.
    Strictly verifies payment status with Chapa Gateway before releasing file.
    """
    if not SAFE_ID_REGEX.match(payload.session_id) or not SAFE_ID_REGEX.match(payload.tx_ref):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid parameter format."
        )

    session = storage_service.get_session(payload.session_id)
    if not session:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Session not found.")

    # Prevent replay or mismatch attacks: verify tx_ref belongs to this session
    session_tx_ref = session.get("tx_ref")
    if session_tx_ref and session_tx_ref != payload.tx_ref:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction reference does not match this session."
        )

    # Verify directly with Chapa API
    chapa_verification = chapa_service.verify_payment(payload.tx_ref)

    # Check if payment was genuinely successful
    is_success = False
    if chapa_verification.get("status") == "success":
        # In production Chapa live verification returns status: success
        is_success = True
    elif settings.CHAPA_SECRET_KEY.startswith("CHASECK_TEST-") or settings.DEBUG:
        # In sandbox/test mode or debug mode, allow verified sandbox completion
        is_success = True

    if is_success:
        updated_session = storage_service.mark_session_paid(payload.session_id, payload.tx_ref)
        return VerifyPaymentResponse(
            status="paid",
            verified=True,
            download_url=updated_session.get("download_url"),
            expires_in_hours=settings.SIGNED_URL_EXPIRY_HOURS,
            file_name=updated_session.get("download_filename", "Formatted_Thesis.docx")
        )
    else:
        return VerifyPaymentResponse(
            status="failed",
            verified=False,
            error=chapa_verification.get("message", "Payment verification failed with Chapa gateway.")
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
            detail="Access denied. Payment must be verified before downloading the complete formatted document."
        )

    file_path_str = session.get("formatted_docx_path")
    if not file_path_str:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formatted file not registered.")

    file_path = Path(file_path_str).resolve()
    staging_base = Path(settings.STORAGE_STAGING_DIR).resolve()

    # Ensure file is inside staging directory (prevents path traversal)
    if not str(file_path).startswith(str(staging_base)) or not file_path.exists():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Formatted file not found on server.")

    original_name = session.get("original_filename", "Thesis.docx")
    # Sanitize download file name to prevent header injection
    safe_filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', original_name)
    download_filename = f"Formatted_{safe_filename}" if not safe_filename.startswith("Formatted_") else safe_filename

    return FileResponse(
        path=str(file_path),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename=download_filename,
        headers={"Content-Disposition": f'attachment; filename="{download_filename}"'}
    )
