import httpx
import hashlib
import json
from typing import Dict, Any, Optional

class WompiService:
    def __init__(self, public_key: str, private_key: str, base_url: str = "https://sandbox.wompi.co/v1"):
        self.public_key = public_key
        self.private_key = private_key
        self.base_url = base_url
        self.headers = {
            "Authorization": f"Bearer {self.public_key}"
        }

    async def _request(self, method: str, endpoint: str, data: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        async with httpx.AsyncClient() as client:
            url = f"{self.base_url}/{endpoint}"
            if method.upper() == "GET":
                response = await client.get(url, headers=self.headers)
            elif method.upper() == "POST":
                response = await client.post(url, json=data, headers=self.headers)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            await response.raise_for_status()  # Raise an exception for bad status codes
            return await response.json()

    async def get_acceptance_token(self) -> Dict[str, Any]:
        """Obtiene un token de aceptación para el uso de tarjetas."""
        return await self._request("GET", "merchants/" + self.public_key)

    async def create_payment_source(self, card_token: str, customer_email: str, acceptance_token: str) -> Dict[str, Any]:
        """Crea una fuente de pago (tokenización de tarjeta)."""
        data = {
            "type": "CARD",
            "token": card_token,
            "customer_email": customer_email,
            "acceptance_token": acceptance_token
        }
        return await self._request("POST", "payment_sources", data=data)

    async def create_transaction(self, amount_in_cents: int, currency: str, customer_email: str, 
                                 payment_source_id: int, reference: str, 
                                 payment_description: str, **kwargs) -> Dict[str, Any]:
        """Crea una transacción de pago."""
        data = {
            "amount_in_cents": amount_in_cents,
            "currency": currency,
            "customer_email": customer_email,
            "payment_source_id": payment_source_id,
            "reference": reference,
            "payment_description": payment_description,
            **kwargs
        }
        return await self._request("POST", "transactions", data=data)

    async def get_transaction(self, transaction_id: str) -> Dict[str, Any]:
        """Obtiene los detalles de una transacción."""
        return await self._request("GET", f"transactions/{transaction_id}")

    async def create_refund(self, transaction_id: str, amount_in_cents: int, reason: str) -> Dict[str, Any]:
        """Crea un reembolso para una transacción."""
        data = {
            "transaction_id": transaction_id,
            "amount_in_cents": amount_in_cents,
            "reason": reason
        }
        endpoint = f"transactions/{transaction_id}/refunds"
        return await self._request("POST", endpoint, data=data)

    def _generate_signature(self, transaction_data: Dict[str, Any], timestamp: int) -> str:
        """Genera la firma de eventos para webhooks."""
        concatenated_string = (
            f"{transaction_data['id']}"
            f"{transaction_data['status']}"
            f"{transaction_data['amount_in_cents']}"
            f"{timestamp}"
            f"{self.private_key}" # Note: Wompi docs say "events secret", using private_key if it's the same
        )
        return hashlib.sha256(concatenated_string.encode('utf-8')).hexdigest()

    def verify_webhook_signature(self, event_data: Dict[str, Any]) -> bool:
        """Verifica la firma de un evento webhook."""
        received_signature = event_data.get("signature_checksum") # Assuming checksum is passed this way
        transaction_details = event_data.get("data", {}).get("transaction", {})
        timestamp = event_data.get("timestamp")

        if not all([received_signature, transaction_details, timestamp is not None]):
            return False

        expected_signature = self._generate_signature(transaction_details, timestamp)
        return received_signature == expected_signature
