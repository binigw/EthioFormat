import os
import json
import uuid
import datetime
from pathlib import Path
from typing import Optional
from fastapi import APIRouter, UploadFile, File, Form, HTTPException, status
from app.models.formatting import PreviewResponseModel, PreviewMetadataModel
from app.services.docx_formatter import docx_formatter
from app.services.converter import converter_service
from app.services.storage_service import storage_service

router = APIRouter(prefix="/api/preview", tags=["preview"])

@router.post("", response_model=PreviewResponseModel)
async def generate_free_preview(
    file: UploadFile = File(...),
    preset_id: str = Form("aau"),
    custom_rules: Optional[str] = Form(None)
):
    """
    Secure 3-Page Free Preview Paywall Endpoint:
    1. Receives uploaded .docx file and selected university preset or custom rules.
    2. Runs python-docx formatting across entire document.
    3. Headless conversion to PDF to dynamically compute exact total pages.
    4. Extracts and renders ONLY the first 3 pages (Cover, Approval, TOC) as high-res base64 PNGs.
    5. Computes exact dynamic pricing (Base 50 ETB for <=20 pages + 1.50 ETB / extra page).
    6. Safely retains full formatted .docx in encrypted session cache without exposing it to client.
    """
    if not file.filename:
        raise HTTPException(status_code=400, detail="Missing file name.")
    
    if not file.filename.lower().endswith(".docx"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid file format. Only Microsoft Word (.docx) files are supported."
        )

    # Parse custom rules if provided
    parsed_custom_rules = None
    if custom_rules and custom_rules.strip():
        try:
            parsed_custom_rules = json.loads(custom_rules)
        except json.JSONDecodeError:
            raise HTTPException(status_code=400, detail="Invalid JSON format in custom_rules.")

    # Generate unique session ID
    session_id = f"sess_{uuid.uuid4().hex[:16]}"
    session_dir = storage_service.get_session_dir(session_id)

    # Save uploaded input file
    input_docx_path = session_dir / "input_original.docx"
    formatted_docx_path = session_dir / "formatted_thesis.docx"

    try:
        content = await file.read()
        if len(content) == 0:
            raise HTTPException(status_code=400, detail="Uploaded file is empty.")
        
        with open(input_docx_path, "wb") as f:
            f.write(content)

        # 1. Format the document with python-docx
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

        # Resolve university display name
        university_name = "Ethiopian Academic Standard"
        for p in docx_formatter.presets_data.get("presets", []):
            if p["id"] == preset_id:
                university_name = p["display_name"]
                break
        if preset_id == "custom":
            university_name = "Custom Thesis Configuration"

        # 3. Register session in secure storage cache
        storage_service.register_session(session_id, {
            "session_id": session_id,
            "original_filename": file.filename,
            "formatted_docx_path": str(formatted_docx_path),
            "input_docx_path": str(input_docx_path),
            "preset_id": preset_id,
            "custom_rules": parsed_custom_rules,
            "total_pages": total_pages,
            "pricing": pricing.model_dump(),
            "university_name": university_name,
            "is_paid": False
        })

        return PreviewResponseModel(
            status="success",
            session_id=session_id,
            total_pages=total_pages,
            preview_pages=preview_pages,
            pricing=pricing,
            metadata=PreviewMetadataModel(
                filename=file.filename,
                formatted_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),
                university=university_name,
                preset_id=preset_id
            )
        )

    except HTTPException:
        raise
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Thesis formatting and preview generation failed: {str(e)}"
        )
