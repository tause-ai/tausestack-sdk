# TauseStack SDK - Notify Module Backends
# Path: tausestack/sdk/notify/backends.py

from .base import AbstractNotifyBackend
from typing import Any, Dict, List, Optional, Union
import logging

logger = logging.getLogger(__name__)


import os
import datetime
import re

def _sanitize_filename(name: str) -> str:
    """Sanitiza una cadena para que sea un nombre de archivo seguro."""
    replacements = {
        '<': '_', '>': '_', ':': '_', '"': '_',
        '/': '_', '\\': '_', '|': '_', '?': '_', '*': '_'
    }
    for char, replacement in replacements.items():
        name = name.replace(char, replacement)
    
    # Reemplazar secuencias de espacios en blanco con un solo guion bajo
    name = re.sub(r'\s+', '_', name)
    
    # Consolidar múltiples guiones bajos consecutivos que podrían resultar
    # de reemplazos adyacentes o de espacios junto a caracteres reemplazados.
    # Por ejemplo, "a:/b" -> "a__b" -> "a_b". O "a / b" -> "a___b" -> "a_b".
    name = re.sub(r'_+', '_', name)

    return name[:100] # Limitar longitud

try:
    import boto3
    from botocore.exceptions import ClientError, NoCredentialsError, PartialCredentialsError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False
    # Definir stubs para ClientError si boto3 no está disponible, para que el type hinting no falle
    class ClientError(Exception):
        pass

class SESNotifyBackend(AbstractNotifyBackend):
    """Backend de notificación que envía mensajes usando AWS Simple Email Service (SES)."""

    def __init__(self, source_email: str, aws_region: Optional[str] = None, aws_access_key_id: Optional[str] = None, aws_secret_access_key: Optional[str] = None):
        if not BOTO3_AVAILABLE:
            logger.error("El paquete boto3 no está instalado. SESNotifyBackend no puede funcionar.")
            raise ImportError("boto3 es requerido para SESNotifyBackend. Instálalo con 'pip install boto3'.")

        self.source_email = source_email
        self.aws_region = aws_region
        self.aws_access_key_id = aws_access_key_id
        self.aws_secret_access_key = aws_secret_access_key
        
        try:
            # Si se proporcionan credenciales explícitas, usarlas.
            # De lo contrario, boto3 buscará en variables de entorno, roles IAM, etc.
            session_params = {}
            if aws_region:
                session_params['region_name'] = aws_region
            if aws_access_key_id and aws_secret_access_key:
                session_params['aws_access_key_id'] = aws_access_key_id
                session_params['aws_secret_access_key'] = aws_secret_access_key
            
            if session_params:
                session = boto3.Session(**session_params)
                self.client = session.client('ses')
            else:
                # Permitir que boto3 determine la región y credenciales por defecto
                self.client = boto3.client('ses', region_name=self.aws_region if self.aws_region else None)
            
            # Verificar si las credenciales son válidas intentando una operación no destructiva
            # (esto es opcional, pero puede ayudar a detectar problemas de configuración temprano)
            # self.client.get_send_quota() 

        except (NoCredentialsError, PartialCredentialsError) as e:
            logger.error(f"Error de credenciales de AWS al inicializar SESNotifyBackend: {e}")
            raise
        except ClientError as e:
            logger.error(f"Error de cliente AWS (posiblemente región incorrecta o permisos) al inicializar SESNotifyBackend: {e}")
            raise
        except Exception as e: # Captura más general para problemas inesperados
            logger.error(f"Error inesperado al inicializar el cliente SES: {e}")
            raise

    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        **kwargs: Any # Podría usarse para Reply-To, CC, BCC, etc. en el futuro
    ) -> bool:
        if not self.client:
            logger.error("Cliente SES no inicializado. No se puede enviar el correo.")
            return False

        if not body_text and not body_html:
            logger.warning("Se intentó enviar un correo vía SES sin body_text ni body_html.")
            return False

        destinations = to if isinstance(to, list) else [to]
        
        message_body = {}
        if body_text:
            message_body['Text'] = {'Data': body_text, 'Charset': 'UTF-8'}
        if body_html:
            message_body['Html'] = {'Data': body_html, 'Charset': 'UTF-8'}

        try:
            response = self.client.send_email(
                Source=self.source_email,
                Destination={'ToAddresses': destinations},
                Message={
                    'Subject': {'Data': subject, 'Charset': 'UTF-8'},
                    'Body': message_body
                },
                # Se podrían añadir ReplyToAddresses, ConfigurationSetName, etc. aquí desde kwargs si es necesario
            )
            logger.info(f"Correo enviado vía SES. Message ID: {response.get('MessageId')}")
            return True
        except ClientError as e:
            error_code = e.response.get('Error', {}).get('Code')
            error_message = e.response.get('Error', {}).get('Message')
            logger.error(f"Error al enviar correo vía SES ({error_code}): {error_message}")
            # Podríamos querer manejar errores específicos como 'MessageRejected' o 'MailFromDomainNotVerifiedException'
            # de manera diferente si fuera necesario.
            return False
        except Exception as e:
            logger.error(f"Error inesperado al enviar correo vía SES: {e}", exc_info=True)
            return False

class LocalFileNotifyBackend(AbstractNotifyBackend):
    """Backend de notificación que guarda los detalles del mensaje en un archivo local."""

    def __init__(self, base_path: str):
        self.base_path = base_path
        if not os.path.exists(self.base_path):
            try:
                os.makedirs(self.base_path, exist_ok=True)
                logger.info(f"Directorio de notificaciones creado: {self.base_path}")
            except OSError as e:
                logger.error(f"No se pudo crear el directorio de notificaciones {self.base_path}: {e}")
                raise

    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        recipients = ", ".join(to) if isinstance(to, list) else to
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S_%f")
        sanitized_subject = _sanitize_filename(subject)
        
        file_extension = '.html' if body_html else '.txt'
        filename = f"{timestamp}_{sanitized_subject}{file_extension}"
        filepath = os.path.join(self.base_path, filename)

        content_to_write = f"To: {recipients}\n"
        content_to_write += f"Subject: {subject}\n"
        content_to_write += f"Date: {datetime.datetime.now().isoformat()}\n\n"

        if body_html:
            content_to_write += "--- Body (HTML) ---\n"
            content_to_write += body_html
        elif body_text:
            content_to_write += "--- Body (Text) ---\n"
            content_to_write += body_text
        else:
            content_to_write += "--- No Body Content ---"
        
        if kwargs:
            content_to_write += "\n\n--- Additional Options ---\n"
            for key, value in kwargs.items():
                content_to_write += f"{key}: {value}\n"

        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content_to_write)
            logger.info(f"Notificación guardada en archivo: {filepath}")
            return True
        except IOError as e:
            logger.error(f"Error al escribir notificación en archivo {filepath}: {e}")
            return False

class ConsoleNotifyBackend(AbstractNotifyBackend):
    """Backend de notificación que imprime los detalles del mensaje en la consola."""

    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        # attachments: Optional[List[Dict[str, Any]]] = None,
        **kwargs: Any
    ) -> bool:
        recipients = ", ".join(to) if isinstance(to, list) else to
        print("---- Nueva Notificación (Consola) ----")
        print(f"Para: {recipients}")
        print(f"Asunto: {subject}")
        if body_text:
            print("--- Cuerpo (Texto) ---")
            print(body_text)
        if body_html:
            print("--- Cuerpo (HTML) ---")
            print(body_html)
        # if attachments:
        #     print(f"Adjuntos: {len(attachments)} archivo(s)")
        if kwargs:
            print(f"Opciones adicionales: {kwargs}")
        print("--------------------------------------")
        logger.info(f"Notificación enviada a la consola para: {recipients}, Asunto: {subject}")
        return True
