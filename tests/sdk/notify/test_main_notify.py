# Tests for Notify Module Main Logic
# Path: tests/sdk/notify/test_main_notify.py

import unittest
from unittest.mock import patch, MagicMock
import os

from tausestack.sdk.notify import main as notify_main # Renombrar para evitar conflicto
from tausestack.sdk.notify.backends import ConsoleNotifyBackend
# from tausestack.sdk.notify.exceptions import NotifyError, BackendNotConfiguredError

class TestMainNotify(unittest.TestCase):

    def tearDown(self):
        # Limpiar instancias de backend cacheadas entre pruebas
        notify_main._notify_backend_instances = {}
        # Restaurar variables de entorno si se modificaron
        if hasattr(self, '_old_env_vars'):
            for key, value in self._old_env_vars.items():
                if value is None:
                    os.environ.pop(key, None)
                else:
                    os.environ[key] = value
            delattr(self, '_old_env_vars')

    def _set_env_var(self, key, value):
        if not hasattr(self, '_old_env_vars'):
            self._old_env_vars = {}
        self._old_env_vars[key] = os.getenv(key)
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value

    @patch('tausestack.sdk.notify.backends.ConsoleNotifyBackend.send')
    def test_send_email_default_console_backend(self, mock_console_send):
        mock_console_send.return_value = True
        success = notify_main.send_email(
            to='default@example.com',
            subject='Default Test',
            body_text='Testing default backend.'
        )
        self.assertTrue(success)
        mock_console_send.assert_called_once_with(
            to='default@example.com',
            subject='Default Test',
            body_text='Testing default backend.',
            body_html=None
        )

    def test_send_email_no_body(self):
        # Debería retornar False y loggear una advertencia, no lanzar excepción por ahora
        with patch.object(notify_main.logger, 'warning') as mock_log_warning:
            success = notify_main.send_email(
                to='nobody@example.com',
                subject='No Body Test'
            )
            self.assertFalse(success)
            mock_log_warning.assert_called_once()

    @patch.dict(os.environ, {'TAUSESTACK_NOTIFY_BACKEND': 'console'})
    @patch('tausestack.sdk.notify.backends.ConsoleNotifyBackend.send')
    def test_send_email_via_env_var(self, mock_console_send):
        mock_console_send.return_value = True
        notify_main.send_email(to='env@example.com', subject='Env Var Test', body_text='Text')
        mock_console_send.assert_called_once()

    # @patch.dict(os.environ, {'TAUSESTACK_NOTIFY_BACKEND': 'non_existent_backend'})
    # def test_send_email_non_existent_backend_falls_back_to_console(self):
    #     # Actualmente, la lógica en _get_notify_backend hace fallback a Console
    #     # Si se cambiara para lanzar BackendNotConfiguredError, esta prueba necesitaría ajustarse
    #     with patch('tausestack.sdk.notify.backends.ConsoleNotifyBackend.send') as mock_console_send:
    #         mock_console_send.return_value = True
    #         with patch.object(notify_main.logger, 'error') as mock_log_error:
    #             success = notify_main.send_email(to='fallback@example.com', subject='Fallback', body_text='Text')
    #             self.assertTrue(success) # Debería usar Console y tener éxito
    #             mock_log_error.assert_called_once()
    #             self.assertIn("'non_existent_backend' no reconocido", mock_log_error.call_args[0][0])
    #             mock_console_send.assert_called_once()

    @patch('tausestack.sdk.notify.main._get_notify_backend')
    def test_send_email_backend_send_fails(self, mock_get_backend):
        mock_backend_instance = MagicMock(spec=ConsoleNotifyBackend)
        mock_backend_instance.send.return_value = False
        mock_get_backend.return_value = mock_backend_instance
        
        success = notify_main.send_email(to='fail@example.com', subject='Send Fail', body_text='Text')
        self.assertFalse(success)

    @patch('tausestack.sdk.notify.main._get_notify_backend')
    def test_send_email_backend_send_raises_exception(self, mock_get_backend):
        mock_backend_instance = MagicMock(spec=ConsoleNotifyBackend)
        mock_backend_instance.send.side_effect = Exception("SMTP Error")
        mock_get_backend.return_value = mock_backend_instance

        with patch.object(notify_main.logger, 'error') as mock_log_error:
            success = notify_main.send_email(to='exception@example.com', subject='Exception Test', body_text='Text')
            self.assertFalse(success)
            mock_log_error.assert_called_once()
            self.assertIn("Error al enviar notificación con backend ConsoleNotifyBackend: SMTP Error", mock_log_error.call_args[0][0])

if __name__ == '__main__':
    unittest.main()
