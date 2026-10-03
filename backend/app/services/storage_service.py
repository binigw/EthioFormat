import os
import shutil
import time
from pathlib import Path
from typing import Dict, Optional, Any
from app.config import settings

class StorageService:
    def __init__(self):
        self.staging_dir = Path(settings.STORAGE_STAGING_DIR)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self.supabase_client = self._init_supabase()

    def _init_supabase(self):
        if settings.SUPABASE_URL and settings.SUPABASE_SERVICE_ROLE_KEY and "supabase.co" in settings.SUPABASE_URL:
            try:
                from supabase import create_client
                client = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_ROLE_KEY)
                print(f"[Supabase] Connected to {settings.SUPABASE_URL} (Bucket: {settings.SUPABASE_BUCKET_NAME})")
                return client
            except Exception as e:
                print(f"[Supabase] Note: Supabase client initialization: {e}")
                return None
        return None

    def get_session_dir(self, session_id: str) -> Path:
        session_dir = self.staging_dir / session_id
        session_dir.mkdir(parents=True, exist_ok=True)
        return session_dir

    def register_session(self, session_id: str, data: Dict[str, Any]):
        data["created_at"] = time.time()
        self._sessions[session_id] = data

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        return self._sessions.get(session_id)

    def mark_session_paid(self, session_id: str, tx_ref: str) -> Dict[str, Any]:
        session = self._sessions.get(session_id)
        if not session:
            # Reconstruct session if present in staging
            session_dir = self.get_session_dir(session_id)
            formatted_file = session_dir / "formatted_thesis.docx"
            session = {
                "session_id": session_id,
                "formatted_docx_path": str(formatted_file),
                "original_filename": "Formatted_Thesis.docx"
            }
            self._sessions[session_id] = session

        session["is_paid"] = True
        session["tx_ref"] = tx_ref
        session["paid_at"] = time.time()

        formatted_docx = session.get("formatted_docx_path")
        file_name = session.get("original_filename", "Formatted_Thesis.docx")
        if not file_name.startswith("Formatted_"):
            file_name = f"Formatted_{file_name}"

        signed_url = None

        # Attempt Supabase Storage Upload & 24h Signed URL generation
        if self.supabase_client and formatted_docx and Path(formatted_docx).exists():
            try:
                bucket = settings.SUPABASE_BUCKET_NAME
                storage_path = f"theses/{session_id}/{file_name}"
                with open(formatted_docx, "rb") as f:
                    file_content = f.read()
                    self.supabase_client.storage.from_(bucket).upload(
                        path=storage_path,
                        file=file_content,
                        file_options={
                            "content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                            "upsert": "true"
                        }
                    )
                # Create a 24-hour signed download URL
                signed_res = self.supabase_client.storage.from_(bucket).create_signed_url(
                    storage_path,
                    expires_in=settings.SIGNED_URL_EXPIRY_HOURS * 3600
                )
                if isinstance(signed_res, dict) and "signedURL" in signed_res:
                    signed_url = signed_res["signedURL"]
                elif hasattr(signed_res, "signed_url"):
                    signed_url = signed_res.signed_url
                print(f"[Supabase] File uploaded successfully to {storage_path}")
            except Exception as e:
                print(f"[Supabase] Storage notice: {e}")

        # Local secure download fallback if storage unavailable
        if not signed_url:
            signed_url = f"/api/download/{session_id}"

        session["download_url"] = signed_url
        session["download_filename"] = file_name
        return session

storage_service = StorageService()
