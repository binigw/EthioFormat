import os
import uuid
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_preview_and_cbe_flow():
    # 1. Test cbe details
    res = client.get("/api/cbe-details")
    assert res.status_code == 200
    assert "cbe_account_number" in res.json()

    # 2. Upload docx for preview
    sample_path = "sample_ethiopian_thesis.docx"
    if not os.path.exists(sample_path):
        sample_path = "backend/sample_ethiopian_thesis.docx"

    with open(sample_path, "rb") as f:
        upload_res = client.post(
            "/api/preview",
            files={"file": ("sample.docx", f, "application/vnd.openxmlformats-officedocument.wordprocessingml.document")},
            data={"preset_id": "aau"}
        )
    assert upload_res.status_code == 200
    preview_data = upload_res.json()
    assert "session_id" in preview_data
    assert "cbe_account_number" in preview_data
    assert len(preview_data["preview_pages"]) > 0

    session_id = preview_data["session_id"]

    # 3. Initiate payment
    init_res = client.post("/api/initiate-cbe-payment", json={"session_id": session_id})
    assert init_res.status_code == 200
    assert init_res.json()["session_id"] == session_id

    # 4. Submit unique transaction ID
    txn_id = f"FT26{uuid.uuid4().hex[:8].upper()}"
    submit_res = client.post("/api/submit-cbe-transaction", json={
        "session_id": session_id,
        "transaction_ref": txn_id,
        "payer_name": "Abebe Bikila"
    })
    assert submit_res.status_code == 200

    # 5. Simulate inbound email receipt webhook
    webhook_res = client.post("/api/cbe-email-webhook", json={
        "subject": "CBE Transaction Alert",
        "sender": "no-reply@cbe.com.et",
        "body": f"Credit Notification: ETB {preview_data['pricing']['total_fee']} credited to 1000659424936. Ref: {txn_id} from Abebe Bikila"
    })
    assert webhook_res.status_code == 200
    assert webhook_res.json()["status"] == "success"
    assert webhook_res.json()["matched_session_id"] == session_id

    # 6. Check transaction status
    status_res = client.get(f"/api/cbe-transaction-status/{session_id}")
    assert status_res.status_code == 200
    assert status_res.json()["status"] == "approved"
    assert status_res.json()["verified"] is True
    assert status_res.json()["download_url"] is not None
