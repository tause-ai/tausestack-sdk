# TauseStack SDK - Notify Module Exceptions
# Path: tausestack/sdk/notify/exceptions.py

class NotifyError(Exception):
    """Clase base para excepciones del módulo de notificación."""
    pass

class BackendNotConfiguredError(NotifyError):
    """Excepción lanzada cuando un backend de notificación no está configurado o no se reconoce."""
    pass

class SendError(NotifyError):
    """Excepción lanzada cuando falla el envío de una notificación."""
    pass
