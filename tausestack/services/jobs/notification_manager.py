"""
NotificationManager: API base para notificaciones multi-canal en Tausestack.

Permite enviar notificaciones por email, logs, Slack, SMS, etc.
Fácilmente extensible y seguro.
"""
import os
from typing import Optional

class NotificationManager:
    def __init__(self):
        self.channels = {}

    def register_channel(self, name: str, handler):
        self.channels[name] = handler

    def notify(self, message: str, channel: str = "log", **kwargs):
        if channel not in self.channels:
            raise ValueError(f"Canal '{channel}' no registrado")
        return self.channels[channel](message, **kwargs)

# Canal por defecto: log a consola

def log_handler(message: str, **kwargs):
    print(f"[NOTIF][LOG] {message}")

# Ejemplo de canal email (requiere configuración SMTP externa)
def email_handler(message: str, to: Optional[str] = None, **kwargs):
    # Aquí iría integración real con SMTP, SendGrid, etc.
    print(f"[NOTIF][EMAIL] Para: {to} | Msg: {message}")

# Ejemplo de canal Slack (requiere webhook)
def slack_handler(message: str, webhook_url: Optional[str] = None, **kwargs):
    # Aquí iría integración real con requests.post(webhook_url, ...)
    print(f"[NOTIF][SLACK] {message} (webhook: {webhook_url})")

# Instancia global y registro de canales básicos
global_notifier = NotificationManager()
global_notifier.register_channel("log", log_handler)
global_notifier.register_channel("email", email_handler)
global_notifier.register_channel("slack", slack_handler)

"""
Ejemplo de integración con jobs:

from services.jobs.job_manager import JobManager
from services.jobs.notification_manager import global_notifier

def job_con_notificacion():
    global_notifier.notify("¡Tarea ejecutada con éxito!", channel="log")
    global_notifier.notify("Notificación por email", channel="email", to="usuario@dominio.com")

jm = JobManager()
jm.register("tarea_notif", job_con_notificacion)
jm.run("tarea_notif")
"""

# Patrón de extensión seguro:
# - Para agregar un nuevo canal, define una función handler y regístrala con global_notifier.register_channel("nombre", handler)
# - Nunca expongas tokens/credenciales en código; usa variables de entorno/configuración.

global_notifier.register_channel("log", log_handler)
global_notifier.register_channel("email", email_handler)
global_notifier.register_channel("slack", slack_handler)
