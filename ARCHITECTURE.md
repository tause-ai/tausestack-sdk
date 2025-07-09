# TauseStack Architecture - Single Source of Truth

## 🎯 **MISSION STATEMENT**
TauseStack is an MCP-native, multi-tenant framework that serves as backend for tause.pro and enables external developers to build on our infrastructure.

## 🏗️ **CORE ARCHITECTURE PRINCIPLES**

### **1. MCP-First Everything**
- ✅ **MCP Server**: Expose ALL TauseStack capabilities as MCP tools
- ✅ **MCP Client**: Consume external MCP servers for extensibility  
- ✅ **Agent Framework**: MCP-based agent orchestration
- ❌ **Never**: Build functionality without MCP exposure

### **2. Multi-Tenant by Default**
- ✅ **tenant_id**: Required in ALL operations
- ✅ **Data Isolation**: Complete separation between tenants
- ✅ **Configuration**: Per-tenant settings and limits
- ❌ **Never**: Single-tenant operations or shared data

### **3. Backwards Compatibility**
- ✅ **API Versioning**: /api/v1/, /api/v2/
- ✅ **Existing Endpoints**: Must continue working
- ✅ **Migration Paths**: For breaking changes
- ❌ **Never**: Break existing integrations

## 📁 **PROJECT STRUCTURE (DO NOT MODIFY)**

```
/tausestack/
├── services/           # ✅ EXTEND ONLY, never rewrite
│   ├── analytics/      # ✅ Working - has examples
│   ├── ai_services/    # ✅ Working - has examples  
│   ├── auth/          # ✅ Working - core functionality
│   ├── billing/       # ✅ Working - has examples
│   ├── communications/# ✅ Working - has examples
│   └── mcp/           # 🔄 NEW - to be implemented
├── sdk/               # ✅ EXTEND ONLY
│   ├── python/        # ✅ Working SDK
│   ├── external/      # ✅ Working external SDK
│   └── ai/           # ✅ Working AI SDK
├── examples/          # ⚠️ CRITICAL - NEVER BREAK
│   ├── ai_integration_demo.py      # ✅ Must keep working
│   ├── multitenant_services_demo.py # ✅ Must keep working
│   └── tausepro_integration_demo.py # ✅ Must keep working
└── admin/             # ✅ Existing UI - extend only
```

## 🛠️ **ESTABLISHED PATTERNS (FOLLOW ALWAYS)**

### **Service Pattern**
```python
# ✅ CORRECT: All services follow this pattern
class ServiceName:
    def __init__(self, tenant_id: str):
        self.tenant_id = tenant_id
        # Per-tenant initialization
    
    async def operation(self, data: dict) -> dict:
        # Always validate tenant
        # Always log for analytics
        # Always handle errors consistently
        pass
```

### **API Pattern**  
```python
# ✅ CORRECT: All APIs follow this pattern
@app.post("/api/v1/service/{tenant_id}/operation")
async def service_operation(
    tenant_id: str,
    data: ServiceModel,
    current_user: User = Depends(get_current_user)
):
    # Validate tenant access
    # Execute operation
    # Track analytics
    # Return standardized response
    pass
```

### **MCP Tool Pattern**
```python
# ✅ CORRECT: How to expose functionality as MCP tool
@ts.mcp.tool("service/operation")
async def service_operation_tool(
    tenant_id: str,
    params: dict
) -> dict:
    service = ServiceName(tenant_id)
    return await service.operation(params)
```

## 🇨🇴 **COLOMBIA MODULE (CRITICAL - DO NOT BREAK)**

```python
# ✅ WORKING: These functions are in production
ts.colombia.validate_cedula(cedula: str) -> bool
ts.colombia.validate_nit(nit: str) -> bool  
ts.colombia.get_departamentos() -> List[dict]
ts.colombia.get_municipios(dept_code: str) -> List[dict]
ts.payments.create_wompi_payment(...)
ts.payments.create_pse_payment(...)
```

## 📊 **EXISTING SERVICES (EXTEND, DON'T REWRITE)**

### **Analytics Service** ✅ Working
- Multi-tenant event tracking
- Dashboard data aggregation
- Real-time metrics
- **Examples**: `examples/multitenant_services_demo.py`

### **AI Services** ✅ Working  
- OpenAI + Anthropic integration
- Code generation capabilities
- Multi-provider orchestration
- **Examples**: `examples/ai_integration_demo.py`

### **Communications** ✅ Working
- Email, SMS, push notifications
- Template management
- Campaign tracking
- **Examples**: `examples/multitenant_services_demo.py`

### **Auth Service** ✅ Working
- Multi-tenant authentication
- Role-based access control
- API key management

### **Storage Service** ✅ Working
- JSON, binary, dataframe storage
- Multi-backend support (local, S3, etc.)
- Per-tenant isolation

## 🎯 **IMPLEMENTATION PRIORITIES**

### **P0 (Critical) - MCP Implementation**
1. **MCP Server**: Expose existing services as MCP tools
2. **MCP Client**: Connect to external MCP servers
3. **MCP Registry**: Marketplace for MCP tools
4. **Agent Framework**: MCP-based orchestration

### **P1 (High) - Framework Enhancement**  
1. **SDK Improvements**: Better developer experience
2. **Plugin System**: Extensibility for tause.pro
3. **Documentation**: Comprehensive guides and examples

### **P2 (Medium) - Admin Enhancement**
1. **MCP Dashboard**: Visualize MCP tools and connections
2. **Developer Portal**: External developer onboarding
3. **Marketplace UI**: Plugin and tool management

## ❌ **NEVER DO (CRITICAL CONSTRAINTS)**

### **Code Changes**
- ❌ Rewrite existing working services
- ❌ Break existing API endpoints
- ❌ Modify working examples without testing
- ❌ Remove tenant_id from any operation
- ❌ Create single-tenant functionality

### **Architecture Changes**
- ❌ Change established patterns without ADR
- ❌ Remove multi-tenant support
- ❌ Break MCP-first principle
- ❌ Ignore backwards compatibility

### **Data Changes**
- ❌ Modify database schemas without migration
- ❌ Remove tenant isolation
- ❌ Break existing data contracts

## 🧪 **TESTING REQUIREMENTS**

### **Before ANY Changes**
```bash
# These MUST pass after every change
python -m pytest tests/
python examples/ai_integration_demo.py
python examples/multitenant_services_demo.py
python examples/tausepro_integration_demo.py
```

### **Integration Tests**
- All services must maintain API contracts
- Examples must continue working
- Multi-tenant isolation must be verified

## 📝 **DEVELOPMENT WORKFLOW**

### **1. Small, Incremental Changes**
- Make smallest possible changes
- Test immediately
- Verify examples still work

### **2. Add, Don't Replace**
- Extend existing functionality
- Add new capabilities alongside old ones
- Deprecate gracefully with migration paths

### **3. Documentation-Driven**
- Update this file with major changes
- Document new patterns as you establish them
- Keep examples current

## 🔄 **CHANGE MANAGEMENT**

### **Architecture Decision Records (ADRs)**
Document major decisions in `/docs/adrs/`:
- ADR-001: MCP-First Architecture
- ADR-002: Multi-Tenant Design
- ADR-003: Plugin System Design

### **Migration Strategy**
For breaking changes:
1. Add new functionality alongside old
2. Provide migration tools
3. Deprecate with clear timeline
4. Remove only after migration period

---

## 🎯 **REMEMBER: THIS IS A FRAMEWORK**

TauseStack is infrastructure that others build upon. Breaking changes hurt:
- ✅ **tause.pro** (our main product)
- ✅ **ai.tause.pro** (our chat agents platform)  
- ✅ **External developers** (building on our framework)
- ✅ **Plugin developers** (extending our ecosystem)

**Every change must consider all these stakeholders.**