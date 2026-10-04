import re
import html
import unicodedata
from typing import Optional, Dict, Any, List

# List of invisible, bidirectional, and zero-width Unicode characters commonly found in email clients & SMS
INVISIBLE_UNICODE_CHARS = {
    '\u200e': '',   # Left-to-Right Mark (LRM) - causes 'ascii' codec crashes
    '\u200f': '',   # Right-to-Left Mark (RLM)
    '\u200b': '',   # Zero-Width Space (ZWSP)
    '\u200c': '',   # Zero-Width Non-Joiner (ZWNJ)
    '\u200d': '',   # Zero-Width Joiner (ZWJ)
    '\u2060': '',   # Word Joiner
    '\ufeff': '',   # Zero-Width No-Break Space (BOM)
    '\u00a0': ' ',  # Non-Breaking Space -> standard space
    '\u202a': '',   # Left-to-Right Embedding
    '\u202b': '',   # Right-to-Left Embedding
    '\u202c': '',   # Pop Directional Formatting
    '\u202d': '',   # Left-to-Right Override
    '\u202e': '',   # Right-to-Left Override
    '\u2008': ' ',  # Punctuation space
    '\u2009': ' ',  # Thin space
    '\u200a': ' ',  # Hair space
    '\u202f': ' ',  # Narrow no-break space
    '\u3000': ' ',  # Ideographic space
}

class CBEEmailParserService:
    """
    High-accuracy Multi-Format Regular Expression & NLP Parser for:
    - Commercial Bank of Ethiopia (CBE) Mobile Banking SMS & Email Notifications
    - CBE Birr / Core Banking Receipts
    - COOPay-EBIRR / EBIRR Transfer SMS & Receipts
    - Telebirr & Academic payment confirmations
    """

    # 1. Patterns for Transaction Reference / FT Number / CBEBirr & COOPay Transfer IDs
    TXN_PATTERNS = [
        # Explicit FT Numbers (Standard CBE Mobile Banking / Core Banking FT number)
        re.compile(r'\b(FT[0-9]{6,20}[A-Za-z0-9]*)\b', re.IGNORECASE),
        # Explicit TXN / CBEBirr / TT / EBIRR Transaction Codes
        re.compile(r'\b(TXN[0-9A-Za-z]{6,24})\b', re.IGNORECASE),
        re.compile(r'\b(CBE[0-9A-Za-z]{6,24})\b', re.IGNORECASE),
        re.compile(r'\b(TT[0-9A-Za-z]{6,24})\b', re.IGNORECASE),
        # Explicit "Transfer ID: ..." / "Transaction ID: ..." / "Txn ID: ..." / "Ref: ..."
        re.compile(
            r'\b(?:Transfer\s*ID|Txn\s*ID|Transaction\s*ID|Ref(?:erence)?(?:\s*No\.?|\s*Number|\s*ID)?|Receipt\s*No\.?|FT\s*No\.?|TT\s*No\.?|Code|የግብይት\s*ቁጥር|የማጣቀሻ\s*ቁጥር|የትራንዛክሽን\s*ቁጥር|መለያ\s*ቁጥር)\s*[:=\-]?\s*([A-Za-z0-9_-]{5,32})\b',
            re.IGNORECASE
        ),
        # Sentence structures: "transfer with reference ...", "deposited with ref ...", "transferred with ID ..."
        re.compile(
            r'(?:transfer(?:red)?|deposit(?:ed)?|credit(?:ed)?|paid)\s+(?:with\s+)?(?:reference|ref|id|txn|code)\s*[:=\-]?\s*([A-Za-z0-9_-]{5,32})',
            re.IGNORECASE
        ),
        # COOPay-EBIRR & EBIRR Transfer SMS (e.g., "[-EBIRR-COOPay-] ... Transfer ID: 2799024023")
        re.compile(
            r'(?:COOPay[-_ ]?EBIRR|EBIRR[-_ ]?COOPay|COOPay|EBIRR|E[-_]BIRR)\s+(?:Transfer|Txn|Ref|Payment)?\s*(?:ID|No\.?|Ref)?\s*[:=\-]?\s*([A-Za-z0-9_-]{5,32})',
            re.IGNORECASE
        ),
        # CBEBirr / Telebirr 8-18 numeric transaction IDs following keyword or starting with 2
        re.compile(r'(?:CBEBirr\s*(?:Txn|Ref|ID|Transaction)|Birr\s*Ref)\s*[:=\-]?\s*([0-9]{8,18})', re.IGNORECASE),
        # Standalone 10-digit numeric transaction IDs (e.g. 2799024023, 2798853639)
        re.compile(r'\b(2[0-9]{9,15})\b', re.IGNORECASE),
        # General 9-16 digit transaction references (excluding account numbers)
        re.compile(r'\b([0-9]{9,16})\b', re.IGNORECASE)
    ]

    # 2. Patterns for Payment Amount in ETB / Birr
    AMOUNT_PATTERNS = [
        # Labelled Amount: "Amount: ETB 63.50" / "መጠን: 63.50 ብር"
        re.compile(
            r'(?:Amount|Total\s*Amount|Credited|Transferred|Paid|Deposited|መጠን|የተከፈለው)\s*[:=\-]?\s*(?:ETB|Birr|USD|ብር)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)\s*(?:ETB|Birr|ብር)?',
            re.IGNORECASE
        ),
        # Currency prefix: "ETB 63.50" or "Birr 50" or "ብር 63.50"
        re.compile(r'(?:ETB|Birr|ብር)\s*[:=\-]?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)', re.IGNORECASE),
        # Currency suffix: "63.50 ETB" or "50.00 Birr" or "63.50 ብር"
        re.compile(r'([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)\s*(?:ETB|Birr|ብር)', re.IGNORECASE),
        # Verb with amount: "credited with 63.50", "credited with ETB 63.50", "deposited 50.00"
        re.compile(r'(?:credited\s+with|deposited|received|paid|transferred)\s+(?:ETB|Birr|ብር)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)', re.IGNORECASE),
        # Account credited notice: "your Account ... has been credited with ETB 63.50"
        re.compile(r'(?:credited|deposited)\s+(?:with\s+)?(?:ETB|Birr|ብር)?\s*([0-9]{1,3}(?:,[0-9]{3})*(?:\.[0-9]{1,2})?|[0-9]+(?:\.[0-9]{1,2})?)', re.IGNORECASE),
    ]

    # 3. Patterns for Payer / Sender Name
    PAYER_NAME_PATTERNS = [
        re.compile(
            r'(?:Payer(?:\s*Name)?|From|Sender|Debited\s*From|received\s+(?:[0-9,.]+\s*(?:ETB|Birr)?\s+)?from)\s*[:=\-]?\s*([A-Za-z\s]{2,35}?)(?=$|\r|\n|\.|\,|(?:Payer|Account|Date|with|on|to|\())',
            re.IGNORECASE
        ),
        re.compile(r'(?:የከፋዩ\s*ስም|ከ)\s*[:=\-]?\s*([^\r\n,.]+)', re.IGNORECASE)
    ]

    # 4. Patterns for Account Number
    ACCOUNT_PATTERNS = [
        re.compile(r'(?:Account|Acc(?:\.?|ount)|Acc\s*No\.?|A\/C|የሂሳብ\s*ቁጥር)\s*[:=\-]?\s*([0-9]{10,16}|\*+[0-9]{4}|1\*+[0-9]{4})', re.IGNORECASE),
    ]

    # 5. Patterns for Date & Time
    DATE_PATTERNS = [
        re.compile(r'(?:Date\s*(?:&|and)?\s*Time|Date|Time|ቀን|on)\s*[:=\-]?\s*([0-9]{2,4}[-/][0-9]{2}[-/][0-9]{2,4}(?:\s+[0-9]{2}:[0-9]{2}(?::[0-9]{2})?)?)', re.IGNORECASE),
    ]

    IGNORED_WORDS = {
        "NOTIFICATION", "CONFIRMATION", "TRANSACTION", "SUCCESS",
        "FAILED", "PENDING", "DEPOSIT", "CREDIT", "PAYMENT", "ACCOUNT",
        "ETHIOFORMAT", "BANKING", "COMMERCIAL", "ETHIOPIA", "CUSTOMER",
        "COOPAY", "EBIRR", "COOPAYEBIRR", "TRANSFER", "TELEBIRR",
        "BIRR", "ETB", "DEBIT", "TRANSFERID", "TXNID", "1000659424936",
        "OROMIA", "SAVING", "CURRENT", "MOBILE"
    }

    @classmethod
    def clean_raw_content(cls, raw_html_or_text: str) -> str:
        """
        Safely strips invisible Unicode marks (\u200e, \u200f, \ufeff, etc.),
        HTML tags, decodes HTML entities (&nbsp;, &amp;), and normalizes whitespace
        while fully preserving Amharic and Latin characters.
        """
        if not raw_html_or_text:
            return ""

        # 1. Strip invisible / directional Unicode characters
        text = str(raw_html_or_text)
        for char, replacement in INVISIBLE_UNICODE_CHARS.items():
            if char in text:
                text = text.replace(char, replacement)

        # 2. Decode HTML entities (&nbsp;, &amp;, etc.)
        try:
            text = html.unescape(text)
        except Exception:
            pass

        # 3. Strip HTML tags (<...>)
        text = re.sub(r'<[^>]+>', ' ', text)

        # 4. Normalize Unicode compatibility characters (NFKC)
        try:
            text = unicodedata.normalize('NFKC', text)
        except Exception:
            pass

        # 5. Clean up redundant spaces and line breaks
        lines = [re.sub(r'[ \t]+', ' ', line).strip() for line in text.splitlines()]
        return "\n".join(line for line in lines if line)

    @classmethod
    def parse_full_cbe_payload(cls, raw_text: str, subject: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses all key fields from email payload:
        - Transaction Reference / ID (FT number, TXN ref, CBEBirr & COOPay numeric ID)
        - Payment Amount (ETB)
        - Payer Name
        - Account Number
        - Date & Time
        """
        clean_subj = cls.clean_raw_content(subject or "")
        clean_body = cls.clean_raw_content(raw_text or "")
        combined_text = f"{clean_subj}\n{clean_body}"

        # 1. Extract Transaction ID
        extracted_txn: Optional[str] = None
        all_txns: List[str] = []
        for pattern in cls.TXN_PATTERNS:
            for match in pattern.finditer(combined_text):
                candidate = match.group(1).strip()
                clean_candidate = re.sub(r'[^A-Za-z0-9_-]', '', candidate)
                if len(clean_candidate) >= 5 and clean_candidate.upper() not in cls.IGNORED_WORDS:
                    val_upper = clean_candidate.upper()
                    if val_upper not in all_txns:
                        all_txns.append(val_upper)
                    if not extracted_txn:
                        extracted_txn = val_upper

        # 2. Extract Amount
        extracted_amount: Optional[float] = None
        for pattern in cls.AMOUNT_PATTERNS:
            for match in pattern.finditer(combined_text):
                try:
                    val_str = match.group(1).replace(",", "").strip()
                    val = float(val_str)
                    if 1.0 <= val <= 100000.0:
                        extracted_amount = round(val, 2)
                        break
                except (ValueError, TypeError):
                    continue
            if extracted_amount is not None:
                break

        # 3. Extract Payer Name
        extracted_payer: Optional[str] = None
        for pattern in cls.PAYER_NAME_PATTERNS:
            match = pattern.search(combined_text)
            if match:
                candidate = match.group(1).strip()
                if len(candidate) >= 3 and candidate.upper() not in cls.IGNORED_WORDS:
                    extracted_payer = candidate.strip()
                    break

        # 4. Extract Account Number
        extracted_acc: Optional[str] = None
        for pattern in cls.ACCOUNT_PATTERNS:
            match = pattern.search(combined_text)
            if match:
                extracted_acc = match.group(1).strip()
                break

        # 5. Extract Date & Time
        extracted_date: Optional[str] = None
        for pattern in cls.DATE_PATTERNS:
            match = pattern.search(combined_text)
            if match:
                extracted_date = match.group(1).strip()
                break

        return {
            "transaction_ref": extracted_txn,
            "all_transaction_refs": all_txns,
            "amount": extracted_amount,
            "payer_name": extracted_payer,
            "account_number": extracted_acc,
            "date_time": extracted_date,
            "currency": "ETB",
            "raw_snippet": combined_text[:300]
        }

cbe_email_parser = CBEEmailParserService()
