# TauseStack SDK - Notify Module Base
# Path: tausestack/sdk/notify/base.py

import abc
from typing import Any, Dict, List, Optional, Union

class AbstractNotifyBackend(abc.ABC):
    """Interfaz abstracta para los backends de notificación."""

    @abc.abstractmethod
    def send(
        self,
        to: Union[str, List[str]],
        subject: str,
        body_text: Optional[str] = None,
        body_html: Optional[str] = None,
        # attachments: Optional[List[Dict[str, Any]]] = None, # Se definirá mejor más adelante
        **kwargs: Any
    ) -> bool:
        """Envía una notificación.

        Args:
            to: Destinatario o lista de destinatarios.
            subject: Asunto de la notificación.
            body_text: Cuerpo de la notificación en texto plano.
            body_html: Cuerpo de la notificación en HTML.
            # attachments: Lista de adjuntos.
            **kwargs: Argumentos adicionales específicos del backend.

        Returns:
            True si el envío fue exitoso, False en caso contrario.
        """
        pass
