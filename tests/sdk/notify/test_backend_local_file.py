import os
import shutil
import tempfile
import unittest
from unittest.mock import patch, mock_open
import datetime

from tausestack.sdk.notify.backends import LocalFileNotifyBackend, _sanitize_filename

class TestSanitizeFilename(unittest.TestCase):
    def test_sanitize_basic(self):
        self.assertEqual(_sanitize_filename("Test Subject!"), "Test_Subject!")

    def test_sanitize_special_chars(self):
        self.assertEqual(_sanitize_filename('File with <>:"/\\|?* chars'), 'File_with_chars')

    def test_sanitize_long_name(self):
        long_name = "a" * 150
        self.assertEqual(len(_sanitize_filename(long_name)), 100)

    def test_sanitize_spaces(self):
        self.assertEqual(_sanitize_filename("subject with multiple   spaces"), "subject_with_multiple_spaces")

class TestLocalFileNotifyBackend(unittest.TestCase):
    def setUp(self):
        # Crear un directorio temporal para las pruebas
        self.test_dir_obj = tempfile.TemporaryDirectory()
        self.test_dir = self.test_dir_obj.name
        self.backend = LocalFileNotifyBackend(base_path=self.test_dir)

    def tearDown(self):
        # Limpiar el directorio temporal
        self.test_dir_obj.cleanup()

    def test_init_creates_directory(self):
        # Verificar que el directorio base se crea si no existe
        new_dir = os.path.join(self.test_dir, "new_notifications")
        if os.path.exists(new_dir):
            shutil.rmtree(new_dir) # Asegurarse de que no existe
        LocalFileNotifyBackend(base_path=new_dir)
        self.assertTrue(os.path.exists(new_dir))
        shutil.rmtree(new_dir)

    def test_send_text_email(self):
        to = "test@example.com"
        subject = "Test Text Email Subject"
        body_text = "This is the body of the text email."
        
        success = self.backend.send(to=to, subject=subject, body_text=body_text, custom_arg="test_value")
        self.assertTrue(success)
        
        # Verificar que el archivo fue creado
        files = os.listdir(self.test_dir)
        self.assertEqual(len(files), 1)
        filepath = os.path.join(self.test_dir, files[0])
        self.assertTrue(files[0].endswith(".txt"))
        self.assertTrue(_sanitize_filename(subject) in files[0])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(f"To: {to}", content)
            self.assertIn(f"Subject: {subject}", content)
            self.assertIn("--- Body (Text) ---", content)
            self.assertIn(body_text, content)
            self.assertIn("custom_arg: test_value", content)

    def test_send_html_email(self):
        to = ["test1@example.com", "test2@example.com"]
        subject = "Test HTML Email with <special> & chars"
        body_html = "<h1>Hello!</h1><p>This is HTML.</p>"
        
        success = self.backend.send(to=to, subject=subject, body_html=body_html)
        self.assertTrue(success)
        
        files = os.listdir(self.test_dir)
        self.assertEqual(len(files), 1)
        filepath = os.path.join(self.test_dir, files[0])
        self.assertTrue(files[0].endswith(".html"))
        self.assertTrue(_sanitize_filename(subject) in files[0])
        
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn(f"To: {', '.join(to)}", content)
            self.assertIn(f"Subject: {subject}", content)
            self.assertIn("--- Body (HTML) ---", content)
            self.assertIn(body_html, content)

    def test_send_no_body(self):
        to = "nobody@example.com"
        subject = "Test No Body"
        success = self.backend.send(to=to, subject=subject)
        self.assertTrue(success)

        files = os.listdir(self.test_dir)
        self.assertEqual(len(files), 1)
        filepath = os.path.join(self.test_dir, files[0])
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
            self.assertIn("--- No Body Content ---", content)

    @patch("tausestack.sdk.notify.backends.open", new_callable=mock_open)
    @patch("tausestack.sdk.notify.backends.logger")
    def test_send_io_error(self, mock_logger, mock_file_open):
        mock_file_open.side_effect = IOError("Disk full")
        
        success = self.backend.send(to="error@example.com", subject="IO Error Test", body_text="test")
        self.assertFalse(success)
        mock_logger.error.assert_called_once()
        self.assertIn("Error al escribir notificación en archivo", mock_logger.error.call_args[0][0])

    @patch("tausestack.sdk.notify.backends.os.makedirs")
    @patch("tausestack.sdk.notify.backends.logger")
    def test_init_cannot_create_directory(self, mock_logger, mock_makedirs):
        mock_makedirs.side_effect = OSError("Permission denied")
        
        with self.assertRaises(OSError):
            LocalFileNotifyBackend(base_path="/unwritable_path/notifications")
        
        mock_logger.error.assert_called_once()
        self.assertIn("No se pudo crear el directorio de notificaciones", mock_logger.error.call_args[0][0])

if __name__ == '__main__':
    unittest.main()
