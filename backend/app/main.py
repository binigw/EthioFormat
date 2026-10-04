import os
import sys
import io
import asyncio
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from app.config import settings
from app.routers import presets, preview, payment
from app.services.cbe_imap_service import cbe_imap_service

# Ensure standard output and error streams handle UTF-8 and unicode seamlessly
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass
elif hasattr(sys.stdout, 'buffer'):
    try:
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    except Exception:
        pass

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Start automated Gmail IMAP background poller
    task = asyncio.create_task(
        cbe_imap_service.start_background_loop(settings.IMAP_POLL_INTERVAL_SECONDS)
    )
    yield
    # Shutdown: Cleanly terminate worker
    cbe_imap_service.stop_background_loop()
    task.cancel()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="EthioFormat — Automated Ethiopian Academic Thesis Formatting Backend",
    lifespan=lifespan
)

# Allowed CORS origins
allowed_origins = [
    "https://ethioformat.netlify.app",
    "http://localhost:3000",
    "http://127.0.0.1:3000"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins if not settings.DEBUG else ["*"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS", "HEAD"],
    allow_headers=["*"],
)

@app.middleware("http")
async def add_security_headers(request, call_next):
    response = await call_next(request)
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "SAMEORIGIN"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
    return response

# Register routers
app.include_router(presets.router)
app.include_router(preview.router)
app.include_router(payment.router)

SAMPLE_DOCX = Path(__file__).parent.parent / "sample_ethiopian_thesis.docx"

@app.get("/")
@app.head("/")
def root():
    """
    Root endpoint for UptimeRobot, Render health checks, and monitoring services.
    """
    return {
        "status": "alive",
        "app": settings.APP_NAME,
        "version": settings.APP_VERSION,
        "message": "EthioFormat Backend is running smoothly."
    }

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
        "base_pages": settings.BASE_PAGE_THRESHOLD,
        "cbe_account": settings.CBE_ACCOUNT_NUMBER,
        "imap_worker_active": cbe_imap_service.is_configured()
    }
