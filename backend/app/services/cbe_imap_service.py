import imaplib
import email
from email.header import decode_header
import asyncio
import time
import datetime
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.cbe_email_parser import cbe_email_parser
from app.services.storage_service import storage_service

class CBEImapService:
    """
    Automated Gmail IMAP Reader Service for Commercial Bank of Ethiopia (CBE) Receipts.
    Connects to Gmail via imaplib over SSL, polls unread CBE transaction alert emails,
    extracts the Transaction ID and Amount via Regex, and verifies pending transactions.
    """

    def __init__(self):
        self.server = settings.GMAIL_IMAP_SERVER
        self.port = settings.GMAIL_IMAP_PORT
        self.user = settings.GMAIL_IMAP_USER
        self.password = settings.GMAIL_IMAP_PASSWORD
        self._is_running = False

    def is_configured(self) -> bool:
        return bool(self.user and self.password)

    def _decode_str(self, header_val: Any) -> str:
        if not header_val:
            return ""
        decoded_fragments = decode_header(header_val)
        out = []
        for frag, enc in decoded_fragments:
            if isinstance(frag, bytes):
                out.append(frag.decode(enc or "utf-8", errors="ignore"))
            else:
                out.append(str(frag))
        return "".join(out)

    def _extract_body(self, msg: email.message.Message) -> str:
        body_parts = []
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if "attachment" not in content_disposition:
                    if content_type in ["text/plain", "text/html"]:
                        payload = part.get_payload(decode=True)
                        if payload:
                            charset = part.get_content_charset() or "utf-8"
                            body_parts.append(payload.decode(charset, errors="ignore"))
        else:
            payload = msg.get_payload(decode=True)
            if payload:
                charset = msg.get_content_charset() or "utf-8"
                body_parts.append(payload.decode(charset, errors="ignore"))

        return "\n".join(body_parts)

    def check_gmail_receipts(self) -> List[Dict[str, Any]]:
        """
        Synchronous single-pass IMAP check.
        Connects to Gmail, scans unread emails, parses CBE alerts, and updates Supabase.
        """
        if not self.is_configured():
            return []

        verified_transactions = []
        mail = None

        try:
            # 1. Connect and login via SSL
            mail = imaplib.IMAP4_SSL(self.server, self.port, timeout=15)
            mail.login(self.user, self.password)
            mail.select("INBOX")

            # 2. Search unread emails
            status, response = mail.search(None, "UNSEEN")
            if status != "OK" or not response or not response[0]:
                mail.logout()
                return []

            email_ids = response[0].split()
            print(f"[CBE IMAP] Found {len(email_ids)} unread email(s) in inbox. Scanning...")

            for e_id in email_ids:
                try:
                    res_code, msg_data = mail.fetch(e_id, "(RFC822)")
                    if res_code != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_email = msg_data[0][1]
                    msg = email.message_from_bytes(raw_email)

                    subject = self._decode_str(msg.get("Subject", ""))
                    sender = self._decode_str(msg.get("From", ""))
                    body = self._extract_body(msg)

                    # Parse with regex parser
                    parsed = cbe_email_parser.parse_full_cbe_payload(raw_text=body, subject=subject)
                    txn_ref = parsed.get("transaction_ref")
                    amount = parsed.get("amount")

                    if txn_ref and amount and amount > 0:
                        txn_ref_upper = txn_ref.strip().upper()
                        print(f"[CBE IMAP] Detected CBE Transaction: {txn_ref_upper} with Amount {amount} ETB")

                        # Match with pending session in Supabase / memory
                        approved = self._process_verified_txn(
                            txn_ref=txn_ref_upper,
                            amount=amount,
                            payer_name=parsed.get("payer_name"),
                            raw_email={"subject": subject, "from": sender, "body": body[:500]}
                        )

                        if approved:
                            verified_transactions.append({
                                "transaction_ref": txn_ref_upper,
                                "amount": amount,
                                "status": "approved"
                            })
                            # Mark email as read in Gmail
                            mail.store(e_id, "+FLAGS", "\\Seen")

                except Exception as ex:
                    print(f"[CBE IMAP] Error processing email #{e_id}: {ex}")

            mail.close()
            mail.logout()

        except Exception as e:
            print(f"[CBE IMAP] Connection/Processing notice: {e}")
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
        Matches extracted transaction against Supabase / memory and unlocks download.
        """
        client = storage_service.supabase_client
        matched_session_id: Optional[str] = None
        expected_amount: float = 50.0

        if client:
            try:
                query = client.table("transactions").select("*").ilike("transaction_ref", txn_ref).execute()
                if query.data and len(query.data) > 0:
                    matched_row = query.data[0]
                    matched_session_id = matched_row.get("session_id")
                    expected_amount = float(matched_row.get("amount_expected", 50.0))
            except Exception as e:
                print(f"[CBE IMAP Supabase Query] Notice: {e}")

        # Fallback to storage sessions
        if not matched_session_id:
            for sid, sdata in storage_service._sessions.items():
                if not sdata.get("is_paid", False):
                    pricing = sdata.get("pricing", {})
                    req_fee = float(pricing.get("total_fee", 50.0))
                    if abs(req_fee - amount) < 0.01 or sdata.get("tx_ref") == txn_ref:
                        matched_session_id = sid
                        expected_amount = req_fee
                        break

        if not matched_session_id:
            print(f"[CBE IMAP] Txn {txn_ref} ({amount} ETB) received but no pending session matched yet.")
            return False

        if amount < expected_amount:
            print(f"[CBE IMAP] Underpayment for session {matched_session_id}: Expected {expected_amount}, got {amount}")
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

        print(f"[CBE IMAP] SUCCESS! Formatted thesis unlocked for session {matched_session_id} (Download: {download_url})")
        return True

    async def start_background_loop(self, poll_interval: int = 20):
        """
        Asynchronous periodic background worker loop for FastAPI lifespan.
        """
        if self._is_running:
            return

        self._is_running = True
        print(f"[CBE IMAP Background Worker] Started with interval {poll_interval}s...")

        while self._is_running:
            try:
                if self.is_configured():
                    # Run synchronous imap check in thread pool so it doesn't block async event loop
                    await asyncio.to_thread(self.check_gmail_receipts)
            except Exception as e:
                print(f"[CBE IMAP Background Error] {e}")

            await asyncio.sleep(poll_interval)

    def stop_background_loop(self):
        self._is_running = False

cbe_imap_service = CBEImapService()
