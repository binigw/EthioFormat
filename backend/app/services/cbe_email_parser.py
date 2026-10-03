import re
from typing import Optional, Tuple, Dict, Any

class CBEEmailParserService:
    """
    High-accuracy Regular Expression & Natural Language Parser for Commercial Bank of Ethiopia (CBE)
    Email Notifications, CBE Birr Mailhooks, and Core Banking Confirmation Receipts.
    """

    # 1. Patterns for CBE Transaction Reference / FT Number
    TXN_PATTERNS = [
        re.compile(r'\b(FT[0-9]{6,18}[A-Za-z0-9]*)\b', re.IGNORECASE),
        re.compile(r'\b(TXN[0-9A-Za-z]{6,20})\b', re.IGNORECASE),
        re.compile(r'\b(CBE[0-9A-Za-z]{6,20})\b', re.IGNORECASE),
        re.compile(r'(?:Transaction\s*(?:ID|Ref|Reference|Number|No\.?)|Txn\s*ID|Ref\s*No\.?|Reference\s*No\.?|FT\s*No\.?|CBEBirr\s*Ref\.?)\s*[:=\-]\s*([A-Za-z0-9_-]{5,32})', re.IGNORECASE),
        re.compile(r'(?:transfer(?:red)?\s+with\s+(?:reference|id|ref))\s*[:=\-]?\s*([A-Za-z0-9_-]{5,32})', re.IGNORECASE),
    ]

    # 2. Patterns for Payment Amount in ETB / Birr
    AMOUNT_PATTERNS = [
        re.compile(r'(?:Amount|Total\s*Amount|Credited|Transferred|Paid|መጠን)\s*[:=\-]?\s*(?:ETB|Birr|USD|ብር)?\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)\s*(?:ETB|Birr|ብር)?', re.IGNORECASE),
        re.compile(r'(?:ETB|Birr|ብር)\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)', re.IGNORECASE),
        re.compile(r'([0-9]{1,6}(?:\.[0-9]{1,2})?)\s*(?:ETB|Birr|ብር)', re.IGNORECASE),
        re.compile(r'(?:credited\s+with|deposited)\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)', re.IGNORECASE),
    ]

    # 3. Patterns for Payer Name
    PAYER_NAME_PATTERNS = [
        re.compile(r'(?:Payer(?:\s*Name)?|From|Sender|Debited\s*From|received\s+(?:[0-9.]+\s*ETB\s+)?from)\s*[:=\-]?\s*([A-Za-z\s]{2,30}?)(?=$|\r|\n|\.|\,|(?:Payer|Account|Date|with|on|\())', re.IGNORECASE),
        re.compile(r'(?:የከፋዩ\s*ስም|ከ)\s*[:=\-]?\s*([^\r\n,.]+)', re.IGNORECASE)
    ]

    # 4. Patterns for Account Number
    ACCOUNT_PATTERNS = [
        re.compile(r'(?:Account|Acc(?:\.?|ount)|Acc\s*No\.?|A\/C|የሂሳብ\s*ቁጥር)\s*[:=\-]?\s*([0-9]{10,16}|\*+[0-9]{4})', re.IGNORECASE),
    ]

    # 5. Patterns for Date & Time
    DATE_PATTERNS = [
        re.compile(r'(?:Date\s*(?:&|and)?\s*Time|Date|Time|ቀን|on)\s*[:=\-]?\s*([0-9]{2,4}[-/][0-9]{2}[-/][0-9]{2,4}(?:\s+[0-9]{2}:[0-9]{2}(?::[0-9]{2})?)?)', re.IGNORECASE),
    ]

    IGNORED_WORDS = {
        "NOTIFICATION", "CONFIRMATION", "TRANSACTION", "SUCCESS",
        "FAILED", "PENDING", "DEPOSIT", "CREDIT", "PAYMENT", "ACCOUNT"
    }

    @classmethod
    def parse_full_cbe_payload(cls, raw_text: str, subject: Optional[str] = None) -> Dict[str, Any]:
        """
        Parses all key fields from email payload:
        - Transaction Reference / ID
        - Payment Amount (ETB)
        - Payer Name
        - Account Number
        - Date & Time
        """
        combined_text = f"{subject or ''}\n{raw_text or ''}"

        # 1. Extract Transaction ID
        extracted_txn: Optional[str] = None
        for pattern in cls.TXN_PATTERNS:
            for match in pattern.finditer(combined_text):
                candidate = match.group(1).strip()
                if len(candidate) >= 5 and candidate.upper() not in cls.IGNORED_WORDS:
                    extracted_txn = candidate
                    break
            if extracted_txn:
                break

        # 2. Extract Amount
        extracted_amount: Optional[float] = None
        for pattern in cls.AMOUNT_PATTERNS:
            for match in pattern.finditer(combined_text):
                try:
                    val_str = match.group(1).replace(",", "").strip()
                    val = float(val_str)
                    if 1.0 <= val <= 100000.0:
                        extracted_amount = val
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
                    extracted_payer = candidate
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
            "amount": extracted_amount,
            "payer_name": extracted_payer,
            "account_number": extracted_acc,
            "date_time": extracted_date,
            "currency": "ETB"
        }

cbe_email_parser = CBEEmailParserService()
