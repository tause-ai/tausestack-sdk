#!/usr/bin/env python3
"""
Communications Service - Multi-Tenant API
TauseStack v0.5.0

Servicio de comunicaciones con aislamiento completo por tenant.
Implementa:
- Email marketing por tenant
- SMS notifications
- Push notifications
- Templates personalizados
- Campañas automatizadas
- Tracking de entregas
- Rate limiting por tenant
"""

from fastapi import FastAPI, HTTPException, Header, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, EmailStr
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import json
import os
import logging
from contextlib import asynccontextmanager
import uuid

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger("communications-service")

# --- Modelos de datos ---

class ChannelType(str, Enum):
    """Tipos de canales de comunicación."""
    EMAIL = "email"
    SMS = "sms"
    PUSH = "push"
    WEBHOOK = "webhook"
    IN_APP = "in_app"

class MessageStatus(str, Enum):
    """Estados de mensajes."""
    PENDING = "pending"
    QUEUED = "queued"
    SENDING = "sending"
    SENT = "sent"
    DELIVERED = "delivered"
    FAILED = "failed"
    BOUNCED = "bounced"
    OPENED = "opened"
    CLICKED = "clicked"

class TemplateType(str, Enum):
    """Tipos de templates."""
    TRANSACTIONAL = "transactional"
    MARKETING = "marketing"
    NOTIFICATION = "notification"
    WELCOME = "welcome"
    RESET_PASSWORD = "reset_password"
    CUSTOM = "custom"

class Priority(str, Enum):
    """Prioridades de envío."""
    LOW = "low"
    NORMAL = "normal"
    HIGH = "high"
    URGENT = "urgent"

class MessageRequest(BaseModel):
    """Request para enviar mensaje."""
    message_id: Optional[str] = None
    tenant_id: Optional[str] = None
    channel: ChannelType
    recipients: List[str]  # emails, phone numbers, device tokens
    template_id: Optional[str] = None
    subject: Optional[str] = None
    content: str
    variables: Dict[str, Any] = Field(default_factory=dict)
    priority: Priority = Priority.NORMAL
    scheduled_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class EmailMessage(BaseModel):
    """Mensaje de email específico."""
    to: List[EmailStr]
    cc: List[EmailStr] = Field(default_factory=list)
    bcc: List[EmailStr] = Field(default_factory=list)
    subject: str
    html_content: Optional[str] = None
    text_content: Optional[str] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)
    reply_to: Optional[EmailStr] = None

class SMSMessage(BaseModel):
    """Mensaje SMS específico."""
    to: List[str]  # phone numbers
    content: str
    sender_id: Optional[str] = None

class PushMessage(BaseModel):
    """Mensaje push específico."""
    device_tokens: List[str]
    title: str
    body: str
    data: Dict[str, Any] = Field(default_factory=dict)
    badge: Optional[int] = None
    sound: Optional[str] = None

class Template(BaseModel):
    """Template de mensaje."""
    template_id: str
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    template_type: TemplateType
    channel: ChannelType
    subject_template: Optional[str] = None
    content_template: str
    variables: List[str] = Field(default_factory=list)
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class Campaign(BaseModel):
    """Campaña de comunicación."""
    campaign_id: str
    name: str
    description: Optional[str] = None
    tenant_id: Optional[str] = None
    template_id: str
    channel: ChannelType
    audience_filter: Dict[str, Any] = Field(default_factory=dict)
    scheduled_at: Optional[datetime] = None
    status: str = "draft"  # draft, scheduled, running, completed, paused
    created_at: Optional[datetime] = None

class TenantCommunicationsConfig(BaseModel):
    """Configuración de comunicaciones por tenant."""
    tenant_id: str
    name: str
    email_config: Dict[str, Any] = Field(default_factory=dict)
    sms_config: Dict[str, Any] = Field(default_factory=dict)
    push_config: Dict[str, Any] = Field(default_factory=dict)
    rate_limits: Dict[str, int] = Field(default_factory=dict)
    default_sender: Dict[str, str] = Field(default_factory=dict)
    tracking_enabled: bool = Field(default=True)
    analytics_enabled: bool = Field(default=True)

class DeliveryReport(BaseModel):
    """Reporte de entrega."""
    message_id: str
    tenant_id: str
    channel: ChannelType
    recipient: str
    status: MessageStatus
    timestamp: datetime
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

# --- Storage multi-tenant simulado ---

class TenantCommunicationsStorage:
    """Storage de comunicaciones aislado por tenant."""
    
    def __init__(self):
        self.tenant_messages: Dict[str, List[Dict[str, Any]]] = {}
        self.tenant_templates: Dict[str, Dict[str, Template]] = {}
        self.tenant_campaigns: Dict[str, Dict[str, Campaign]] = {}
        self.tenant_configs: Dict[str, TenantCommunicationsConfig] = {}
        self.tenant_delivery_reports: Dict[str, List[DeliveryReport]] = {}
        self.tenant_rate_counters: Dict[str, Dict[str, int]] = {}
    
    def get_tenant_messages(self, tenant_id: str) -> List[Dict[str, Any]]:
        """Obtener mensajes del tenant."""
        if tenant_id not in self.tenant_messages:
            self.tenant_messages[tenant_id] = []
        return self.tenant_messages[tenant_id]
    
    def get_tenant_templates(self, tenant_id: str) -> Dict[str, Template]:
        """Obtener templates del tenant."""
        if tenant_id not in self.tenant_templates:
            self.tenant_templates[tenant_id] = {}
        return self.tenant_templates[tenant_id]
    
    def get_tenant_campaigns(self, tenant_id: str) -> Dict[str, Campaign]:
        """Obtener campañas del tenant."""
        if tenant_id not in self.tenant_campaigns:
            self.tenant_campaigns[tenant_id] = {}
        return self.tenant_campaigns[tenant_id]
    
    async def store_message(self, tenant_id: str, message: Dict[str, Any]) -> str:
        """Almacenar mensaje."""
        messages = self.get_tenant_messages(tenant_id)
        message_id = message.get("message_id", str(uuid.uuid4()))
        message["message_id"] = message_id
        message["created_at"] = datetime.utcnow().isoformat()
        messages.append(message)
        return message_id
    
    async def update_message_status(self, tenant_id: str, message_id: str, status: MessageStatus):
        """Actualizar estado del mensaje."""
        messages = self.get_tenant_messages(tenant_id)
        for message in messages:
            if message.get("message_id") == message_id:
                message["status"] = status
                message["updated_at"] = datetime.utcnow().isoformat()
                break

# Storage global
communications_storage = TenantCommunicationsStorage()

# --- Simuladores de proveedores ---

class MockEmailProvider:
    """Simulador de proveedor de email."""
    
    async def send_email(self, tenant_id: str, email: EmailMessage) -> bool:
        """Simular envío de email."""
        await asyncio.sleep(0.1)  # Simular latencia
        logger.info(f"📧 Email enviado para tenant {tenant_id}: {email.subject} → {email.to}")
        return True

class MockSMSProvider:
    """Simulador de proveedor SMS."""
    
    async def send_sms(self, tenant_id: str, sms: SMSMessage) -> bool:
        """Simular envío de SMS."""
        await asyncio.sleep(0.1)  # Simular latencia
        logger.info(f"📱 SMS enviado para tenant {tenant_id}: {sms.content[:50]}... → {sms.to}")
        return True

class MockPushProvider:
    """Simulador de proveedor push."""
    
    async def send_push(self, tenant_id: str, push: PushMessage) -> bool:
        """Simular envío de push notification."""
        await asyncio.sleep(0.1)  # Simular latencia
        logger.info(f"🔔 Push enviado para tenant {tenant_id}: {push.title} → {len(push.device_tokens)} devices")
        return True

# Proveedores globales
email_provider = MockEmailProvider()
sms_provider = MockSMSProvider()
push_provider = MockPushProvider()

# --- Helpers multi-tenant ---

def get_tenant_id_from_request(
    tenant_id: Optional[str] = Header(None, alias="X-Tenant-ID"),
    tenant_query: Optional[str] = Query(None, alias="tenant_id")
) -> str:
    """Extraer tenant ID del request."""
    effective_tenant = tenant_id or tenant_query or "default"
    return effective_tenant

async def validate_tenant_access(tenant_id: str) -> bool:
    """Validar acceso del tenant."""
    return tenant_id in ["default", "cliente_premium", "cliente_basico", "cliente_enterprise"]

async def check_rate_limit(tenant_id: str, channel: ChannelType) -> bool:
    """Verificar rate limit del tenant."""
    config = communications_storage.tenant_configs.get(tenant_id)
    if not config:
        return True  # Sin límites si no hay configuración
    
    rate_limits = config.rate_limits
    channel_limit = rate_limits.get(channel.value, 1000)  # Límite por defecto
    
    # Verificar contador actual
    if tenant_id not in communications_storage.tenant_rate_counters:
        communications_storage.tenant_rate_counters[tenant_id] = {}
    
    current_count = communications_storage.tenant_rate_counters[tenant_id].get(channel.value, 0)
    
    if current_count >= channel_limit:
        return False
    
    # Incrementar contador
    communications_storage.tenant_rate_counters[tenant_id][channel.value] = current_count + 1
    return True

# --- Lifespan management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida del servicio."""
    logger.info("🚀 Communications Service iniciando...")
    
    # Inicializar configuraciones por defecto
    await initialize_default_configs()
    
    # Inicializar templates por defecto
    await initialize_default_templates()
    
    yield
    
    logger.info("🛑 Communications Service cerrando...")

async def initialize_default_configs():
    """Inicializar configuraciones por defecto."""
    default_tenants = ["cliente_premium", "cliente_basico", "cliente_enterprise"]
    
    for tenant_id in default_tenants:
        if tenant_id not in communications_storage.tenant_configs:
            # Configurar límites según el tipo de tenant
            if tenant_id == "cliente_premium":
                rate_limits = {"email": 10000, "sms": 5000, "push": 50000}
            elif tenant_id == "cliente_enterprise":
                rate_limits = {"email": 50000, "sms": 20000, "push": 200000}
            else:  # básico
                rate_limits = {"email": 1000, "sms": 500, "push": 5000}
            
            config = TenantCommunicationsConfig(
                tenant_id=tenant_id,
                name=f"Communications Config for {tenant_id}",
                rate_limits=rate_limits,
                default_sender={
                    "email": f"noreply@{tenant_id}.example.com",
                    "sms": f"{tenant_id.upper()}"
                }
            )
            communications_storage.tenant_configs[tenant_id] = config

async def initialize_default_templates():
    """Inicializar templates por defecto."""
    default_templates = [
        {
            "template_id": "welcome_email",
            "name": "Welcome Email",
            "template_type": TemplateType.WELCOME,
            "channel": ChannelType.EMAIL,
            "subject_template": "¡Bienvenido a {{tenant_name}}!",
            "content_template": "Hola {{user_name}}, bienvenido a nuestra plataforma.",
            "variables": ["tenant_name", "user_name"]
        },
        {
            "template_id": "reset_password",
            "name": "Reset Password",
            "template_type": TemplateType.RESET_PASSWORD,
            "channel": ChannelType.EMAIL,
            "subject_template": "Restablecer contraseña",
            "content_template": "Haz clic aquí para restablecer tu contraseña: {{reset_link}}",
            "variables": ["reset_link"]
        },
        {
            "template_id": "notification_sms",
            "name": "General SMS Notification",
            "template_type": TemplateType.NOTIFICATION,
            "channel": ChannelType.SMS,
            "content_template": "{{message}} - {{tenant_name}}",
            "variables": ["message", "tenant_name"]
        }
    ]
    
    for tenant_id in ["cliente_premium", "cliente_basico", "cliente_enterprise"]:
        templates = communications_storage.get_tenant_templates(tenant_id)
        for template_data in default_templates:
            template = Template(
                tenant_id=tenant_id,
                created_at=datetime.utcnow(),
                **template_data
            )
            templates[template.template_id] = template

# --- FastAPI App ---

app = FastAPI(
    title="Communications Service - Multi-Tenant",
    description="Servicio de comunicaciones con aislamiento completo por tenant",
    version="0.6.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# --- Middleware ---

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"]
)

# --- Endpoints de configuración ---

@app.post("/config/tenant", response_model=TenantCommunicationsConfig)
async def configure_tenant_communications(
    config: TenantCommunicationsConfig,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Configurar comunicaciones para un tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    config.tenant_id = tenant_id
    communications_storage.tenant_configs[tenant_id] = config
    
    logger.info(f"📞 Configuración actualizada para tenant {tenant_id}")
    return config

@app.get("/config/tenant", response_model=TenantCommunicationsConfig)
async def get_tenant_communications_config(
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener configuración de comunicaciones del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    config = communications_storage.tenant_configs.get(tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return config

# --- Endpoints de envío de mensajes ---

@app.post("/messages/send")
async def send_message(
    message: MessageRequest,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Enviar mensaje."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    # Verificar rate limit
    if not await check_rate_limit(tenant_id, message.channel):
        raise HTTPException(status_code=429, detail="Rate limit excedido")
    
    message.tenant_id = tenant_id
    if not message.message_id:
        message.message_id = str(uuid.uuid4())
    
    # Almacenar mensaje
    await communications_storage.store_message(tenant_id, message.dict())
    
    # Procesar envío en background
    background_tasks.add_task(process_message, tenant_id, message)
    
    logger.info(f"📤 Mensaje programado para envío: {message.message_id} para tenant {tenant_id}")
    return {"status": "queued", "message_id": message.message_id}

async def process_message(tenant_id: str, message: MessageRequest):
    """Procesar envío de mensaje."""
    try:
        await communications_storage.update_message_status(tenant_id, message.message_id, MessageStatus.SENDING)
        
        if message.channel == ChannelType.EMAIL:
            email = EmailMessage(
                to=message.recipients,
                subject=message.subject or "Notification",
                html_content=message.content
            )
            success = await email_provider.send_email(tenant_id, email)
        elif message.channel == ChannelType.SMS:
            sms = SMSMessage(
                to=message.recipients,
                content=message.content
            )
            success = await sms_provider.send_sms(tenant_id, sms)
        elif message.channel == ChannelType.PUSH:
            push = PushMessage(
                device_tokens=message.recipients,
                title=message.subject or "Notification",
                body=message.content
            )
            success = await push_provider.send_push(tenant_id, push)
        else:
            success = False
        
        if success:
            await communications_storage.update_message_status(tenant_id, message.message_id, MessageStatus.SENT)
        else:
            await communications_storage.update_message_status(tenant_id, message.message_id, MessageStatus.FAILED)
            
    except Exception as e:
        logger.error(f"Error enviando mensaje {message.message_id}: {e}")
        await communications_storage.update_message_status(tenant_id, message.message_id, MessageStatus.FAILED)

@app.post("/messages/email")
async def send_email(
    email: EmailMessage,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Enviar email específico."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    if not await check_rate_limit(tenant_id, ChannelType.EMAIL):
        raise HTTPException(status_code=429, detail="Rate limit excedido")
    
    message_id = str(uuid.uuid4())
    
    # Almacenar mensaje
    message_data = {
        "message_id": message_id,
        "channel": ChannelType.EMAIL,
        "recipients": email.to,
        "subject": email.subject,
        "content": email.html_content or email.text_content,
        "status": MessageStatus.QUEUED
    }
    await communications_storage.store_message(tenant_id, message_data)
    
    # Enviar en background
    background_tasks.add_task(email_provider.send_email, tenant_id, email)
    background_tasks.add_task(
        communications_storage.update_message_status, 
        tenant_id, 
        message_id, 
        MessageStatus.SENT
    )
    
    return {"status": "queued", "message_id": message_id}

# --- Endpoints de templates ---

@app.post("/templates", response_model=Template)
async def create_template(
    template: Template,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Crear template personalizado."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    template.tenant_id = tenant_id
    template.created_at = datetime.utcnow()
    template.updated_at = datetime.utcnow()
    
    templates = communications_storage.get_tenant_templates(tenant_id)
    templates[template.template_id] = template
    
    logger.info(f"📝 Template creado: {template.name} para tenant {tenant_id}")
    return template

@app.get("/templates", response_model=List[Template])
async def list_templates(
    template_type: Optional[TemplateType] = None,
    channel: Optional[ChannelType] = None,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Listar templates del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    templates = communications_storage.get_tenant_templates(tenant_id)
    result = list(templates.values())
    
    # Filtrar por tipo
    if template_type:
        result = [t for t in result if t.template_type == template_type]
    
    # Filtrar por canal
    if channel:
        result = [t for t in result if t.channel == channel]
    
    return result

@app.get("/templates/{template_id}", response_model=Template)
async def get_template(
    template_id: str,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener template específico."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    templates = communications_storage.get_tenant_templates(tenant_id)
    template = templates.get(template_id)
    
    if not template:
        raise HTTPException(status_code=404, detail="Template no encontrado")
    
    return template

# --- Endpoints de campañas ---

@app.post("/campaigns", response_model=Campaign)
async def create_campaign(
    campaign: Campaign,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Crear campaña de comunicación."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    campaign.tenant_id = tenant_id
    campaign.created_at = datetime.utcnow()
    
    campaigns = communications_storage.get_tenant_campaigns(tenant_id)
    campaigns[campaign.campaign_id] = campaign
    
    logger.info(f"📢 Campaña creada: {campaign.name} para tenant {tenant_id}")
    return campaign

@app.get("/campaigns", response_model=List[Campaign])
async def list_campaigns(
    status: Optional[str] = None,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Listar campañas del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    campaigns = communications_storage.get_tenant_campaigns(tenant_id)
    result = list(campaigns.values())
    
    if status:
        result = [c for c in result if c.status == status]
    
    return result

# --- Endpoints de estadísticas ---

@app.get("/stats/delivery")
async def get_delivery_stats(
    channel: Optional[ChannelType] = None,
    days: int = Query(7, ge=1, le=90),
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener estadísticas de entrega."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    messages = communications_storage.get_tenant_messages(tenant_id)
    
    # Filtrar por canal si se especifica
    if channel:
        messages = [m for m in messages if m.get("channel") == channel]
    
    # Filtrar por fecha
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    recent_messages = [
        m for m in messages 
        if datetime.fromisoformat(m.get("created_at", "1970-01-01T00:00:00")) >= cutoff_date
    ]
    
    # Calcular estadísticas
    total_messages = len(recent_messages)
    sent_messages = len([m for m in recent_messages if m.get("status") == MessageStatus.SENT])
    failed_messages = len([m for m in recent_messages if m.get("status") == MessageStatus.FAILED])
    
    # Estadísticas por canal
    channel_stats = {}
    for message in recent_messages:
        ch = message.get("channel", "unknown")
        if ch not in channel_stats:
            channel_stats[ch] = {"total": 0, "sent": 0, "failed": 0}
        channel_stats[ch]["total"] += 1
        if message.get("status") == MessageStatus.SENT:
            channel_stats[ch]["sent"] += 1
        elif message.get("status") == MessageStatus.FAILED:
            channel_stats[ch]["failed"] += 1
    
    return {
        "tenant_id": tenant_id,
        "period_days": days,
        "total_messages": total_messages,
        "sent_messages": sent_messages,
        "failed_messages": failed_messages,
        "success_rate": sent_messages / total_messages if total_messages > 0 else 0,
        "channel_stats": channel_stats,
        "timestamp": datetime.utcnow().isoformat()
    }

@app.get("/stats/rate-limits")
async def get_rate_limit_stats(
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener estadísticas de rate limits."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    config = communications_storage.tenant_configs.get(tenant_id)
    current_usage = communications_storage.tenant_rate_counters.get(tenant_id, {})
    
    rate_limits = config.rate_limits if config else {}
    
    stats = {}
    for channel, limit in rate_limits.items():
        used = current_usage.get(channel, 0)
        stats[channel] = {
            "limit": limit,
            "used": used,
            "remaining": limit - used,
            "percentage_used": (used / limit * 100) if limit > 0 else 0
        }
    
    return {
        "tenant_id": tenant_id,
        "rate_limit_stats": stats,
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Health check ---

@app.get("/health")
async def health_check():
    """Health check del servicio."""
    return {
        "status": "healthy",
        "service": "communications-mt",
        "version": "0.6.0",
        "timestamp": datetime.utcnow().isoformat(),
        "tenants_configured": len(communications_storage.tenant_configs),
        "total_messages": sum(len(messages) for messages in communications_storage.tenant_messages.values())
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    ) 