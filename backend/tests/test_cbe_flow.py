import pytest
import email
from fastapi.testclient import TestClient
from app.main import app
from app.services.pricing_engine import PricingEngine
from app.services.cbe_email_parser import CBEEmailParserService
from app.services.storage_service import StorageService
from app.services.cbe_imap_service import cbe_imap_service

client = TestClient(app)

def test_root_endpoint():
    res = client.get("/")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "alive"
    assert "EthioFormat" in data["app"]

    # HEAD request support for uptime monitors (UptimeRobot, Render, Netlify)
    res_head = client.head("/")
    assert res_head.status_code == 200

def test_cbe_details_endpoint():
    res = client.get("/api/cbe-details")
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "success"
    assert "cbe_account_number" in data
    assert "cbe_account_name" in data
    assert data["cbe_account_number"] == "1000659424936"
    assert data["cbe_account_name"] == "BINIAM KEBEDE AMADE"

    # Test route alias
    res_alias = client.get("/api/cbe-details")
    assert res_alias.status_code == 200

def test_pricing_calculation():
    # 20 pages base
    p20 = PricingEngine.calculate_pricing(20)
    assert p20.base_fee == 50.0
    assert p20.incremental_fee == 0.0
    assert p20.total_fee == 50.0

    # 30 pages
    p30 = PricingEngine.calculate_pricing(30)
    assert p30.base_fee == 50.0
    assert p30.incremental_fee == 15.0
    assert p30.total_fee == 65.0

def test_cbe_email_parser_standard():
    sample_text = """
    Dear Customer,
    Your account 1000659424936 has been credited with ETB 65.00 on 04/10/2026.
    Transaction ID: FT2609871234
    Sender: ABEBE BIKILA
    Thank you for banking with CBE.
    """
    receipt = CBEEmailParserService.parse_full_cbe_payload(sample_text)
    assert receipt["transaction_ref"] == "FT2609871234"
    assert receipt["amount"] == 65.00
    assert receipt["payer_name"] == "ABEBE BIKILA"

def test_cbe_email_parser_coopay_and_cbe_sms():
    # COOPay-EBIRR SMS from screenshot
    sms_coopay = "[-EBIRR-COOPay-] Transfer ID: 2799024023, You have successfully transferred ETB 63.50 to 1000659424936 BINIAM KEBEDE AMADE."
    res1 = CBEEmailParserService.parse_full_cbe_payload(sms_coopay)
    assert res1["transaction_ref"] == "2799024023"
    assert res1["amount"] == 63.50

    # CBE Core banking SMS from screenshot
    sms_cbe = "Dear Mr Biniam your Account 1********4936 has been credited with ETB 63.50 on 10/4/2026. Reason: Transfer ID 2799024023."
    res2 = CBEEmailParserService.parse_full_cbe_payload(sms_cbe)
    assert res2["transaction_ref"] == "2799024023"
    assert res2["amount"] == 63.50

def test_cbe_email_parser_hidden_unicode_and_ltr_marks():
    sample_text_with_hidden_unicode = (
        "\u200eDear\u200b Customer,\u00a0"
        "Your account 1000729362799 has been \u200ecredited with \ufeffETB 50.00 on 04/10/2026.\n"
        "Transaction ID:\u200e FT2699881122\u200e\n"
        "Sender: \u200eYOHANNES\u00a0WONDIMAGEGNEHU\u200e\n"
        "Thank you for banking with CBE."
    )
    receipt = CBEEmailParserService.parse_full_cbe_payload(sample_text_with_hidden_unicode)
    assert receipt["transaction_ref"] == "FT2699881122"
    assert receipt["amount"] == 50.00
    assert "YOHANNES" in receipt["payer_name"]

def test_safe_header_and_body_decoding():
    raw_email_bytes = (
        b"From: CBE <no-reply@cbe.com.et>\r\n"
        b"Subject: Credit Notification \xe2\x80\x8e FT2609871234\r\n\r\n"
        b"Dear Customer,\r\n\xe2\x80\x8eYou received ETB 50.00 from Abebe Bikila.\r\n"
        b"Transaction Ref: \xe2\x80\x8eFT2609871234\xe2\x80\x8e\r\n"
    )
    msg = email.message_from_bytes(raw_email_bytes)
    subj = cbe_imap_service._decode_header_safely(msg.get("Subject"))
    body = cbe_imap_service._extract_body_safely(msg)

    assert "\u200e" not in subj
    assert "FT2609871234" in subj
    assert "\u200e" not in body

    parsed = CBEEmailParserService.parse_full_cbe_payload(raw_text=body, subject=subj)
    assert parsed["transaction_ref"] == "FT2609871234"
    assert parsed["amount"] == 50.00

def test_cbe_email_parser_html_and_non_breaking_spaces():
    html_sample = """
    <div>
        <p>Dear Customer,</p>
        <p>You have received <b>ETB&nbsp;50.00</b> from <b>Almaz Ayana</b>.</p>
        <p>Txn Ref No.: <b>FT2627883921</b></p>
        <p>Date: 2026-10-04 14:20:00</p>
    </div>
    """
    receipt = CBEEmailParserService.parse_full_cbe_payload(html_sample)
    assert receipt["transaction_ref"] == "FT2627883921"
    assert receipt["amount"] == 50.00
    assert receipt["payer_name"] == "Almaz Ayana"

def test_cbe_email_parser_amharic():
    amharic_sample = """
    የከፋዩ ስም: በቀለ ቶሎሳ
    የግብይት ቁጥር: FT2600112233
    መጠን: 50.00 ብር
    ቀን: 04/10/2026
    """
    receipt = CBEEmailParserService.parse_full_cbe_payload(amharic_sample)
    assert receipt["transaction_ref"] == "FT2600112233"
    assert receipt["amount"] == 50.00
    assert receipt["payer_name"] == "በቀለ ቶሎሳ"

def test_storage_persistence_and_lookup():
    service = StorageService()
    session_id = "test_persistence_session_debug_999"
    service.register_session(
        session_id=session_id,
        data={
            "session_id": session_id,
            "formatted_docx_path": "test.docx",
            "original_filename": "test.docx",
            "total_pages": 25,
            "pricing": {"base_fee": 50.0, "incremental_fee": 7.5, "total_fee": 57.5, "currency": "ETB"},
            "university": "Addis Ababa University",
            "is_paid": False
        }
    )

    # Attach transaction reference
    service.update_session_transaction(session_id, "FT2699887766", "Derartu Tulu")

    # Lookup from fresh service instance
    new_service = StorageService()
    matched_id = new_service.find_session_by_txn_ref("ft-2699887766")
    assert matched_id == session_id

    # Mark paid
    new_service.mark_session_paid(session_id, "FT2699887766")
    sess_paid = StorageService().get_session(session_id)
    assert sess_paid["is_paid"] is True
    assert sess_paid["tx_ref"] == "FT2699887766"

def test_preverified_transaction_flow():
    service = StorageService()
    txn_ref = "2798853639"
    service.register_preverified_transaction(
        txn_ref=txn_ref,
        data={
            "transaction_ref": txn_ref,
            "amount": 63.50,
            "payer_name": "BINIAM KEBEDE AMADE",
            "source": "gmail_imap"
        }
    )

    # Check retrieval
    res = service.get_preverified_transaction("2798853639")
    assert res is not None
    assert res["amount"] == 63.50
    assert res["transaction_ref"] == txn_ref
