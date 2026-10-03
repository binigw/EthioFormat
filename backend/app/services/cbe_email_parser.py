import re
from typing import Optional, Tuple, Dict, Any

class CBEEmailParserService:
    """
    High-accuracy Regular Expression Parser for Commercial Bank of Ethiopia (CBE)
    Email Notifications, CBE Birr SMS alerts, and Core Banking Confirmation Receipts.
    """

    # 1. Patterns for CBE Transaction Reference / FT Number
    # Examples:
    # "Transaction ID: FT2409873ABCD"
    # "Txn Ref: FT2609384729"
    # "Ref No: TXN8374928"
    # "FT2409873ABCD"
    TXN_PATTERNS = [
        re.compile(r'\b(FT[0-9]{6,18}[A-Za-z0-9]*)\b', re.IGNORECASE),
        re.compile(r'\b(TXN[0-9A-Za-z]{6,20})\b', re.IGNORECASE),
        re.compile(r'\b(CBE[0-9A-Za-z]{6,20})\b', re.IGNORECASE),
        re.compile(r'(?:Transaction\s*(?:ID|Ref|Reference|Number|No\.?)|Txn\s*ID|Ref\s*No\.?|Reference\s*No\.?|FT\s*No\.?|CBEBirr\s*Ref\.?)\s*[:=\-]\s*([A-Za-z0-9_-]{5,32})', re.IGNORECASE),
        re.compile(r'(?:transfer(?:red)?\s+with\s+(?:reference|id|ref))\s*[:=\-]?\s*([A-Za-z0-9_-]{5,32})', re.IGNORECASE),
    ]

    # 2. Patterns for Payment Amount in ETB / Birr
    # Examples:
    # "Amount: ETB 50.00"
    # "Credited with 65.50 ETB"
    # "Transfer of Birr 80.00"
    # "Amount: 146.00 ETB"
    # "የተላከው መጠን: 50.00 ብር"
    AMOUNT_PATTERNS = [
        re.compile(r'(?:Amount|Total\s*Amount|Credited|Transferred|Paid|መጠን)\s*[:=\-]?\s*(?:ETB|Birr|USD|ብር)?\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)\s*(?:ETB|Birr|ብር)?', re.IGNORECASE),
        re.compile(r'(?:ETB|Birr|ብር)\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)', re.IGNORECASE),
        re.compile(r'([0-9]{1,6}(?:\.[0-9]{1,2})?)\s*(?:ETB|Birr|ብር)', re.IGNORECASE),
        re.compile(r'(?:credited\s+with|deposited)\s*([0-9]{1,6}(?:\.[0-9]{1,2})?)', re.IGNORECASE),
    ]

    IGNORED_WORDS = {
        "NOTIFICATION", "CONFIRMATION", "TRANSACTION", "SUCCESS",
        "FAILED", "PENDING", "DEPOSIT", "CREDIT", "PAYMENT", "ACCOUNT"
    }

    @classmethod
    def parse_email_content(cls, raw_text: str, subject: Optional[str] = None) -> Tuple[Optional[str], Optional[float]]:
        """
        Extracts (transaction_ref, amount) from incoming email payload text and subject line.
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
                    if 1.0 <= val <= 100000.0:  # Sensible range for thesis pricing
                        extracted_amount = val
                        break
                except (ValueError, TypeError):
                    continue
            if extracted_amount is not None:
                break

        return extracted_txn, extracted_amount

cbe_email_parser = CBEEmailParserService()
