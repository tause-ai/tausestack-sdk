import os
import pytest
from unittest.mock import patch
# Forma recomendada de ejecución:
# cd /Users/tause/Documents/proyectos/tausestack/templates/website/backend/app
# pytest -v payments/test_wompi_service.py
try:
    from payments.wompi_service import WompiService  # Import absoluto para pytest desde app/
except ImportError:
    from wompi_service import WompiService  # Import relativo para pytest desde payments/


# Usa llaves de sandbox para pruebas
PUBLIC_KEY = os.getenv("WOMPI_PUBLIC_KEY", "pub_test_xxx")
PRIVATE_KEY = os.getenv("WOMPI_PRIVATE_KEY", "prv_test_xxx")

@pytest.fixture
def wompi():
    return WompiService(PUBLIC_KEY, PRIVATE_KEY, environment="sandbox")

def test_create_transaction_card_success(wompi):
    payload = {
        "amount_in_cents": 10000,
        "currency": "COP",
        "customer_email": "test@example.com",
        "payment_method": {"type": "CARD", "token": "tok_test_visa_123456"},
        "reference": "pedido-qa-001"
    }
    with patch("payments.wompi_service.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"id": "txn_123", "status": "APPROVED"}
        resp = wompi.create_transaction(payload)
        assert resp["status"] == "APPROVED"
        assert resp["id"] == "txn_123"

def test_create_transaction_missing_fields(wompi):
    payload = {
        "currency": "COP",
        "customer_email": "test@example.com",
        "payment_method": {"type": "CARD", "token": "tok_test_visa_123456"}
        # Falta amount_in_cents y reference
    }
    with pytest.raises(ValueError) as exc:
        wompi.create_transaction(payload)
    assert "Falta el campo obligatorio" in str(exc.value)

def test_create_transaction_invalid_payment_method(wompi):
    payload = {
        "amount_in_cents": 10000,
        "currency": "COP",
        "customer_email": "test@example.com",
        "payment_method": {"type": "CARD"},  # Falta token
        "reference": "pedido-qa-002"
    }
    with pytest.raises(ValueError) as exc:
        wompi.create_transaction(payload)
    assert "token" in str(exc.value)

def test_refund_transaction(wompi):
    with patch("payments.wompi_service.requests.post") as mock_post:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "SUCCESS"}
        resp = wompi.refund_transaction("txn_123", 10000, "QA test")
        assert resp["status"] == "SUCCESS"

def test_handle_webhook_valid_signature(wompi):
    data = '{"event":"transaction.updated","data":{"id":"txn_123"}}'
    signature = wompi.validate_signature(data, wompi.validate_signature(data, "dummy"))
    # Simula la firma correcta
    with patch.object(wompi, "validate_signature", return_value=True):
        result = wompi.handle_webhook(data, "firma")
        assert result["event"] == "transaction.updated"

def test_handle_webhook_invalid_signature(wompi):
    data = '{"event":"transaction.updated","data":{"id":"txn_123"}}'
    with patch.object(wompi, "validate_signature", return_value=False):
        result = wompi.handle_webhook(data, "firma")
        assert result is None
