import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.config import settings
from app.services.cbe_email_parser import CBEEmailParserService
from app.services.pricing_engine import PricingEngine
from app.services.storage_service import StorageService

client = TestClient(app)

def test_root_endpoint():
    # Test GET /
    res_get = client.get("/")
    assert res_get.status_code == 200
    data = res_get.json()
    assert data["status"] == "alive"

    # Test HEAD /
    res_head = client.head("/")
    assert res_head.status_code == 200

def test_cbe_details_endpoint():
    response = client.get("/api/cbe-details")
    assert response.status_code == 200
    data = response.json()
    assert "cbe_account_number" in data
    assert "cbe_account_name" in data
    assert data["cbe_account_number"] == settings.CBE_ACCOUNT_NUMBER
    assert data["cbe_account_name"] == settings.CBE_ACCOUNT_NAME

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

def test_cbe_email_parser():
    sample_text = """
    Dear Customer,
    Your account 1000123456789 has been credited with ETB 65.00 on 04/10/2026.
    Transaction ID: FT2609871234
    Sender: ABEBE BIKILA
    Thank you for banking with CBE.
    """
    receipt = CBEEmailParserService.parse_full_cbe_payload(sample_text)
    assert receipt["transaction_ref"] == "FT2609871234"
    assert receipt["amount"] == 65.00
    assert receipt["payer_name"] == "ABEBE BIKILA"

def test_storage_persistence():
    service = StorageService()
    session_id = "test_persistence_session_123"
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

    # Check from a fresh instance
    new_service = StorageService()
    sess = new_service.get_session(session_id)
    assert sess is not None
    assert sess["total_pages"] == 25
    assert sess["pricing"]["total_fee"] == 57.5
    assert sess["is_paid"] is False

    # Mark paid
    new_service.mark_session_paid(session_id, "FT2609871234")
    sess_paid = StorageService().get_session(session_id)
    assert sess_paid["is_paid"] is True
    assert sess_paid["tx_ref"] == "FT2609871234"
