import os
import gc
import json
import uuid
import re
import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.models.formatting import PreviewResponseModel, PreviewMetadataModel
from app.services.docx_formatter import docx_formatter
from app.services.converter import converter_service
from app.services.storage_service import storage_service
from app.config import settings

router = APIRouter(prefix="/api/preview", tags=["preview"])

MAX_FILE_SIZE_BYTES = 50 * 1024 * 1024

@router.post("", response_model=PreviewResponseModel)
async def generate_free_preview(
    file: UploadFile = File(...),
    preset_id: str = Form("aau"),
    custom_rules: Optional[str] = Form(None)
):
    """
    Secure 3-Page Free Preview Paywall Endpoint:
    1. Validates file extension, mime-type, and file size (< 50MB).
    2. Runs python-docx formatting across entire document.
    3. Converts to PDF to compute dynamic page count.
    4. Extracts and renders ONLY the first 3 pages as high-res base64 PNGs.
    5. Computes exact dynamic pricing.
    6. Safely retains full formatted .docx in isolated persistent session storage.
    """
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing file name.")

    clean_filename = Path(file.filename).name
    if not clean_filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only Microsoft Word (.docx) files are supported."
        )

    valid_preset_ids = [p["id"] for p in docx_formatter.presets_data.get("presets", [])] + ["custom"]
    if preset_id not in valid_preset_ids:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid preset_id. Must be one of registered universities or 'custom'."
        )

    parsed_custom_rules = None
    if preset_id == "custom" and custom_rules and custom_rules.strip():
        try:
            parsed_custom_rules = json.loads(custom_rules)
            if not isinstance(parsed_custom_rules, dict):
                raise ValueError()
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid JSON structure in custom_rules."
            )

    session_id = f"sess_{uuid.uuid4().hex[:16]}"
    session_dir = storage_service.get_session_dir(session_id)

    input_docx_path = session_dir / "input_original.docx"
    formatted_docx_path = session_dir / "formatted_thesis.docx"

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Uploaded file is empty.")
        
        if len(content) > MAX_FILE_SIZE_BYTES:
            raise HTTPException(
                status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                detail="Uploaded file exceeds 50MB maximum allowable size."
            )

        with open(input_docx_path, "wb") as f:
            f.write(content)
        del content

        # 1. Format document with python-docx
        format_result = docx_formatter.format_document(
            input_docx_path=str(input_docx_path),
            output_docx_path=str(formatted_docx_path),
            preset_id=preset_id,
            custom_rules=parsed_custom_rules
        )

        # 2. Run conversion pipeline: PDF -> dynamic page count -> 3-page base64 rendering -> dynamic pricing
        pipeline_result = converter_service.process_document_pipeline(
            formatted_docx_path=str(formatted_docx_path),
            work_dir=str(session_dir)
        )

        total_pages = pipeline_result["total_pages"]
        preview_pages = pipeline_result["preview_pages"]
        pricing = pipeline_result["pricing"]

        university_name = "Ethiopian Academic Standard"
        for p in docx_formatter.presets_data.get("presets", []):
            if p["id"] == preset_id:
                university_name = p["display_name"]
                break
        if preset_id == "custom":
            university_name = "Custom Thesis Configuration"

        # 3. Register session in persistent storage cache
        storage_service.register_session(session_id, {
            "session_id": session_id,
            "original_filename": clean_filename,
            "formatted_docx_path": str(formatted_docx_path),
            "input_docx_path": str(input_docx_path),
            "preset_id": preset_id,
            "custom_rules": parsed_custom_rules,
            "total_pages": total_pages,
            "pricing": pricing.model_dump(),
            "university_name": university_name,
            "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
            "cbe_account_name": settings.CBE_ACCOUNT_NAME,
            "is_paid": False
        })

        return PreviewResponseModel(
            status="success",
            session_id=session_id,
            total_pages=total_pages,
            preview_pages=preview_pages,
            pricing=pricing,
            cbe_account_number=settings.CBE_ACCOUNT_NUMBER,
            cbe_account_name=settings.CBE_ACCOUNT_NAME,
            metadata=PreviewMetadataModel(
                filename=clean_filename,
                formatted_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                university=university_name,
                preset_id=preset_id
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Thesis formatting failed: {str(e)}"
        )
    finally:
        try:
            await file.close()
        except Exception:
            pass
        gc.collect()
