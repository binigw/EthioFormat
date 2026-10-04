import imaplib
import email
from email.header import decode_header
import asyncio
import time
import re
import datetime
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.cbe_email_parser import cbe_email_parser
from app.services.storage_service import storage_service

class CBEImapService:
    """
    Automated Gmail IMAP Reader Service for Commercial Bank of Ethiopia (CBE) Receipts.
    Connects to Gmail via imaplib over SSL, polls unread & recent CBE transaction alert emails,
    extracts the Transaction ID and Amount via Regex, and verifies pending transactions.
    """

    def __init__(self):
        self.server = settings.GMAIL_IMAP_SERVER
        self.port = settings.GMAIL_IMAP_PORT
        self.user = settings.GMAIL_IMAP_USER
        self.password = settings.GMAIL_IMAP_PASSWORD
        self._is_running = False
        self._last_log_time = 0

    def is_configured(self) -> bool:
        return bool(self.user and self.password)

    def get_status_info(self) -> Dict[str, Any]:
        return {
            "configured": self.is_configured(),
            "server": self.server,
            "port": self.port,
            "user": self.user if self.user else "(not set)",
            "password_set": bool(self.password),
            "is_running": self._is_running
        }

    def _decode_str(self, header_val: Any) -> str:
        if not header_val:
            return ""
        try:
            decoded_fragments = decode_header(header_val)
            out = []
            for frag, enc in decoded_fragments:
                if isinstance(frag, bytes):
                    out.append(frag.decode(enc or "utf-8", errors="ignore"))
                else:
                    out.append(str(frag))
            return "".join(out)
        except Exception:
            return str(header_val)

    def _extract_body(self, msg: email.message.Message) -> str:
        body_parts = []
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition", ""))
                if "attachment" not in content_disposition:
                    if content_type in ["text/plain", "text/html"]:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            try:
                                body_parts.append(payload.decode(charset, errors="ignore"))
                            except Exception:
                                body_parts.append(payload.decode("utf-8", errors="ignore"))
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                try:
                    body_parts.append(payload.decode(charset, errors="ignore"))
                except Exception:
                    body_parts.append(payload.decode("utf-8", errors="ignore"))

        return "\n".join(body_parts)

    def check_gmail_receipts(self) -> List[Dict[str, Any]]:
        """
        Synchronous single-pass IMAP check.
        Connects to Gmail, scans UNSEEN + recent emails, parses CBE alerts, and updates Supabase & disk metadata.
        """
        if not self.is_configured():
            now = time.time()
            if now - self._last_log_time > 60:
                print(
                    "[CBE IMAP] ⚠️ IMAP Not Configured: GMAIL_IMAP_USER or GMAIL_IMAP_PASSWORD environment variable is empty. "
                    "Make sure to set GMAIL_IMAP_USER and GMAIL_IMAP_PASSWORD in Render Environment variables."
                )
                self._last_log_time = now
            return []

        verified_transactions = []
        mail = None

        try:
            # 1. Connect and login via SSL
            mail = imaplib.IMAP4_SSL(self.server, self.port, timeout=12)
            mail.login(self.user, self.password)
            mail.select("INBOX")

            # 2. Gather email IDs to inspect: UNSEEN first, plus last 25 recent messages
            email_ids_to_check = set()

            # Search unseen
            status_unseen, resp_unseen = mail.search(None, "UNSEEN")
            if status_unseen == "OK" and resp_unseen and resp_unseen[0]:
                for eid in resp_unseen[0].split():
                    email_ids_to_check.add(eid)

            # Search ALL to capture recent seen emails (last 25)
            status_all, resp_all = mail.search(None, "ALL")
            if status_all == "OK" and resp_all and resp_all[0]:
                all_ids = resp_all[0].split()
                # Take last 25 emails
                for eid in all_ids[-25:]:
                    email_ids_to_check.add(eid)

            if not email_ids_to_check:
                mail.close()
                mail.logout()
                return []

            # Sort IDs numerically descending (newest first)
            sorted_eids = sorted(list(email_ids_to_check), key=lambda x: int(x) if x.isdigit() else 0, reverse=True)
            print(f"[CBE IMAP] Checking {len(sorted_eids)} recent email(s) in inbox for CBE receipts...")

            for e_id in sorted_eids:
                try:
                    res_code, msg_data = mail.fetch(e_id, "(RFC822)")
                    if res_code != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject = self._decode_str(msg.get("Subject", ""))
                    sender = self._decode_str(msg.get("From", ""))
                    body = self._extract_body(msg)

                    # Quick pre-filter: check if email contains CBE / banking keywords
                    combined_check = f"{subject} {sender} {body[:500]}".lower()
                    cbe_keywords = ["cbe", "commercial bank", "birr", "ft2", "txn", "credited", "deposited", "የግብይት", "ባንክ"]
                    if not any(kw in combined_check for kw in cbe_keywords):
                        continue

                    print(f"[CBE IMAP] Scanning relevant email #{e_id.decode() if isinstance(e_id, bytes) else e_id}: Subject='{subject}' | From='{sender}'")

                    # Parse with regex parser
                    parsed = cbe_email_parser.parse_full_cbe_payload(raw_text=body, subject=subject)
                    txn_ref = parsed.get("transaction_ref")
                    amount = parsed.get("amount")
                    payer_name = parsed.get("payer_name")

                    print(f"[CBE IMAP] Extracted metadata from email -> Txn ID: '{txn_ref}', Amount: {amount} ETB, Payer: '{payer_name}'")

                    if txn_ref and amount and amount > 0:
                        txn_ref_upper = txn_ref.strip().upper()

                        # Match with pending session in Supabase / memory / disk
                        approved = self._process_verified_txn(
                            txn_ref=txn_ref_upper,
                            amount=amount,
                            payer_name=payer_name,
                            raw_email={"subject": subject, "from": sender, "body": body[:500]}
                        )

                        if approved:
                            verified_transactions.append({
                                "transaction_ref": txn_ref_upper,
                                "amount": amount,
                                "status": "approved"
                            })
                            # Mark email as read in Gmail
                            try:
                                mail.store(e_id, "+FLAGS", "\\Seen")
                            except Exception:
                                pass

                except Exception as ex:
                    print(f"[CBE IMAP] Error processing email #{e_id}: {ex}")

            mail.close()
            mail.logout()

        except Exception as e:
            print(f"[CBE IMAP] Connection/Authentication notice: {e}")
            if mail:
                try:
                    mail.logout()
                except Exception:
                    pass

        return verified_transactions

    def _process_verified_txn(
        self,
        txn_ref: str,
        amount: float,
        payer_name: Optional[str] = None,
        raw_email: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Matches extracted transaction against:
        1. Supabase transactions table
        2. Disk metadata session records (session_metadata.json)
        3. Local in-memory session registry
        4. Pricing amount match fallback
        """
        clean_ref = re.sub(r'[^A-Z0-9]', '', txn_ref.upper())
        print(f"[CBE IMAP] Attempting to match Txn '{txn_ref}' (Normalized: '{clean_ref}', Amount: {amount} ETB)...")

        client = storage_service.supabase_client
        matched_session_id: Optional[str] = None
        expected_amount: float = 50.0

        # 1. Check Supabase transactions table
        if client:
            try:
                query = client.table("transactions").select("*").ilike("transaction_ref", f"%{txn_ref}%").execute()
                if query.data and len(query.data) > 0:
                    matched_row = query.data[0]
                    matched_session_id = matched_row.get("session_id")
                    expected_amount = float(matched_row.get("amount_expected", 50.0))
                    print(f"[CBE IMAP] Matched via Supabase transactions table -> Session: {matched_session_id}")
            except Exception as e:
                print(f"[CBE IMAP Supabase Query] Notice: {e}")

        # 2. Check Disk & Memory Sessions for matching submitted Txn ID
        if not matched_session_id:
            matched_sid = storage_service.find_session_by_txn_ref(clean_ref)
            if matched_sid:
                matched_session_id = matched_sid
                sess = storage_service.get_session(matched_sid)
                pricing = sess.get("pricing", {}) if sess else {}
                expected_amount = float(pricing.get("total_fee", 50.0))
                print(f"[CBE IMAP] Matched via Disk/Memory Session find_session_by_txn_ref -> Session: {matched_session_id}")

        # 3. Fallback: Check all active unpaid sessions by exact pricing amount if only 1 pending
        if not matched_session_id:
            all_sessions = storage_service.get_all_sessions()
            unpaid_matching = []
            for sid, sdata in all_sessions.items():
                if not sdata.get("is_paid", False):
                    pricing = sdata.get("pricing", {})
                    req_fee = float(pricing.get("total_fee", 50.0))
                    if abs(req_fee - amount) < 0.01:
                        unpaid_matching.append((sid, req_fee))

            if len(unpaid_matching) == 1:
                matched_session_id = unpaid_matching[0][0]
                expected_amount = unpaid_matching[0][1]
                print(f"[CBE IMAP] Matched via single pending pricing amount match -> Session: {matched_session_id}")

        if not matched_session_id:
            print(f"[CBE IMAP] Txn '{txn_ref}' ({amount} ETB) parsed from email, but no pending session matched yet. Storing in Supabase registry.")
            # Record in Supabase as pre-verified so when the user submits their Txn ID later, it verifies immediately
            if client:
                try:
                    client.table("transactions").upsert({
                        "session_id": "pre_verified",
                        "amount_expected": amount,
                        "amount_paid": amount,
                        "transaction_ref": txn_ref,
                        "status": "approved",
                        "payer_name": payer_name,
                        "raw_webhook_payload": raw_email
                    }, on_conflict="transaction_ref").execute()
                except Exception as e:
                    print(f"[CBE IMAP Supabase Record] Notice: {e}")
            return False

        if amount < expected_amount:
            print(f"[CBE IMAP] ❌ Underpayment for session {matched_session_id}: Expected {expected_amount} ETB, got {amount} ETB")
            return False

        # Mark paid & generate 24h Supabase Signed URL
        updated_session = storage_service.mark_session_paid(matched_session_id, txn_ref)
        download_url = updated_session.get("download_url")

        if client:
            try:
                client.table("transactions").update({
                    "amount_paid": amount,
                    "status": "approved",
                    "download_url": download_url,
                    "payer_name": payer_name,
                    "verified_at": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    "raw_webhook_payload": raw_email
                }).eq("session_id", matched_session_id).execute()
            except Exception as e:
                print(f"[CBE IMAP Supabase Update] Notice: {e}")

        print(f"[CBE IMAP] ✅ SUCCESS! Formatted thesis unlocked for session {matched_session_id} (Txn: {txn_ref}, Download: {download_url})")
        return True

    async def start_background_loop(self, poll_interval: int = 20):
        """
        Asynchronous periodic background worker loop for FastAPI lifespan.
        """
        if self._is_running:
            return

        self._is_running = True
        status_info = self.get_status_info()
        print(f"[CBE IMAP Background Worker] Initialized (Configured: {status_info['configured']}, Server: {status_info['server']}:{status_info['port']}, User: {status_info['user']}, Interval: {poll_interval}s)")

        while self._is_running:
            try:
                if self.is_configured():
                    # Run synchronous imap check in thread pool so it doesn't block async event loop
                    await asyncio.to_thread(self.check_gmail_receipts)
                else:
                    now = time.time()
                    if now - self._last_log_time > 120:
                        print(f"[CBE IMAP Background Worker] Idle: Gmail IMAP not configured. Waiting for GMAIL_IMAP_USER/GMAIL_IMAP_PASSWORD or Webhooks.")
                        self._last_log_time = now
            except Exception as e:
                print(f"[CBE IMAP Background Loop Error] {e}")

            await asyncio.sleep(poll_interval)

    def stop_background_loop(self):
        self._is_running = False
        print("[CBE IMAP Background Worker] Stopped.")

cbe_imap_service = CBEImapService()
