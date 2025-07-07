# Tests for ConsoleNotifyBackend
# Path: tests/sdk/notify/test_backend_console.py

import unittest
from unittest.mock import patch
import io

from tausestack.sdk.notify.backends import ConsoleNotifyBackend

class TestConsoleNotifyBackend(unittest.TestCase):

    def setUp(self):
        self.backend = ConsoleNotifyBackend()

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_send_simple_text_email(self, mock_stdout):
        success = self.backend.send(
            to='test@example.com',
            subject='Test Subject',
            body_text='Hello, world!'
        )
        self.assertTrue(success)
        output = mock_stdout.getvalue()
        self.assertIn('Para: test@example.com', output)
        self.assertIn('Asunto: Test Subject', output)
        self.assertIn('Hello, world!', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_send_html_email(self, mock_stdout):
        success = self.backend.send(
            to=['test1@example.com', 'test2@example.com'],
            subject='HTML Test',
            body_html='<h1>Hello</h1><p>World</p>'
        )
        self.assertTrue(success)
        output = mock_stdout.getvalue()
        self.assertIn('Para: test1@example.com, test2@example.com', output)
        self.assertIn('Asunto: HTML Test', output)
        self.assertIn('<h1>Hello</h1><p>World</p>', output)

    @patch('sys.stdout', new_callable=io.StringIO)
    def test_send_with_kwargs(self, mock_stdout):
        success = self.backend.send(
            to='kwarg@example.com',
            subject='Kwargs Test',
            body_text='Testing kwargs.',
            custom_header='X-My-Header: value'
        )
        self.assertTrue(success)
        output = mock_stdout.getvalue()
        self.assertIn("Opciones adicionales: {'custom_header': 'X-My-Header: value'}", output)

if __name__ == '__main__':
    unittest.main()
