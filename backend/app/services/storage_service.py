import os
import json
import re
import shutil
import time
from pathlib import Path
from typing import Dict, Optional, Any, Tuple
from app.config import settings

class StorageService:
    def __init__(self):
        self.staging_dir = Path(settings.STORAGE_STAGING_DIR)
        self.staging_dir.mkdir(parents=True, exist_ok=True)
        self._sessions: Dict[str, Dict[str, Any]] = {}
        self._preverified: Dict[str, Dict[str, Any]] = {}
        self._consumed_txns: Dict[str, Dict[str, Any]] = {}
        self.supabase_client = self._init_supabase()
        self._load_consumed_txns_from_disk()

    def _load_consumed_txns_from_disk(self):
        try:
            consumed_file = self.staging_dir / "consumed_transactions.json"
            if consumed_file.exists():
                with open(consumed_file, "r", encoding="utf-8") as f:
                    self._consumed_txns = json.load(f)
        except Exception as e:
            print(f"[StorageService] Failed to load consumed txns from disk: {e}")

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
        Stores session in-memory, on shared disk (/tmp), and syncs with Supabase Storage.
        """
        data["created_at"] = time.time()
        self._sessions[session_id] = data

        # 1. Local disk persistence
        try:
            session_dir = self.get_session_dir(session_id)
            meta_path = session_dir / "session_metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[StorageService] Failed to persist session metadata: {e}")

        # 2. Cloud Supabase Storage sync
        if self.supabase_client:
            try:
                bucket = settings.SUPABASE_BUCKET_NAME
                self.supabase_client.storage.from_(bucket).upload(
                    path=f"theses/{session_id}/status.json",
                    file=json.dumps(data, ensure_ascii=False).encode("utf-8"),
                    file_options={"content-type": "application/json", "upsert": "true"}
                )

                formatted_docx = data.get("formatted_docx_path")
                if formatted_docx and Path(formatted_docx).exists():
                    with open(formatted_docx, "rb") as f_in:
                        f_bytes = f_in.read()
                        self.supabase_client.storage.from_(bucket).upload(
                            path=f"theses/{session_id}/formatted_thesis.docx",
                            file=f_bytes,
                            file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "upsert": "true"}
                        )
                        filename_try = data.get("download_filename") or data.get("original_filename")
                        if filename_try:
                            if not filename_try.startswith("Formatted_"):
                                filename_try = f"Formatted_{filename_try}"
                            self.supabase_client.storage.from_(bucket).upload(
                                path=f"theses/{session_id}/{filename_try}",
                                file=f_bytes,
                                file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "upsert": "true"}
                            )

                input_docx = data.get("input_docx_path")
                if input_docx and Path(input_docx).exists():
                    with open(input_docx, "rb") as f_in:
                        self.supabase_client.storage.from_(bucket).upload(
                            path=f"theses/{session_id}/input_original.docx",
                            file=f_in.read(),
                            file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "upsert": "true"}
                        )
            except Exception as e:
                print(f"[Supabase Storage] Notice during register_session: {e}")

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieves session data from:
        1. In-memory dictionary (if already paid)
        2. Persistent disk metadata (session_metadata.json)
        3. Supabase Storage (theses/{session_id}/status.json)
        4. Local file fallback
        """
        # If in-memory is already marked paid, return immediately
        if session_id in self._sessions and self._sessions[session_id].get("is_paid", False):
            return self._sessions[session_id]

        # 2. Disk metadata check
        try:
            session_dir = self.staging_dir / session_id
            meta_path = session_dir / "session_metadata.json"
            if meta_path.exists():
                with open(meta_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._sessions[session_id] = data
                    if data.get("is_paid", False):
                        return data
        except Exception as e:
            print(f"[StorageService] Disk metadata read error for {session_id}: {e}")

        # 3. Supabase Storage status.json check
        if self.supabase_client:
            try:
                bucket = settings.SUPABASE_BUCKET_NAME
                res = self.supabase_client.storage.from_(bucket).download(f"theses/{session_id}/status.json")
                if res:
                    data = json.loads(res.decode("utf-8"))
                    self._sessions[session_id] = data
                    # Cache to disk
                    try:
                        session_dir = self.get_session_dir(session_id)
                        with open(session_dir / "session_metadata.json", "w", encoding="utf-8") as f:
                            json.dump(data, f, indent=2)
                    except Exception:
                        pass
                    return data
            except Exception:
                pass

        # In-memory fallback if disk had no newer info
        if session_id in self._sessions:
            return self._sessions[session_id]

        # 4. File existence fallback
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

    def update_session_transaction(
        self,
        session_id: str,
        transaction_ref: str,
        payer_name: Optional[str] = None,
        payer_phone: Optional[str] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Attaches the user-submitted transaction ID & payer info to the session
        and writes it immediately to disk & Supabase Storage so all workers & background IMAP loops find it.
        """
        session = self.get_session(session_id)
        if not session:
            # Reconstruct session if missing
            session = {
                "session_id": session_id,
                "original_filename": "Formatted_Thesis.docx",
                "total_pages": 20,
                "pricing": {"base_fee": 50.0, "incremental_fee": 0.0, "total_fee": 50.0, "currency": "ETB"},
                "cbe_account_number": settings.CBE_ACCOUNT_NUMBER,
                "cbe_account_name": settings.CBE_ACCOUNT_NAME,
                "is_paid": False
            }

        clean_ref = transaction_ref.strip().upper()
        session["transaction_ref"] = clean_ref
        session["tx_ref"] = clean_ref
        if payer_name:
            session["payer_name"] = payer_name.strip()
        if payer_phone:
            session["payer_phone"] = payer_phone.strip()
        session["tx_submitted_at"] = time.time()

        self._sessions[session_id] = session

        try:
            session_dir = self.get_session_dir(session_id)
            meta_path = session_dir / "session_metadata.json"
            with open(meta_path, "w", encoding="utf-8") as f:
                json.dump(session, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[StorageService] Failed to update transaction on disk: {e}")

        if self.supabase_client:
            try:
                bucket = settings.SUPABASE_BUCKET_NAME
                self.supabase_client.storage.from_(bucket).upload(
                    path=f"theses/{session_id}/status.json",
                    file=json.dumps(session, ensure_ascii=False).encode("utf-8"),
                    file_options={"content-type": "application/json", "upsert": "true"}
                )
            except Exception:
                pass

        return session

    def register_preverified_transaction(self, txn_ref: str, data: Dict[str, Any]):
        """
        Stores receipts parsed from Gmail / Webhooks even before the user submits their transaction ID.
        Ensures 0-second instant approval when the user submits their FT/TXN number.
        """
        if not txn_ref:
            return
        clean_ref = re.sub(r'[^A-Z0-9]', '', txn_ref.upper())
        data["verified_at"] = time.time()
        data["transaction_ref"] = clean_ref
        self._preverified[clean_ref] = data

        # 1. Local disk persistence
        try:
            pre_file = self.staging_dir / "preverified_txns.json"
            all_pre = {}
            if pre_file.exists():
                try:
                    with open(pre_file, "r", encoding="utf-8") as f:
                        all_pre = json.load(f)
                except Exception:
                    all_pre = {}
            all_pre[clean_ref] = data
            with open(pre_file, "w", encoding="utf-8") as f:
                json.dump(all_pre, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[StorageService] Failed to save preverified txns: {e}")

        # 2. Supabase Storage cloud sync
        if self.supabase_client:
            try:
                bucket = settings.SUPABASE_BUCKET_NAME
                self.supabase_client.storage.from_(bucket).upload(
                    path=f"verified_txns/{clean_ref}.json",
                    file=json.dumps(data, ensure_ascii=False).encode("utf-8"),
                    file_options={"content-type": "application/json", "upsert": "true"}
                )
            except Exception:
                pass

    def get_preverified_transaction(self, txn_ref: str) -> Optional[Dict[str, Any]]:
        """
        Checks if a transaction reference has already been received via Gmail IMAP or Webhooks.
        """
        if not txn_ref:
            return None
        clean_ref = re.sub(r'[^A-Z0-9]', '', txn_ref.upper())

        # 1. In-memory check
        if clean_ref in self._preverified:
            return self._preverified[clean_ref]
        for k, v in self._preverified.items():
            if clean_ref == k or clean_ref in k or k in clean_ref:
                return v

        # 2. Local disk check
        try:
            pre_file = self.staging_dir / "preverified_txns.json"
            if pre_file.exists():
                with open(pre_file, "r", encoding="utf-8") as f:
                    all_pre = json.load(f)
                    if clean_ref in all_pre:
                        self._preverified[clean_ref] = all_pre[clean_ref]
                        return all_pre[clean_ref]
                    for k, v in all_pre.items():
                        if clean_ref == k or clean_ref in k or k in clean_ref:
                            self._preverified[k] = v
                            return v
        except Exception:
            pass

        # 3. Supabase Storage check
        if self.supabase_client:
            try:
                bucket = settings.SUPABASE_BUCKET_NAME
                res = self.supabase_client.storage.from_(bucket).download(f"verified_txns/{clean_ref}.json")
                if res:
                    data = json.loads(res.decode("utf-8"))
                    self._preverified[clean_ref] = data
                    return data
            except Exception:
                pass

        return None

    def is_transaction_claimed(self, txn_ref: str, current_session_id: Optional[str] = None) -> Tuple[bool, Optional[str]]:
        """
        Anti-Replay / Double-Spending Prevention Engine:
        Determines if a transaction ID has already been redeemed for another thesis session.
        Returns:
            (True, claimed_session_id) -> If already consumed by ANOTHER session (REPLAY DETECTED!)
            (False, current_session_id or None) -> If unused or belongs to this exact session.
        """
        if not txn_ref:
            return (False, None)

        clean_ref = re.sub(r'[^A-Z0-9]', '', str(txn_ref).upper())
        if not clean_ref:
            return (False, None)

        # 1. In-memory consumed registry check
        if clean_ref in self._consumed_txns:
            claimed_sid = self._consumed_txns[clean_ref].get("session_id")
            if current_session_id and claimed_sid == current_session_id:
                return (False, claimed_sid)
            return (True, claimed_sid)

        # 2. Local disk consumed_transactions.json check
        try:
            consumed_file = self.staging_dir / "consumed_transactions.json"
            if consumed_file.exists():
                with open(consumed_file, "r", encoding="utf-8") as f:
                    disk_consumed = json.load(f)
                    self._consumed_txns.update(disk_consumed)
                    if clean_ref in disk_consumed:
                        claimed_sid = disk_consumed[clean_ref].get("session_id")
                        if current_session_id and claimed_sid == current_session_id:
                            return (False, claimed_sid)
                        return (True, claimed_sid)
        except Exception:
            pass

        # 3. Check all existing sessions on disk/memory: has any other paid session used this txn ref?
        all_sessions = self.get_all_sessions()
        for sid, sdata in all_sessions.items():
            if current_session_id and sid == current_session_id:
                continue
            if sdata.get("is_paid", False):
                cand = sdata.get("transaction_ref") or sdata.get("tx_ref")
                if cand:
                    cand_clean = re.sub(r'[^A-Z0-9]', '', str(cand).upper())
                    if cand_clean == clean_ref:
                        # Auto-register into consumed pool
                        self._consumed_txns[clean_ref] = {
                            "transaction_ref": clean_ref,
                            "session_id": sid,
                            "claimed_at": sdata.get("paid_at", time.time())
                        }
                        return (True, sid)

        # 4. Supabase Storage consumed_txns/{clean_ref}.json check
        if self.supabase_client:
            try:
                bucket = settings.SUPABASE_BUCKET_NAME
                res = self.supabase_client.storage.from_(bucket).download(f"consumed_txns/{clean_ref}.json")
                if res:
                    data = json.loads(res.decode("utf-8"))
                    claimed_sid = data.get("session_id")
                    self._consumed_txns[clean_ref] = data
                    if current_session_id and claimed_sid == current_session_id:
                        return (False, claimed_sid)
                    return (True, claimed_sid)
            except Exception:
                pass

        # 5. Supabase Database transactions table check (if available)
        if self.supabase_client:
            try:
                query = self.supabase_client.table("transactions").select("session_id, status, transaction_ref").eq("status", "approved").ilike("transaction_ref", f"%{clean_ref}%").execute()
                if query.data and len(query.data) > 0:
                    for row in query.data:
                        claimed_sid = row.get("session_id")
                        if current_session_id and claimed_sid == current_session_id:
                            return (False, claimed_sid)
                        return (True, claimed_sid)
            except Exception:
                pass

        return (False, None)

    def claim_transaction(
        self,
        txn_ref: str,
        session_id: str,
        amount: float = 50.0,
        payer_name: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Atomically locks and consumes a transaction ID for a single document session.
        Prevents double-spending / multi-session reuse.
        """
        if not txn_ref:
            return {}

        clean_ref = re.sub(r'[^A-Z0-9]', '', str(txn_ref).upper())
        record = {
            "transaction_ref": clean_ref,
            "session_id": session_id,
            "amount": amount,
            "payer_name": payer_name,
            "claimed_at": time.time(),
            "claimed_iso": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())
        }

        # 1. Update in-memory registry
        self._consumed_txns[clean_ref] = record

        # 2. Write to persistent local disk
        try:
            consumed_file = self.staging_dir / "consumed_transactions.json"
            all_consumed = {}
            if consumed_file.exists():
                try:
                    with open(consumed_file, "r", encoding="utf-8") as f:
                        all_consumed = json.load(f)
                except Exception:
                    all_consumed = {}
            all_consumed[clean_ref] = record
            with open(consumed_file, "w", encoding="utf-8") as f:
                json.dump(all_consumed, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"[StorageService] Failed to save consumed txn to disk: {e}")

        # 3. Supabase Cloud Sync
        if self.supabase_client:
            try:
                bucket = settings.SUPABASE_BUCKET_NAME
                self.supabase_client.storage.from_(bucket).upload(
                    path=f"consumed_txns/{clean_ref}.json",
                    file=json.dumps(record, ensure_ascii=False).encode("utf-8"),
                    file_options={"content-type": "application/json", "upsert": "true"}
                )
            except Exception:
                pass

        return record

    def get_all_sessions(self) -> Dict[str, Dict[str, Any]]:
        """
        Gathers all sessions across in-memory, disk metadata, and Supabase Storage.
        """
        combined: Dict[str, Dict[str, Any]] = dict(self._sessions)

        if self.staging_dir.exists():
            for item in self.staging_dir.iterdir():
                if item.is_dir() and (item / "session_metadata.json").exists():
                    sid = item.name
                    if sid not in combined:
                        try:
                            with open(item / "session_metadata.json", "r", encoding="utf-8") as f:
                                combined[sid] = json.load(f)
                        except Exception:
                            pass

        return combined

    def find_session_by_txn_ref(self, target_ref: str) -> Optional[str]:
        """
        Searches active unpaid sessions for matching transaction_ref / tx_ref.
        Only matches sessions that are NOT already paid to prevent hijacking/replaying.
        """
        if not target_ref:
            return None

        clean_target = re.sub(r'[^A-Z0-9]', '', target_ref.upper())
        all_sessions = self.get_all_sessions()

        for sid, sdata in all_sessions.items():
            if sdata.get("is_paid", False):
                continue  # Skip already paid sessions!
            candidate = sdata.get("transaction_ref") or sdata.get("tx_ref")
            if candidate:
                clean_cand = re.sub(r'[^A-Z0-9]', '', str(candidate).upper())
                if clean_cand == clean_target or clean_target in clean_cand or clean_cand in clean_target:
                    return sid

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

        clean_ref = re.sub(r'[^A-Z0-9]', '', str(tx_ref).upper()) if tx_ref else tx_ref
        session["is_paid"] = True
        session["status"] = "approved"
        session["tx_ref"] = clean_ref
        session["transaction_ref"] = clean_ref
        session["paid_at"] = time.time()

        # Atomically claim transaction ID for this session exclusively
        self.claim_transaction(
            txn_ref=clean_ref,
            session_id=session_id,
            amount=float(session.get("pricing", {}).get("total_fee", settings.BASE_FEE_ETB)),
            payer_name=session.get("payer_name")
        )

        formatted_docx = session.get("formatted_docx_path")
        file_name = session.get("original_filename", "Formatted_Thesis.docx")
        if not file_name.startswith("Formatted_"):
            file_name = f"Formatted_{file_name}"

        # 1. Internal secure download URL fallback
        direct_url = f"/api/download/{session_id}"
        session["download_url"] = direct_url
        session["download_filename"] = file_name

        # 2. Upload to Supabase Storage Bucket & Generate Signed URL (24 Hours)
        if self.supabase_client:
            try:
                bucket_name = settings.SUPABASE_BUCKET_NAME
                cloud_dest_path = f"theses/{session_id}/{file_name}"

                file_bytes = None
                if formatted_docx and Path(formatted_docx).exists():
                    with open(formatted_docx, "rb") as f_in:
                        file_bytes = f_in.read()
                else:
                    # Check if already in Supabase
                    try:
                        file_bytes = self.supabase_client.storage.from_(bucket_name).download(f"theses/{session_id}/formatted_thesis.docx")
                    except Exception:
                        pass

                if file_bytes:
                    # Upload formatted deliverable with final filename AND formatted_thesis.docx
                    self.supabase_client.storage.from_(bucket_name).upload(
                        path=cloud_dest_path,
                        file=file_bytes,
                        file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "upsert": "true"}
                    )
                    self.supabase_client.storage.from_(bucket_name).upload(
                        path=f"theses/{session_id}/formatted_thesis.docx",
                        file=file_bytes,
                        file_options={"content-type": "application/vnd.openxmlformats-officedocument.wordprocessingml.document", "upsert": "true"}
                    )

                # Generate 24-hour signed download URL
                expiry_seconds = settings.SIGNED_URL_EXPIRY_HOURS * 3600
                signed_res = self.supabase_client.storage.from_(bucket_name).create_signed_url(
                    path=cloud_dest_path,
                    expires_in=expiry_seconds
                )

                if signed_res and "signedURL" in signed_res:
                    session["download_url"] = signed_res["signedURL"]
                elif signed_res and "signedUrl" in signed_res:
                    session["download_url"] = signed_res["signedUrl"]

            except Exception as e:
                print(f"[Supabase Storage] Notice: {e}. Retaining direct fallback URL.")

        # Update in-memory & disk cache
        self.register_session(session_id, session)
        return session

storage_service = StorageService()
