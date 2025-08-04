import pytest
import httpx
from unittest.mock import AsyncMock, patch
from tausestack.sdk.gateways.wompi.client import WompiService

# Configuration for tests
TEST_PUBLIC_KEY = "pub_test_12345"
TEST_PRIVATE_KEY = "prv_test_67890" # Or event secret for webhooks
WOMPI_SANDBOX_URL = "https://sandbox.wompi.co/v1"

@pytest.fixture
def wompi_service():
    return WompiService(public_key=TEST_PUBLIC_KEY, private_key=TEST_PRIVATE_KEY)

@pytest.mark.asyncio
async def test_get_acceptance_token(wompi_service):
    mock_response_data = {"data": {"presigned_acceptance": {"acceptance_token": "tok_test_123", "permalink": "..."}}}
    
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        result = await wompi_service.get_acceptance_token()
        
        mock_get.assert_called_once_with(f"{WOMPI_SANDBOX_URL}/merchants/{TEST_PUBLIC_KEY}", headers=wompi_service.headers)
        assert result == mock_response_data

@pytest.mark.asyncio
async def test_create_payment_source(wompi_service):
    mock_response_data = {"data": {"id": 1, "status": "CREATED", "token": "card_tok_test"}}
    card_token = "tok_test_card_123"
    customer_email = "test@example.com"
    acceptance_token = "acc_tok_test_456"
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        result = await wompi_service.create_payment_source(card_token, customer_email, acceptance_token)
        
        expected_payload = {
            "type": "CARD", "token": card_token, "customer_email": customer_email, "acceptance_token": acceptance_token
        }
        mock_post.assert_called_once_with(f"{WOMPI_SANDBOX_URL}/payment_sources", json=expected_payload, headers=wompi_service.headers)
        assert result == mock_response_data

@pytest.mark.asyncio
async def test_create_transaction(wompi_service):
    mock_response_data = {"data": {"id": "txn_123", "status": "PENDING"}}
    transaction_data = {
        "amount_in_cents": 10000, "currency": "COP", "customer_email": "test@example.com",
        "payment_source_id": 1, "reference": "ref_123", "payment_description": "Test Payment"
    }
    
    with patch('httpx.AsyncClient.post', new_callable=AsyncMock) as mock_post:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = AsyncMock()
        mock_post.return_value = mock_response
        
        result = await wompi_service.create_transaction(**transaction_data)
        
        mock_post.assert_called_once_with(f"{WOMPI_SANDBOX_URL}/transactions", json=transaction_data, headers=wompi_service.headers)
        assert result == mock_response_data

@pytest.mark.asyncio
async def test_get_transaction(wompi_service):
    transaction_id = "txn_abc_123"
    mock_response_data = {"data": {"id": transaction_id, "status": "APPROVED"}}
    
    with patch('httpx.AsyncClient.get', new_callable=AsyncMock) as mock_get:
        mock_response = AsyncMock()
        mock_response.json.return_value = mock_response_data
        mock_response.raise_for_status = AsyncMock()
        mock_get.return_value = mock_response
        
        result = await wompi_service.get_transaction(transaction_id)
        
        mock_get.assert_called_once_with(f"{WOMPI_SANDBOX_URL}/transactions/{transaction_id}", headers=wompi_service.headers)
        assert result == mock_response_data

def test_generate_signature_internal_consistency(wompi_service):
    transaction_details = {
        "id": "txn_sig_test_123",
        "status": "APPROVED",
        "amount_in_cents": 50000
    }
    timestamp = 1609459200 # Example timestamp (Jan 1, 2021)
    
    generated_signature = wompi_service._generate_signature(transaction_details, timestamp)
    
    event_data = {
        "data": {"transaction": transaction_details},
        "timestamp": timestamp,
        "signature_checksum": generated_signature
    }
    
    assert wompi_service.verify_webhook_signature(event_data) is True

def test_verify_webhook_signature_fail_tampered_data(wompi_service):
    transaction_details = {
        "id": "txn_sig_test_fail",
        "status": "DECLINED",
        "amount_in_cents": 1000
    }
    timestamp = 1609459201
    
    generated_signature = wompi_service._generate_signature(transaction_details, timestamp)
    
    tampered_event_data = {
        "data": {"transaction": {**transaction_details, "amount_in_cents": 2000}}, # Amount changed
        "timestamp": timestamp,
        "signature_checksum": generated_signature
    }
    assert wompi_service.verify_webhook_signature(tampered_event_data) is False

def test_verify_webhook_signature_fail_tampered_signature(wompi_service):
    transaction_details = {
        "id": "txn_sig_test_fail_sig",
        "status": "APPROVED",
        "amount_in_cents": 7000
    }
    timestamp = 1609459202
    
    tampered_signature = "thisisafakesignature12345"
    
    event_data = {
        "data": {"transaction": transaction_details},
        "timestamp": timestamp,
        "signature_checksum": tampered_signature
    }
    assert wompi_service.verify_webhook_signature(event_data) is False
