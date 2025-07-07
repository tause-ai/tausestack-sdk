#!/usr/bin/env python3
"""
Billing Service - Multi-Tenant API
TauseStack v0.5.0

Servicio de facturación con aislamiento completo por tenant.
Implementa:
- Subscription management por tenant
- Usage tracking y metering
- Billing cycles automatizados
- Payment processing
- Invoice generation
- Usage-based pricing
- Tier management
- Webhook notifications
"""

from fastapi import FastAPI, HTTPException, Header, Query, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from pydantic import BaseModel, Field, validator
from typing import Dict, Any, List, Optional, Union
from datetime import datetime, timedelta
from enum import Enum
from decimal import Decimal
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
logger = logging.getLogger("billing-service")

# --- Modelos de datos ---

class SubscriptionStatus(str, Enum):
    """Estados de suscripción."""
    ACTIVE = "active"
    INACTIVE = "inactive"
    SUSPENDED = "suspended"
    CANCELLED = "cancelled"
    EXPIRED = "expired"
    TRIAL = "trial"

class BillingCycle(str, Enum):
    """Ciclos de facturación."""
    MONTHLY = "monthly"
    QUARTERLY = "quarterly"
    YEARLY = "yearly"
    USAGE_BASED = "usage_based"

class PaymentStatus(str, Enum):
    """Estados de pago."""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"
    REFUNDED = "refunded"
    PARTIAL = "partial"

class UsageMetric(str, Enum):
    """Métricas de uso."""
    API_CALLS = "api_calls"
    STORAGE_GB = "storage_gb"
    BANDWIDTH_GB = "bandwidth_gb"
    USERS = "users"
    EVENTS = "events"
    MESSAGES = "messages"
    COMPUTE_HOURS = "compute_hours"

class PlanTier(str, Enum):
    """Tiers de planes."""
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"
    CUSTOM = "custom"

class Plan(BaseModel):
    """Plan de suscripción."""
    plan_id: str
    name: str
    description: Optional[str] = None
    tier: PlanTier
    base_price: Decimal = Field(default=Decimal("0.00"))
    billing_cycle: BillingCycle
    features: List[str] = Field(default_factory=list)
    limits: Dict[str, int] = Field(default_factory=dict)
    usage_pricing: Dict[str, Decimal] = Field(default_factory=dict)  # precio por unidad de uso
    is_active: bool = Field(default=True)
    created_at: Optional[datetime] = None

class Subscription(BaseModel):
    """Suscripción de tenant."""
    subscription_id: str
    tenant_id: str
    plan_id: str
    status: SubscriptionStatus
    start_date: datetime
    end_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    current_period_start: datetime
    current_period_end: datetime
    auto_renew: bool = Field(default=True)
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

class UsageRecord(BaseModel):
    """Registro de uso."""
    usage_id: Optional[str] = None
    tenant_id: str
    subscription_id: str
    metric: UsageMetric
    quantity: int
    unit_price: Optional[Decimal] = None
    timestamp: datetime
    metadata: Dict[str, Any] = Field(default_factory=dict)

class Invoice(BaseModel):
    """Factura."""
    invoice_id: str
    tenant_id: str
    subscription_id: str
    invoice_number: str
    amount: Decimal
    tax_amount: Decimal = Field(default=Decimal("0.00"))
    total_amount: Decimal
    currency: str = Field(default="USD")
    billing_period_start: datetime
    billing_period_end: datetime
    due_date: datetime
    status: PaymentStatus = PaymentStatus.PENDING
    line_items: List[Dict[str, Any]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    paid_at: Optional[datetime] = None

class Payment(BaseModel):
    """Pago."""
    payment_id: str
    tenant_id: str
    invoice_id: str
    amount: Decimal
    currency: str = Field(default="USD")
    payment_method: str
    status: PaymentStatus
    transaction_id: Optional[str] = None
    processed_at: Optional[datetime] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)

class TenantBillingConfig(BaseModel):
    """Configuración de facturación por tenant."""
    tenant_id: str
    company_name: str
    billing_email: str
    payment_method_id: Optional[str] = None
    tax_id: Optional[str] = None
    billing_address: Dict[str, str] = Field(default_factory=dict)
    currency: str = Field(default="USD")
    auto_pay: bool = Field(default=True)
    usage_alerts: Dict[str, int] = Field(default_factory=dict)  # alertas por métrica
    created_at: Optional[datetime] = None

class UsageAlert(BaseModel):
    """Alerta de uso."""
    alert_id: str
    tenant_id: str
    metric: UsageMetric
    threshold: int
    current_usage: int
    percentage: float
    triggered_at: datetime
    is_resolved: bool = Field(default=False)

# --- Storage multi-tenant simulado ---

class TenantBillingStorage:
    """Storage de billing aislado por tenant."""
    
    def __init__(self):
        self.plans: Dict[str, Plan] = {}
        self.tenant_subscriptions: Dict[str, List[Subscription]] = {}
        self.tenant_usage: Dict[str, List[UsageRecord]] = {}
        self.tenant_invoices: Dict[str, List[Invoice]] = {}
        self.tenant_payments: Dict[str, List[Payment]] = {}
        self.tenant_configs: Dict[str, TenantBillingConfig] = {}
        self.tenant_alerts: Dict[str, List[UsageAlert]] = {}
    
    def get_tenant_subscriptions(self, tenant_id: str) -> List[Subscription]:
        """Obtener suscripciones del tenant."""
        return self.tenant_subscriptions.get(tenant_id, [])
    
    def get_tenant_usage(self, tenant_id: str) -> List[UsageRecord]:
        """Obtener registros de uso del tenant."""
        return self.tenant_usage.get(tenant_id, [])
    
    def get_tenant_invoices(self, tenant_id: str) -> List[Invoice]:
        """Obtener facturas del tenant."""
        return self.tenant_invoices.get(tenant_id, [])
    
    async def add_usage_record(self, tenant_id: str, usage: UsageRecord) -> str:
        """Agregar registro de uso."""
        if tenant_id not in self.tenant_usage:
            self.tenant_usage[tenant_id] = []
        
        usage.usage_id = str(uuid.uuid4())
        self.tenant_usage[tenant_id].append(usage)
        
        # Verificar alertas de uso
        await self._check_usage_alerts(tenant_id, usage.metric)
        
        return usage.usage_id
    
    async def _check_usage_alerts(self, tenant_id: str, metric: UsageMetric):
        """Verificar alertas de uso."""
        config = self.tenant_configs.get(tenant_id)
        if not config or metric.value not in config.usage_alerts:
            return
        
        threshold = config.usage_alerts[metric.value]
        
        # Calcular uso actual del mes
        now = datetime.utcnow()
        month_start = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        
        usage_records = self.get_tenant_usage(tenant_id)
        current_usage = sum(
            record.quantity for record in usage_records
            if record.metric == metric and record.timestamp >= month_start
        )
        
        percentage = (current_usage / threshold * 100) if threshold > 0 else 0
        
        # Crear alerta si se supera el 80%
        if percentage >= 80:
            alert = UsageAlert(
                alert_id=str(uuid.uuid4()),
                tenant_id=tenant_id,
                metric=metric,
                threshold=threshold,
                current_usage=current_usage,
                percentage=percentage,
                triggered_at=now
            )
            
            if tenant_id not in self.tenant_alerts:
                self.tenant_alerts[tenant_id] = []
            self.tenant_alerts[tenant_id].append(alert)
            
            logger.warning(f"🚨 Alerta de uso para {tenant_id}: {metric.value} al {percentage:.1f}%")

# Storage global
billing_storage = TenantBillingStorage()

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

def calculate_usage_cost(usage_records: List[UsageRecord], plan: Plan) -> Decimal:
    """Calcular costo basado en uso."""
    total_cost = Decimal("0.00")
    
    for record in usage_records:
        metric_price = plan.usage_pricing.get(record.metric.value, Decimal("0.00"))
        cost = Decimal(str(record.quantity)) * metric_price
        total_cost += cost
    
    return total_cost

# --- Lifespan management ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestión del ciclo de vida del servicio."""
    logger.info("🚀 Billing Service iniciando...")
    
    # Inicializar planes por defecto
    await initialize_default_plans()
    
    # Inicializar configuraciones por defecto
    await initialize_default_configs()
    
    # Inicializar suscripciones por defecto
    await initialize_default_subscriptions()
    
    yield
    
    logger.info("🛑 Billing Service cerrando...")

async def initialize_default_plans():
    """Inicializar planes por defecto."""
    plans = [
        Plan(
            plan_id="basic_monthly",
            name="Plan Básico Mensual",
            tier=PlanTier.BASIC,
            base_price=Decimal("29.99"),
            billing_cycle=BillingCycle.MONTHLY,
            features=["5,000 API calls/mes", "1GB storage", "Email support"],
            limits={"api_calls": 5000, "storage_gb": 1, "users": 5},
            usage_pricing={
                "api_calls": Decimal("0.001"),
                "storage_gb": Decimal("0.50"),
                "messages": Decimal("0.01")
            },
            created_at=datetime.utcnow()
        ),
        Plan(
            plan_id="premium_monthly",
            name="Plan Premium Mensual",
            tier=PlanTier.PREMIUM,
            base_price=Decimal("99.99"),
            billing_cycle=BillingCycle.MONTHLY,
            features=["50,000 API calls/mes", "10GB storage", "Priority support", "Analytics"],
            limits={"api_calls": 50000, "storage_gb": 10, "users": 25},
            usage_pricing={
                "api_calls": Decimal("0.0008"),
                "storage_gb": Decimal("0.40"),
                "messages": Decimal("0.008")
            },
            created_at=datetime.utcnow()
        ),
        Plan(
            plan_id="enterprise_monthly",
            name="Plan Enterprise Mensual",
            tier=PlanTier.ENTERPRISE,
            base_price=Decimal("499.99"),
            billing_cycle=BillingCycle.MONTHLY,
            features=["Unlimited API calls", "100GB storage", "24/7 support", "Advanced analytics", "Custom integrations"],
            limits={"api_calls": -1, "storage_gb": 100, "users": -1},  # -1 = unlimited
            usage_pricing={
                "api_calls": Decimal("0.0005"),
                "storage_gb": Decimal("0.30"),
                "messages": Decimal("0.005")
            },
            created_at=datetime.utcnow()
        )
    ]
    
    for plan in plans:
        billing_storage.plans[plan.plan_id] = plan

async def initialize_default_configs():
    """Inicializar configuraciones por defecto."""
    configs = [
        TenantBillingConfig(
            tenant_id="cliente_basico",
            company_name="Cliente Básico S.L.",
            billing_email="billing@basico.com",
            currency="EUR",
            usage_alerts={"api_calls": 4000, "storage_gb": 1, "messages": 1000},
            created_at=datetime.utcnow()
        ),
        TenantBillingConfig(
            tenant_id="cliente_premium",
            company_name="Premium Corp",
            billing_email="billing@premium.com",
            currency="USD",
            usage_alerts={"api_calls": 40000, "storage_gb": 8, "messages": 5000},
            created_at=datetime.utcnow()
        ),
        TenantBillingConfig(
            tenant_id="cliente_enterprise",
            company_name="Enterprise Solutions Inc.",
            billing_email="billing@enterprise.com",
            currency="USD",
            usage_alerts={"storage_gb": 80, "messages": 20000},
            created_at=datetime.utcnow()
        )
    ]
    
    for config in configs:
        billing_storage.tenant_configs[config.tenant_id] = config

async def initialize_default_subscriptions():
    """Inicializar suscripciones por defecto."""
    now = datetime.utcnow()
    
    subscriptions = [
        Subscription(
            subscription_id="sub_basico_001",
            tenant_id="cliente_basico",
            plan_id="basic_monthly",
            status=SubscriptionStatus.ACTIVE,
            start_date=now - timedelta(days=15),
            current_period_start=now - timedelta(days=15),
            current_period_end=now + timedelta(days=15),
            created_at=now - timedelta(days=15)
        ),
        Subscription(
            subscription_id="sub_premium_001",
            tenant_id="cliente_premium",
            plan_id="premium_monthly",
            status=SubscriptionStatus.ACTIVE,
            start_date=now - timedelta(days=20),
            current_period_start=now - timedelta(days=20),
            current_period_end=now + timedelta(days=10),
            created_at=now - timedelta(days=20)
        ),
        Subscription(
            subscription_id="sub_enterprise_001",
            tenant_id="cliente_enterprise",
            plan_id="enterprise_monthly",
            status=SubscriptionStatus.ACTIVE,
            start_date=now - timedelta(days=25),
            current_period_start=now - timedelta(days=25),
            current_period_end=now + timedelta(days=5),
            created_at=now - timedelta(days=25)
        )
    ]
    
    for subscription in subscriptions:
        if subscription.tenant_id not in billing_storage.tenant_subscriptions:
            billing_storage.tenant_subscriptions[subscription.tenant_id] = []
        billing_storage.tenant_subscriptions[subscription.tenant_id].append(subscription)

# --- FastAPI App ---

app = FastAPI(
    title="Billing Service - Multi-Tenant",
    description="Servicio de facturación con aislamiento completo por tenant",
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

# --- Endpoints de planes ---

@app.get("/plans", response_model=List[Plan])
async def list_plans(
    tier: Optional[PlanTier] = None,
    billing_cycle: Optional[BillingCycle] = None
):
    """Listar planes disponibles."""
    plans = list(billing_storage.plans.values())
    
    if tier:
        plans = [p for p in plans if p.tier == tier]
    
    if billing_cycle:
        plans = [p for p in plans if p.billing_cycle == billing_cycle]
    
    return [p for p in plans if p.is_active]

@app.get("/plans/{plan_id}", response_model=Plan)
async def get_plan(plan_id: str):
    """Obtener plan específico."""
    plan = billing_storage.plans.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    return plan

# --- Endpoints de suscripciones ---

@app.post("/subscriptions", response_model=Subscription)
async def create_subscription(
    plan_id: str,
    trial_days: Optional[int] = None,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Crear nueva suscripción."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    # Verificar que el plan existe
    plan = billing_storage.plans.get(plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    now = datetime.utcnow()
    
    # Crear suscripción
    subscription = Subscription(
        subscription_id=f"sub_{tenant_id}_{str(uuid.uuid4())[:8]}",
        tenant_id=tenant_id,
        plan_id=plan_id,
        status=SubscriptionStatus.TRIAL if trial_days else SubscriptionStatus.ACTIVE,
        start_date=now,
        trial_end_date=now + timedelta(days=trial_days) if trial_days else None,
        current_period_start=now,
        current_period_end=now + timedelta(days=30),  # Mensual por defecto
        created_at=now
    )
    
    # Almacenar suscripción
    if tenant_id not in billing_storage.tenant_subscriptions:
        billing_storage.tenant_subscriptions[tenant_id] = []
    billing_storage.tenant_subscriptions[tenant_id].append(subscription)
    
    logger.info(f"💳 Suscripción creada: {subscription.subscription_id} para tenant {tenant_id}")
    return subscription

@app.get("/subscriptions", response_model=List[Subscription])
async def list_subscriptions(
    status: Optional[SubscriptionStatus] = None,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Listar suscripciones del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    subscriptions = billing_storage.get_tenant_subscriptions(tenant_id)
    
    if status:
        subscriptions = [s for s in subscriptions if s.status == status]
    
    return subscriptions

@app.get("/subscriptions/{subscription_id}", response_model=Subscription)
async def get_subscription(
    subscription_id: str,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener suscripción específica."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    subscriptions = billing_storage.get_tenant_subscriptions(tenant_id)
    subscription = next((s for s in subscriptions if s.subscription_id == subscription_id), None)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    
    return subscription

# --- Endpoints de uso ---

@app.post("/usage/record")
async def record_usage(
    usage: UsageRecord,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Registrar uso de recursos."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    usage.tenant_id = tenant_id
    usage.timestamp = datetime.utcnow()
    
    # Verificar que la suscripción existe
    subscriptions = billing_storage.get_tenant_subscriptions(tenant_id)
    subscription = next((s for s in subscriptions if s.subscription_id == usage.subscription_id), None)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    
    # Obtener precio unitario del plan
    plan = billing_storage.plans.get(subscription.plan_id)
    if plan:
        usage.unit_price = plan.usage_pricing.get(usage.metric.value, Decimal("0.00"))
    
    # Registrar uso
    usage_id = await billing_storage.add_usage_record(tenant_id, usage)
    
    logger.info(f"📊 Uso registrado: {usage.metric.value} = {usage.quantity} para tenant {tenant_id}")
    return {"status": "recorded", "usage_id": usage_id}

@app.get("/usage/summary")
async def get_usage_summary(
    subscription_id: Optional[str] = None,
    metric: Optional[UsageMetric] = None,
    days: int = Query(30, ge=1, le=365),
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener resumen de uso."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    usage_records = billing_storage.get_tenant_usage(tenant_id)
    
    # Filtrar por suscripción
    if subscription_id:
        usage_records = [u for u in usage_records if u.subscription_id == subscription_id]
    
    # Filtrar por métrica
    if metric:
        usage_records = [u for u in usage_records if u.metric == metric]
    
    # Filtrar por fecha
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    usage_records = [u for u in usage_records if u.timestamp >= cutoff_date]
    
    # Calcular resumen
    summary = {}
    total_cost = Decimal("0.00")
    
    for record in usage_records:
        metric_name = record.metric.value
        if metric_name not in summary:
            summary[metric_name] = {
                "total_quantity": 0,
                "total_cost": Decimal("0.00"),
                "unit_price": record.unit_price or Decimal("0.00")
            }
        
        summary[metric_name]["total_quantity"] += record.quantity
        if record.unit_price:
            cost = Decimal(str(record.quantity)) * record.unit_price
            summary[metric_name]["total_cost"] += cost
            total_cost += cost
    
    return {
        "tenant_id": tenant_id,
        "period_days": days,
        "total_records": len(usage_records),
        "total_cost": total_cost,
        "metrics": summary,
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Endpoints de facturación ---

@app.post("/invoices/generate")
async def generate_invoice(
    subscription_id: str,
    background_tasks: BackgroundTasks,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Generar factura para suscripción."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    # Verificar suscripción
    subscriptions = billing_storage.get_tenant_subscriptions(tenant_id)
    subscription = next((s for s in subscriptions if s.subscription_id == subscription_id), None)
    
    if not subscription:
        raise HTTPException(status_code=404, detail="Suscripción no encontrada")
    
    # Obtener plan
    plan = billing_storage.plans.get(subscription.plan_id)
    if not plan:
        raise HTTPException(status_code=404, detail="Plan no encontrado")
    
    # Calcular período de facturación
    period_start = subscription.current_period_start
    period_end = subscription.current_period_end
    
    # Obtener uso del período
    usage_records = [
        u for u in billing_storage.get_tenant_usage(tenant_id)
        if u.subscription_id == subscription_id and period_start <= u.timestamp <= period_end
    ]
    
    # Calcular costos
    base_amount = plan.base_price
    usage_cost = calculate_usage_cost(usage_records, plan)
    subtotal = base_amount + usage_cost
    tax_amount = subtotal * Decimal("0.10")  # 10% tax simulado
    total_amount = subtotal + tax_amount
    
    # Crear factura
    invoice = Invoice(
        invoice_id=f"inv_{tenant_id}_{str(uuid.uuid4())[:8]}",
        tenant_id=tenant_id,
        subscription_id=subscription_id,
        invoice_number=f"INV-{datetime.utcnow().strftime('%Y%m%d')}-{len(billing_storage.get_tenant_invoices(tenant_id)) + 1:04d}",
        amount=subtotal,
        tax_amount=tax_amount,
        total_amount=total_amount,
        billing_period_start=period_start,
        billing_period_end=period_end,
        due_date=datetime.utcnow() + timedelta(days=30),
        line_items=[
            {"description": f"Plan {plan.name}", "amount": float(base_amount)},
            {"description": "Uso adicional", "amount": float(usage_cost)}
        ],
        created_at=datetime.utcnow()
    )
    
    # Almacenar factura
    if tenant_id not in billing_storage.tenant_invoices:
        billing_storage.tenant_invoices[tenant_id] = []
    billing_storage.tenant_invoices[tenant_id].append(invoice)
    
    # Procesar pago automático si está configurado
    config = billing_storage.tenant_configs.get(tenant_id)
    if config and config.auto_pay:
        background_tasks.add_task(process_automatic_payment, tenant_id, invoice.invoice_id)
    
    logger.info(f"🧾 Factura generada: {invoice.invoice_number} para tenant {tenant_id}")
    return invoice

async def process_automatic_payment(tenant_id: str, invoice_id: str):
    """Procesar pago automático."""
    await asyncio.sleep(2)  # Simular procesamiento
    
    invoices = billing_storage.get_tenant_invoices(tenant_id)
    invoice = next((i for i in invoices if i.invoice_id == invoice_id), None)
    
    if invoice:
        # Simular pago exitoso
        payment = Payment(
            payment_id=f"pay_{str(uuid.uuid4())[:8]}",
            tenant_id=tenant_id,
            invoice_id=invoice_id,
            amount=invoice.total_amount,
            payment_method="auto_charge",
            status=PaymentStatus.PAID,
            processed_at=datetime.utcnow(),
            metadata={"auto_processed": True}
        )
        
        # Almacenar pago
        if tenant_id not in billing_storage.tenant_payments:
            billing_storage.tenant_payments[tenant_id] = []
        billing_storage.tenant_payments[tenant_id].append(payment)
        
        # Actualizar factura
        invoice.status = PaymentStatus.PAID
        invoice.paid_at = datetime.utcnow()
        
        logger.info(f"💳 Pago automático procesado: {payment.payment_id} para tenant {tenant_id}")

@app.get("/invoices", response_model=List[Invoice])
async def list_invoices(
    status: Optional[PaymentStatus] = None,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Listar facturas del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    invoices = billing_storage.get_tenant_invoices(tenant_id)
    
    if status:
        invoices = [i for i in invoices if i.status == status]
    
    return invoices

# --- Endpoints de alertas ---

@app.get("/alerts/usage")
async def get_usage_alerts(
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener alertas de uso."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    alerts = billing_storage.tenant_alerts.get(tenant_id, [])
    active_alerts = [a for a in alerts if not a.is_resolved]
    
    return {
        "tenant_id": tenant_id,
        "active_alerts": len(active_alerts),
        "total_alerts": len(alerts),
        "alerts": active_alerts,
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Endpoints de configuración ---

@app.post("/config/tenant", response_model=TenantBillingConfig)
async def configure_tenant_billing(
    config: TenantBillingConfig,
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Configurar billing para un tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    config.tenant_id = tenant_id
    billing_storage.tenant_configs[tenant_id] = config
    
    logger.info(f"💰 Configuración de billing actualizada para tenant {tenant_id}")
    return config

@app.get("/config/tenant", response_model=TenantBillingConfig)
async def get_tenant_billing_config(
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener configuración de billing del tenant."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    config = billing_storage.tenant_configs.get(tenant_id)
    if not config:
        raise HTTPException(status_code=404, detail="Configuración no encontrada")
    
    return config

# --- Endpoints de estadísticas ---

@app.get("/stats/revenue")
async def get_revenue_stats(
    days: int = Query(30, ge=1, le=365),
    tenant_id: str = Depends(get_tenant_id_from_request)
):
    """Obtener estadísticas de ingresos."""
    if not await validate_tenant_access(tenant_id):
        raise HTTPException(status_code=403, detail="Acceso denegado al tenant")
    
    invoices = billing_storage.get_tenant_invoices(tenant_id)
    payments = billing_storage.tenant_payments.get(tenant_id, [])
    
    # Filtrar por fecha
    cutoff_date = datetime.utcnow() - timedelta(days=days)
    recent_invoices = [i for i in invoices if i.created_at and i.created_at >= cutoff_date]
    recent_payments = [p for p in payments if p.processed_at and p.processed_at >= cutoff_date]
    
    # Calcular estadísticas
    total_invoiced = sum(i.total_amount for i in recent_invoices)
    total_paid = sum(p.amount for p in recent_payments if p.status == PaymentStatus.PAID)
    outstanding = sum(i.total_amount for i in recent_invoices if i.status == PaymentStatus.PENDING)
    
    return {
        "tenant_id": tenant_id,
        "period_days": days,
        "total_invoiced": total_invoiced,
        "total_paid": total_paid,
        "outstanding_amount": outstanding,
        "payment_rate": float(total_paid / total_invoiced) if total_invoiced > 0 else 0,
        "invoices_count": len(recent_invoices),
        "payments_count": len(recent_payments),
        "timestamp": datetime.utcnow().isoformat()
    }

# --- Health check ---

@app.get("/health")
async def health_check():
    """Health check del servicio."""
    total_subscriptions = sum(len(subs) for subs in billing_storage.tenant_subscriptions.values())
    total_invoices = sum(len(invs) for invs in billing_storage.tenant_invoices.values())
    
    return {
        "status": "healthy",
        "service": "billing-mt",
        "version": "0.6.0",
        "timestamp": datetime.utcnow().isoformat(),
        "tenants_configured": len(billing_storage.tenant_configs),
        "total_subscriptions": total_subscriptions,
        "total_invoices": total_invoices,
        "available_plans": len(billing_storage.plans)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8003,
        reload=True,
        log_level="info"
    ) 