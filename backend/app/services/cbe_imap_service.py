import sys
import io
import os
import imaplib
import email
import email.policy
from email.header import decode_header
import asyncio
import time
import re
import datetime
from typing import List, Dict, Any, Optional
from app.config import settings
from app.services.cbe_email_parser import cbe_email_parser
from app.services.storage_service import storage_service

def safe_print(msg: Any):
    """
    Safely prints messages to stdout without crashing on ascii-only terminal streams or hidden unicode characters.
    """
    try:
        s = cbe_email_parser.clean_raw_content(str(msg))
        sys.stdout.write(s + "\n")
        sys.stdout.flush()
    except UnicodeEncodeError:
        try:
            s_clean = str(msg).encode('ascii', errors='replace').decode('ascii')
            sys.stdout.write(s_clean + "\n")
            sys.stdout.flush()
        except Exception:
            pass
    except Exception:
        pass

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

    def _decode_header_safely(self, raw_header_val: Any) -> str:
        """
        Robust email header decoder that guarantees safe string conversion
        without failing on raw 8-bit bytes or invisible directional Unicode characters.
        """
        if not raw_header_val:
            return ""

        try:
            if isinstance(raw_header_val, str):
                cleaned = cbe_email_parser.clean_raw_content(raw_header_val)
                if "=?" in raw_header_val:
                    try:
                        fragments = decode_header(raw_header_val)
                        out = []
                        for frag, enc in fragments:
                            if isinstance(frag, bytes):
                                charset = enc or "utf-8"
                                try:
                                    out.append(frag.decode(charset, errors="ignore"))
                                except Exception:
                                    out.append(frag.decode("utf-8", errors="ignore"))
                            else:
                                out.append(str(frag))
                        return cbe_email_parser.clean_raw_content("".join(out))
                    except Exception:
                        return cleaned
                return cleaned

            if isinstance(raw_header_val, bytes):
                return cbe_email_parser.clean_raw_content(
                    raw_header_val.decode("utf-8", errors="ignore")
                )

            return cbe_email_parser.clean_raw_content(str(raw_header_val))

        except Exception as e:
            return cbe_email_parser.clean_raw_content(str(raw_header_val))

    def _extract_body_safely(self, msg: Any) -> str:
        """
        Extracts plain text / HTML body parts with multi-encoding fallback and Unicode sanitization.
        """
        body_parts = []

        try:
            if hasattr(msg, "get_body"):
                try:
                    plain_body = msg.get_body(preferencelist=('plain', 'html'))
                    if plain_body:
                        content = plain_body.get_content()
                        if content:
                            return cbe_email_parser.clean_raw_content(str(content))
                except Exception:
                    pass

            def _decode_bytes(b_data: bytes, enc: Optional[str]) -> str:
                if not b_data:
                    return ""
                for charset in [enc, "utf-8", "latin1", "windows-1252", "iso-8859-1"]:
                    if not charset:
                        continue
                    try:
                        return b_data.decode(charset, errors="replace")
                    except Exception:
                        continue
                return b_data.decode("utf-8", errors="ignore")

            if hasattr(msg, "is_multipart") and msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition", ""))
                    if "attachment" not in content_disposition:
                        if content_type in ["text/plain", "text/html"]:
                            payload = part.get_payload(decode=True)
                            if isinstance(payload, bytes):
                                charset = part.get_content_charset()
                                text = _decode_bytes(payload, charset)
                                body_parts.append(text)
                            elif isinstance(payload, str):
                                body_parts.append(payload)
            else:
                payload = msg.get_payload(decode=True) if hasattr(msg, "get_payload") else str(msg)
                if isinstance(payload, bytes):
                    charset = msg.get_content_charset() if hasattr(msg, "get_content_charset") else None
                    text = _decode_bytes(payload, charset)
                    body_parts.append(text)
                elif isinstance(payload, str):
                    body_parts.append(payload)

        except Exception as ex:
            body_parts.append(str(ex))

        return cbe_email_parser.clean_raw_content("\n".join(body_parts))

    def check_gmail_receipts(self, target_txn_ref: Optional[str] = None) -> List[Dict[str, Any]]:
        """
        Synchronous single-pass IMAP check with targeted Txn ID search.
        Connects to Gmail, scans targeted, UNSEEN, and recent emails, parses CBE alerts,
        and updates Supabase, disk metadata, and pre-verified registry.
        """
        if not self.is_configured():
            now = time.time()
            if now - self._last_log_time > 60:
                safe_print(
                    "[CBE IMAP] ⚠️ IMAP Not Configured: GMAIL_IMAP_USER or GMAIL_IMAP_PASSWORD environment variable is empty."
                )
                self._last_log_time = now
            return []

        verified_transactions = []
        mail = None

        try:
            # 1. Connect and login via SSL
            mail = imaplib.IMAP4_SSL(self.server, self.port, timeout=15)
            mail.login(self.user, self.password)
            mail.select("INBOX")

            email_ids_to_check = set()
            clean_target = re.sub(r'[^A-Z0-9]', '', target_txn_ref.upper()) if target_txn_ref else None

            # 2. Targeted search if user provided a transaction ID
            if clean_target and len(clean_target) >= 4:
                safe_print(f"[CBE IMAP] Performing targeted IMAP search for Txn ID: '{clean_target}'...")
                for query in [f'TEXT "{clean_target}"', f'BODY "{clean_target}"', f'SUBJECT "{clean_target}"']:
                    try:
                        status_t, resp_t = mail.search(None, query)
                        if status_t == "OK" and resp_t and resp_t[0]:
                            for eid in resp_t[0].split():
                                email_ids_to_check.add(eid)
                    except Exception:
                        pass

            # 3. Search UNSEEN
            try:
                status_unseen, resp_unseen = mail.search(None, "UNSEEN")
                if status_unseen == "OK" and resp_unseen and resp_unseen[0]:
                    for eid in resp_unseen[0].split():
                        email_ids_to_check.add(eid)
            except Exception as e_search:
                safe_print(f"[CBE IMAP] Notice in search UNSEEN: {e_search}")

            # 4. Search ALL to capture last 50 recent messages
            try:
                status_all, resp_all = mail.search(None, "ALL")
                if status_all == "OK" and resp_all and resp_all[0]:
                    all_ids = resp_all[0].split()
                    for eid in all_ids[-50:]:
                        email_ids_to_check.add(eid)
            except Exception as e_all:
                safe_print(f"[CBE IMAP] Notice in search ALL: {e_all}")

            if not email_ids_to_check:
                try:
                    mail.close()
                    mail.logout()
                except Exception:
                    pass
                return []

            # Sort IDs numerically descending (newest first)
            def _get_id_num(x):
                try:
                    s = x.decode("ascii") if isinstance(x, bytes) else str(x)
                    return int(s)
                except Exception:
                    return 0

            sorted_eids = sorted(list(email_ids_to_check), key=_get_id_num, reverse=True)
            safe_print(f"[CBE IMAP] Checking {len(sorted_eids)} email(s) in inbox (Target: {clean_target or 'All'})...")

            # Broad Ethiopian payment keywords
            cbe_keywords = [
                "cbe", "birr", "ebirr", "coopay", "transfer", "transferred", "txn", "ref", "ft",
                "credit", "credited", "etb", "biniam", "1000659424936", "4936", "bank", "sms",
                "alert", "deposited", "deposit", "payment", "receipt", "የግብይት", "ባንክ", "ብር", "መለያ", "ሒሳብ"
            ]

            for e_id in sorted_eids:
                try:
                    clean_eid = e_id if isinstance(e_id, bytes) else str(e_id).encode("ascii")
                    res_code, msg_data = mail.fetch(clean_eid, "(RFC822)")
                    if res_code != "OK" or not msg_data or not msg_data[0]:
                        continue

                    raw_email = msg_data[0][1]
                    if not isinstance(raw_email, bytes):
                        continue

                    try:
                        msg = email.message_from_bytes(raw_email, policy=email.policy.default)
                    except Exception:
                        msg = email.message_from_bytes(raw_email)

                    subject = self._decode_header_safely(msg.get("Subject", ""))
                    sender = self._decode_header_safely(msg.get("From", ""))
                    body = self._extract_body_safely(msg)

                    combined_check = f"{subject} {sender} {body}".lower()

                    # Check if matches target or payment keywords
                    is_targeted_match = clean_target and (clean_target.lower() in combined_check)
                    has_payment_keywords = any(kw in combined_check for kw in cbe_keywords)

                    if not is_targeted_match and not has_payment_keywords:
                        continue

                    eid_str = clean_eid.decode("ascii", errors="ignore")
                    safe_print(f"[CBE IMAP] Processing email #{eid_str}: Subject='{subject}' | From='{sender}'")

                    parsed = cbe_email_parser.parse_full_cbe_payload(raw_text=body, subject=subject)
                    txn_ref = parsed.get("transaction_ref")
                    amount = parsed.get("amount")
                    payer_name = parsed.get("payer_name")

                    # If targeted and regex missed it, try direct search
                    if not txn_ref and clean_target and clean_target.lower() in combined_check:
                        txn_ref = clean_target

                    safe_print(f"[CBE IMAP] Extracted -> Txn ID: '{txn_ref}', Amount: {amount} ETB, Payer: '{payer_name}'")

                    if txn_ref:
                        txn_ref_upper = txn_ref.strip().upper()
                        # Default amount to 50 if parser couldn't find explicit amount but found Txn ID
                        parsed_amount = amount if (amount and amount > 0) else 50.0

                        # Register in preverified storage regardless of matching
                        storage_service.register_preverified_transaction(
                            txn_ref=txn_ref_upper,
                            data={
                                "transaction_ref": txn_ref_upper,
                                "amount": parsed_amount,
                                "payer_name": payer_name,
                                "source": "gmail_imap",
                                "email_id": eid_str,
                                "subject": subject,
                                "from": sender
                            }
                        )

                        # Match with active pending session
                        approved = self._process_verified_txn(
                            txn_ref=txn_ref_upper,
                            amount=parsed_amount,
                            payer_name=payer_name,
                            raw_email={"subject": subject, "from": sender, "body": body[:500]}
                        )

                        if approved:
                            verified_transactions.append({
                                "transaction_ref": txn_ref_upper,
                                "amount": parsed_amount,
                                "status": "approved"
                            })
                            try:
                                mail.store(clean_eid, "+FLAGS", "\\Seen")
                            except Exception:
                                pass

                except Exception as ex:
                    safe_print(f"[CBE IMAP] Error processing email #{e_id}: {ex}")

            try:
                mail.close()
                mail.logout()
            except Exception:
                pass

        except Exception as e:
            safe_print(f"[CBE IMAP] Connection/Processing notice: {e}")
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
        safe_print(f"[CBE IMAP] Matching Txn '{txn_ref}' (Normalized: '{clean_ref}', Amount: {amount} ETB)...")

        client = storage_service.supabase_client
        matched_session_id: Optional[str] = None
        expected_amount: float = 50.0

        # 1. Check Supabase transactions table
        if client:
            try:
                query = client.table("transactions").select("*").ilike("transaction_ref", f"%{clean_ref}%").execute()
                if query.data and len(query.data) > 0:
                    matched_row = query.data[0]
                    matched_session_id = matched_row.get("session_id")
                    expected_amount = float(matched_row.get("amount_expected", 50.0))
                    safe_print(f"[CBE IMAP] Matched via Supabase transactions table -> Session: {matched_session_id}")
            except Exception as e:
                safe_print(f"[CBE IMAP Supabase Query] Notice: {e}")

        # 2. Check Disk & Memory Sessions for matching submitted Txn ID
        if not matched_session_id:
            matched_sid = storage_service.find_session_by_txn_ref(clean_ref)
            if matched_sid:
                matched_session_id = matched_sid
                sess = storage_service.get_session(matched_sid)
                pricing = sess.get("pricing", {}) if sess else {}
                expected_amount = float(pricing.get("total_fee", 50.0))
                safe_print(f"[CBE IMAP] Matched via Disk/Memory Session find_session_by_txn_ref -> Session: {matched_session_id}")

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
                safe_print(f"[CBE IMAP] Matched via single pending pricing amount match -> Session: {matched_session_id}")

        if not matched_session_id:
            safe_print(f"[CBE IMAP] Txn '{clean_ref}' ({amount} ETB) pre-verified and saved for future submission.")
            return False

        # Mark paid & generate 24h Supabase Signed URL
        updated_session = storage_service.mark_session_paid(matched_session_id, clean_ref)
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
                safe_print(f"[CBE IMAP Supabase Update] Notice: {e}")

        safe_print(f"[CBE IMAP] ✅ SUCCESS! Formatted thesis unlocked for session {matched_session_id} (Txn: {clean_ref}, Download: {download_url})")
        return True

    async def start_background_loop(self, poll_interval: int = 15):
        """
        Asynchronous periodic background worker loop for FastAPI lifespan.
        """
        if self._is_running:
            return

        self._is_running = True
        status_info = self.get_status_info()
        safe_print(f"[CBE IMAP Background Worker] Initialized (Configured: {status_info['configured']}, Server: {status_info['server']}:{status_info['port']}, User: {status_info['user']}, Interval: {poll_interval}s)")

        while self._is_running:
            try:
                if self.is_configured():
                    await asyncio.to_thread(self.check_gmail_receipts)
                else:
                    now = time.time()
                    if now - self._last_log_time > 120:
                        safe_print(f"[CBE IMAP Background Worker] Idle: Waiting for GMAIL_IMAP_USER/GMAIL_IMAP_PASSWORD or Webhooks.")
                        self._last_log_time = now
            except Exception as e:
                safe_print(f"[CBE IMAP Loop Exception] {e}")

            await asyncio.sleep(poll_interval)

cbe_imap_service = CBEImapService()
