# TauseStack SDK - Notify Module Main Logic
# Path: tausestack/sdk/notify/main.py

from typing import Any, Dict, List, Optional, Union
import os
import logging

from .base import AbstractNotifyBackend
from .backends import ConsoleNotifyBackend, LocalFileNotifyBackend, SESNotifyBackend, BOTO3_AVAILABLE
# Importar otros backends aquí cuando se implementen
from .exceptions import NotifyError, BackendNotConfiguredError # Descomentar si se usan

logger = logging.getLogger(__name__)

_notify_backend_instances: Dict[str, AbstractNotifyBackend] = {}

DEFAULT_NOTIFY_BACKEND = 'console'
DEFAULT_NOTIFY_LOCAL_FILE_PATH = './.tausestack_notifications'
DEFAULT_NOTIFY_SES_SOURCE_EMAIL = os.getenv('TAUSESTACK_NOTIFY_SES_SOURCE_EMAIL', None)
DEFAULT_NOTIFY_SES_AWS_REGION = os.getenv('TAUSESTACK_NOTIFY_SES_AWS_REGION', None)
# DEFAULT_NOTIFY_BACKEND_CONFIG: Dict[str, Dict[str, Any]] = {
#     'console': {},
#     'local_file': {'base_path': './.tausestack_notifications'},
#     'ses': {},
#     'smtp': {'host': '', 'port': 587, 'username': '', 'password': '', 'use_tls': True}
# }

def _get_notify_backend(backend_name: Optional[str] = None, config: Optional[Dict[str, Any]] = None) -> AbstractNotifyBackend:
    effective_backend_name = backend_name or os.getenv('TAUSESTACK_NOTIFY_BACKEND', DEFAULT_NOTIFY_BACKEND)
    config_to_use = config or {}

    instance_key = effective_backend_name
    if effective_backend_name == 'local_file':
        base_path = config_to_use.get('base_path', os.getenv('TAUSESTACK_NOTIFY_LOCAL_FILE_PATH', DEFAULT_NOTIFY_LOCAL_FILE_PATH))
        # Crear una clave de instancia única basada en base_path para permitir múltiples instancias con diferentes rutas
        path_key_component = base_path.replace('/', '_').replace('.', '_').replace(':', '_') # Simplificar esto si es posible
        instance_key = f"local_file_path_{path_key_component}"
    elif effective_backend_name == 'ses':
        # Para SES, la clave de instancia podría basarse en source_email y región si se permiten múltiples configuraciones
        # Por ahora, una instancia global es suficiente si la configuración es global vía env vars o una única config.
        # Si se pasan aws_access_key_id/aws_secret_access_key en config, la clave debería incluirlos para ser única.
        source_email = config_to_use.get('source_email', DEFAULT_NOTIFY_SES_SOURCE_EMAIL)
        aws_region = config_to_use.get('aws_region', DEFAULT_NOTIFY_SES_AWS_REGION)
        aws_access_key_id = config_to_use.get('aws_access_key_id') # No hay default para credenciales directas
        aws_secret_access_key = config_to_use.get('aws_secret_access_key')
        
        # Construir una clave de instancia más específica si se usan credenciales directas
        if aws_access_key_id and aws_secret_access_key:
            instance_key = f"ses_{source_email}_{aws_region}_{aws_access_key_id[:5]}" # Usar parte del access key para unicidad
        else:
            instance_key = f"ses_{source_email}_{aws_region}" 

    if instance_key not in _notify_backend_instances:
        logger.debug(f"Creando nueva instancia para backend de notificación: {instance_key}")
        if effective_backend_name == 'console':
            _notify_backend_instances[instance_key] = ConsoleNotifyBackend()
        elif effective_backend_name == 'local_file':
            base_path = config_to_use.get('base_path', os.getenv('TAUSESTACK_NOTIFY_LOCAL_FILE_PATH', DEFAULT_NOTIFY_LOCAL_FILE_PATH))
            _notify_backend_instances[instance_key] = LocalFileNotifyBackend(base_path=base_path)
        elif effective_backend_name == 'ses':
            if not BOTO3_AVAILABLE:
                logger.error("Intento de usar SESNotifyBackend pero boto3 no está disponible. Usando ConsoleBackend.")
                _notify_backend_instances[instance_key] = ConsoleNotifyBackend()
            else:
                source_email = config_to_use.get('source_email', DEFAULT_NOTIFY_SES_SOURCE_EMAIL)
                aws_region = config_to_use.get('aws_region', DEFAULT_NOTIFY_SES_AWS_REGION)
                aws_access_key_id = config_to_use.get('aws_access_key_id')
                aws_secret_access_key = config_to_use.get('aws_secret_access_key')

                if not source_email:
                    logger.error("TAUSESTACK_NOTIFY_SES_SOURCE_EMAIL no está configurado. No se puede usar SESNotifyBackend. Usando ConsoleBackend.")
                    _notify_backend_instances[instance_key] = ConsoleNotifyBackend()
                else:
                    try:
                        _notify_backend_instances[instance_key] = SESNotifyBackend(
                            source_email=source_email,
                            aws_region=aws_region,
                            aws_access_key_id=aws_access_key_id,
                            aws_secret_access_key=aws_secret_access_key
                        )
                    except ImportError: # Ya logueado por el constructor de SESNotifyBackend
                        _notify_backend_instances[instance_key] = ConsoleNotifyBackend()
                    except Exception as e: # Captura errores de credenciales/configuración de SES
                        logger.error(f"Error al inicializar SESNotifyBackend ({e}). Usando ConsoleBackend.")
                        _notify_backend_instances[instance_key] = ConsoleNotifyBackend()
        # elif effective_backend_name == 'ses':
        #     # Lógica para SES
        #     pass
        # elif effective_backend_name == 'smtp':
        #     # Lógica para SMTP
        #     pass
        else:
            logger.error(f"Backend de notificación '{effective_backend_name}' no reconocido o no implementado. Usando ConsoleBackend por defecto.")
            # Considerar lanzar BackendNotConfiguredError aquí en lugar de hacer fallback silencioso
            # raise BackendNotConfiguredError(f"Backend de notificación '{effective_backend_name}' no reconocido o no implementado.")
            _notify_backend_instances[instance_key] = ConsoleNotifyBackend() # Fallback a consola por ahora
    
    return _notify_backend_instances[instance_key]

def send_email(
    to: Union[str, List[str]],
    subject: str,
    body_text: Optional[str] = None,
    body_html: Optional[str] = None,
    # attachments: Optional[List[Dict[str, Any]]] = None,
    backend: Optional[str] = None,
    backend_config: Optional[Dict[str, Any]] = None,
    **kwargs: Any
) -> bool:
    """Envía un correo electrónico utilizando el backend de notificación configurado.

    Args:
        to: Destinatario o lista de destinatarios del correo.
        subject: Asunto del correo.
        body_text: Cuerpo del correo en formato de texto plano.
        body_html: Cuerpo del correo en formato HTML.
        # attachments: Lista de adjuntos. Cada adjunto es un dict con 'filename' y 'content'.
        backend: Nombre del backend a utilizar (e.g., 'console', 'ses', 'smtp').
                 Si es None, usa el backend por defecto.
        backend_config: Configuración específica para el backend seleccionado.
        **kwargs: Argumentos adicionales para pasar al método send del backend.

    Returns:
        True si el correo fue enviado exitosamente, False en caso contrario.
    """
    if not body_text and not body_html:
        logger.warning("Se intentó enviar un correo sin body_text ni body_html.")
        # Considerar lanzar ValueError aquí
        # raise ValueError("Se debe proporcionar al menos body_text o body_html.")
        return False

    try:
        selected_backend = _get_notify_backend(backend_name=backend, config=backend_config)
        return selected_backend.send(
            to=to,
            subject=subject,
            body_text=body_text,
            body_html=body_html,
            # attachments=attachments,
            **kwargs
        )
    except Exception as e:
        logger.error(f"Error al enviar notificación con backend {selected_backend.__class__.__name__}: {e}", exc_info=True)
        # Considerar lanzar NotifyError aquí
        # raise NotifyError(f"Error al enviar notificación: {e}") from e
        return False

