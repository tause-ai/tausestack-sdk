#!/usr/bin/env python
# -*- coding: utf-8 -*-

import unittest
import os
from unittest.mock import patch, MagicMock

# Asegurarse de que boto3 y moto estén disponibles para las pruebas
# Esto es más una nota para el desarrollador; la importación real se maneja en el backend
try:
    import boto3
    from moto import mock_aws
    MOTO_SES_AVAILABLE = True
except ImportError:
    MOTO_SES_AVAILABLE = False

from tausestack.sdk.notify.backends import SESNotifyBackend, BOTO3_AVAILABLE
from tausestack.sdk.notify.exceptions import NotifyError # Si se usa para errores específicos

# Solo ejecutar pruebas si moto[ses] y boto3 están disponibles
@unittest.skipIf(not MOTO_SES_AVAILABLE, "moto[ses] o boto3 no están instalados, saltando pruebas de SESBackend")
class TestSESNotifyBackend(unittest.TestCase):

    def setUp(self): 
        # Configuración común para las pruebas de SES
        self.source_email = "sender@example.com"
        self.aws_region = "us-east-1" # Moto típicamente usa esta región por defecto
        
        # Simular variables de entorno si el backend las usa directamente (aunque es mejor pasar config)
        # os.environ['TAUSESTACK_NOTIFY_SES_SOURCE_EMAIL'] = self.source_email
        # os.environ['TAUSESTACK_NOTIFY_SES_AWS_REGION'] = self.aws_region

    @mock_aws
    def test_send_email_success(self):
        """Prueba el envío exitoso de un correo electrónico usando SES simulado."""
        conn = boto3.client("ses", region_name=self.aws_region)
        conn.verify_email_identity(EmailAddress=self.source_email) # SES requiere que el remitente esté verificado

        backend = SESNotifyBackend(source_email=self.source_email, aws_region=self.aws_region)
        
        to_email = "recipient@example.com"
        subject = "Test Email from SES"
        body_text = "This is a test email body (text)."
        body_html = "<h1>This is a test email body (HTML).</h1>"

        success = backend.send(
            to=to_email,
            subject=subject,
            body_text=body_text,
            body_html=body_html
        )
        self.assertTrue(success, "El método send debería retornar True en caso de éxito.")

        # Verificar que send_email fue llamado (moto no lo hace directamente, pero podemos verificar el estado de envío si tuviéramos acceso a métricas o logs)
        # Por ahora, el éxito de la llamada a la API de boto3 es la principal verificación.
        # Moto intercepta la llamada a send_email. Si no hay excepciones, se asume que la llamada fue procesada por moto.

    @mock_aws
    def test_send_email_client_error(self):
        """Prueba el manejo de ClientError de AWS SES."""
        # Inicializar el backend normalmente. Su self.client será un cliente moto.
        backend = SESNotifyBackend(source_email=self.source_email, aws_region=self.aws_region)

        # Para instanciar ClientError correctamente para el side_effect, necesitamos un cliente SES.
        # @mock_aws ya nos da esto a través de boto3.client dentro del contexto mock_aws.
        ses_client_for_exceptions = boto3.client('ses', region_name=self.aws_region)
        
        # Parchear el método send_email en la instancia del cliente DENTRO del objeto backend.
        with patch.object(backend.client, 'send_email', side_effect=ses_client_for_exceptions.exceptions.ClientError(
            {'Error': {'Code': 'MessageRejected', 'Message': 'Email address is not verified.'}},
            'SendEmail'
        )) as mock_send_email_method:
            success = backend.send(
                to="recipient@example.com",
                subject="Test Error",
                body_text="Test"
            )
            self.assertFalse(success, "El método send debería retornar False si SES ClientError ocurre.")
            mock_send_email_method.assert_called_once()

    def test_initialization_no_boto3(self):
        """Prueba que la inicialización falla si boto3 no está disponible."""
        with patch('tausestack.sdk.notify.backends.BOTO3_AVAILABLE', False):
            with self.assertRaises(ImportError):
                SESNotifyBackend(source_email=self.source_email, aws_region=self.aws_region)

    @mock_aws
    def test_send_without_body(self):
        """Prueba que el envío falla si no se provee ni body_text ni body_html."""
        conn = boto3.client("ses", region_name=self.aws_region)
        conn.verify_email_identity(EmailAddress=self.source_email)
        backend = SESNotifyBackend(source_email=self.source_email, aws_region=self.aws_region)
        success = backend.send(to="r@x.com", subject="Test")
        self.assertFalse(success, "El envío debe fallar si no hay cuerpo de mensaje.")

    @mock_aws
    def test_send_to_multiple_recipients(self):
        """Prueba el envío a múltiples destinatarios."""
        conn = boto3.client("ses", region_name=self.aws_region)
        conn.verify_email_identity(EmailAddress=self.source_email)
        backend = SESNotifyBackend(source_email=self.source_email, aws_region=self.aws_region)
        
        recipients = ["r1@example.com", "r2@example.com"]
        success = backend.send(
            to=recipients,
            subject="Multiple Recipients Test",
            body_text="Hello all!"
        )
        self.assertTrue(success, "El envío a múltiples destinatarios debería ser exitoso.")

    @mock_aws
    def test_initialization_with_explicit_credentials(self):
        """Prueba la inicialización del backend con credenciales explícitas."""
        # Moto no usa realmente las credenciales, pero podemos verificar que el cliente se crea.
        # Esta prueba es más para la lógica de inicialización del backend.
        try:
            backend = SESNotifyBackend(
                source_email=self.source_email,
                aws_region=self.aws_region,
                aws_access_key_id='TEST_ACCESS_KEY',
                aws_secret_access_key='TEST_SECRET_KEY'
            )
            self.assertIsNotNone(backend.client, "El cliente SES debería inicializarse con credenciales explícitas.")
        except Exception as e:
            self.fail(f"La inicialización con credenciales explícitas no debería fallar: {e}")


if __name__ == '__main__':
    unittest.main()
