import os
import json
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
        """
        Stores session in-memory and persistently on disk (session_metadata.json)
        so any Gunicorn worker process or container restart retains the session.
        """
        data["created_at"] = time.time()
        self._sessions[session_id] = data

        try:
            session_dir = self.get_session_dir(session_id)
            meta_path = session_dir / "session_metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[StorageService] Failed to persist session metadata: {e}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves session data from:
        1. In-memory dictionary
        2. Persistent disk metadata (session_metadata.json)
        3. Formatted docx directory fallback
        """
        # 1. In-memory check
        if session_id in self._sessions:
            return self._sessions[session_id]

        # 2. Disk metadata check
        try:
            session_dir = self.staging_dir / session_id
            meta_path = session_dir / "session_metadata.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._sessions[session_id] = data
                    return data
        except Exception as e:
            print(f"[StorageService] Disk metadata read error for {session_id}: {e}")

        # 3. File existence fallback
        session_dir = self.staging_dir / session_id
        formatted_file = session_dir / "formatted_thesis.docx"
        if formatted_file.exists():
            data = {
                "session_id": session_id,
                "formatted_docx_path": str(formatted_file),
                "original_filename": "Formatted_Thesis.docx",
                "total_pages": 20,
                "pricing": {"base_fee": 50.0, "incremental_fee": 0.0, "total_fee": 50.0, "currency": "ETB"},
                "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
                "cbe_account_name": settings.CBE_ACCOUNT_NAME,
                "is_paid": False
            }
            self._sessions[session_id] = data
            return data

        return None

    def mark_session_paid(self, session_id: str, tx_ref: str) -> Dict[str, Any]:
        session = self.get_session(session_id)
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

        # Persist updated paid state to disk metadata
        try:
            session_dir = self.get_session_dir(session_id)
            meta_path = session_dir / "session_metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[StorageService] Failed to persist paid session metadata: {e}")

        return session

storage_service = StorageService()
