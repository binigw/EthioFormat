import os
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.config import settings
from app.routers import presets, preview, payment

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="EthioFormat — Automated Ethiopian Academic Thesis Formatting Backend"
)

# Enable CORS for Next.js preview & local environment
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routers
app.include_router(presets.router)
app.include_router(preview.router)
app.include_router(payment.router)

SAMPLE_DOCX = Path("/home/user/backend/sample_ethiopian_thesis.docx")

@app.get("/api/sample-thesis")
def get_sample_thesis():
    if not SAMPLE_DOCX.exists():
        from create_sample import create_sample_thesis
        create_sample_thesis(str(SAMPLE_DOCX))
    return FileResponse(
        path=str(SAMPLE_DOCX),
        media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        filename="Sample_AAU_MSc_Thesis.docx"
    )

@app.get("/api/health")
def health_check():
    return {
        "status": "healthy",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "base_fee": settings.BASE_FEE_ETB,
        "base_pages": settings.BASE_PAGE_THRESHOLD
    }
