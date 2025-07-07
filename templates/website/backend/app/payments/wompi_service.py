import requests
import hashlib
import os

class WompiService:
    BASE_URLS = {
        "production": "https://production.wompi.co/v1",
        "sandbox": "https://sandbox.wompi.co/v1"
    }

    def __init__(self, public_key, private_key, environment="sandbox"):
        if environment not in self.BASE_URLS:
            raise ValueError(f"Entorno invÃ¡lido: {environment}. Debe ser 'production' o 'sandbox'.")
        self.public_key = public_key
        self.private_key = private_key
        self.base_url = self.BASE_URLS[environment]
        self.headers = {
            "Authorization": f"Bearer {self.public_key}"
        }

    def _validate_payload(self, payload, required_fields):
        for field in required_fields:
            if field not in payload:
                raise ValueError(f"Falta el campo obligatorio en el payload: {field}")

    def create_transaction(self, payload):
        required_fields = ["amount_in_cents", "currency", "customer_email", "payment_method", "reference"]
        self._validate_payload(payload, required_fields)

        if payload["payment_method"].get("type") == "CARD" and "token" not in payload["payment_method"]:
            raise ValueError("Falta el 'token' para el mÃ©todo de pago con tarjeta (CARD)")

        url = f"{self.base_url}/transactions"
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()  # Lanza excepciÃ³n para errores HTTP
        return response.json()

    def refund_transaction(self, transaction_id, amount_in_cents, reason):
        url = f"{self.base_url}/transactions/{transaction_id}/refund"
        payload = {
            "amount_in_cents": amount_in_cents,
            "reason": reason
        }
        response = requests.post(url, json=payload, headers=self.headers)
        response.raise_for_status()
        return response.json()

    def validate_signature(self, data, signature_header):
        # Esta es una implementaciÃ³n simplificada. La lÃ³gica real de Wompi puede variar.
        # Se recomienda consultar la documentaciÃ³n oficial para la validaciÃ³n de webhooks.
        secret = os.getenv("WOMPI_WEBHOOK_SECRET", "dummy_secret")
        content_to_sign = f"{data}{secret}"
        expected_signature = hashlib.sha256(content_to_sign.encode()).hexdigest()
        return signature_header == expected_signature

    def handle_webhook(self, data, signature):
        if not self.validate_signature(data, signature):
            # En un entorno real, aquÃ­ deberÃ­as registrar un intento de webhook no vÃ¡lido.
            return None
        return requests.utils.json.loads(data)
