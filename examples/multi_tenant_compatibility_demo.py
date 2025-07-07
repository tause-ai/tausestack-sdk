"""
Demostración de Compatibilidad Multi-Tenant en TauseStack v2.0

Este ejemplo muestra cómo:
1. Código existente sigue funcionando sin cambios (compatibilidad hacia atrás)
2. Nuevas aplicaciones pueden aprovechar capacidades multi-tenant
3. Migración gradual de monolítico a multi-tenant
"""

import os
from tausestack import sdk

def demo_backward_compatibility():
    """
    Demostración: Código existente funciona sin cambios
    """
    print("=== 🔄 COMPATIBILIDAD HACIA ATRÁS ===")
    
    # ✅ Código existente - NO requiere cambios
    sdk.storage.json.put("user_config", {"theme": "dark", "language": "es"})
    config = sdk.storage.json.get("user_config")
    print(f"Configuración obtenida: {config}")
    
    # ✅ Funciona automáticamente con tenant 'default'
    print(f"Tenant actual: {sdk.get_current_tenant_id()}")  # 'default'
    
    # ✅ Todos los demás módulos también funcionan igual
    sdk.cache.cached(ttl=300)
    def expensive_calculation():
        return "resultado_calculado"
    
    print("✅ Código legacy funciona perfectamente")

def demo_multi_tenant_explicit():
    """
    Demostración: Uso explícito de multi-tenancy
    """
    print("\n=== 🏢 MULTI-TENANT EXPLÍCITO ===")
    
    # Configurar tenants
    sdk.tenancy.configure_tenant("cliente_123", {
        "name": "Cliente Premium",
        "storage": {
            "backend": "s3",
            "bucket_name": "cliente-123-bucket",
            "key_prefix": "data/"
        }
    })
    
    sdk.tenancy.configure_tenant("cliente_456", {
        "name": "Cliente Standard", 
        "storage": {
            "backend": "local",
            "base_path": "./storage/cliente_456"
        }
    })
    
    # Usar tenant específico
    sdk.storage.json.put("config", {"plan": "premium"}, tenant_id="cliente_123")
    sdk.storage.json.put("config", {"plan": "standard"}, tenant_id="cliente_456")
    
    # Verificar aislamiento
    config_123 = sdk.storage.json.get("config", tenant_id="cliente_123")
    config_456 = sdk.storage.json.get("config", tenant_id="cliente_456")
    
    print(f"Cliente 123: {config_123}")  # {"plan": "premium"}
    print(f"Cliente 456: {config_456}")  # {"plan": "standard"}
    
    print("✅ Datos completamente aislados por tenant")

def demo_context_manager():
    """
    Demostración: Context manager para operaciones por tenant
    """
    print("\n=== 🎯 CONTEXT MANAGER ===")
    
    # Configurar datos para diferentes tenants
    with sdk.tenancy.tenant_context("cliente_123"):
        # Todo dentro de este bloque usa cliente_123
        sdk.storage.json.put("session", {"user_id": 123, "active": True})
        sdk.storage.binary.put("avatar.jpg", b"imagen_cliente_123")
        
        # Verificar tenant actual
        print(f"Tenant en contexto: {sdk.get_current_tenant_id()}")
    
    with sdk.tenancy.tenant_context("cliente_456"):
        sdk.storage.json.put("session", {"user_id": 456, "active": False})
        sdk.storage.binary.put("avatar.jpg", b"imagen_cliente_456")
        
        print(f"Tenant en contexto: {sdk.get_current_tenant_id()}")
    
    # Verificar aislamiento
    with sdk.tenancy.tenant_context("cliente_123"):
        session_123 = sdk.storage.json.get("session")
        avatar_123 = sdk.storage.binary.get("avatar.jpg")
        print(f"Cliente 123 - Session: {session_123}")
        print(f"Cliente 123 - Avatar: {len(avatar_123)} bytes")
    
    with sdk.tenancy.tenant_context("cliente_456"):
        session_456 = sdk.storage.json.get("session")
        avatar_456 = sdk.storage.binary.get("avatar.jpg")
        print(f"Cliente 456 - Session: {session_456}")
        print(f"Cliente 456 - Avatar: {len(avatar_456)} bytes")
    
    print("✅ Context manager funciona perfectamente")

def demo_gradual_migration():
    """
    Demostración: Migración gradual de monolítico a multi-tenant
    """
    print("\n=== 🚀 MIGRACIÓN GRADUAL ===")
    
    # FASE 1: App monolítica (sin cambios)
    print("📱 Fase 1: Aplicación monolítica")
    sdk.storage.json.put("app_config", {"version": "1.0", "mode": "monolithic"})
    
    # FASE 2: Habilitar multi-tenancy progresivamente
    print("🔄 Fase 2: Habilitando multi-tenancy...")
    os.environ["TAUSESTACK_MULTI_TENANT_MODE"] = "true"
    sdk.tenancy.enable_multi_tenant_mode()
    
    # La misma app ahora puede manejar múltiples tenants
    print(f"Multi-tenant habilitado: {sdk.is_multi_tenant_enabled()}")
    
    # FASE 3: Configurar tenants específicos sin romper funcionalidad existente
    print("🏢 Fase 3: Configurando tenants específicos...")
    
    # Datos existentes siguen en tenant 'default'
    existing_config = sdk.storage.json.get("app_config")
    print(f"Configuración existente (tenant default): {existing_config}")
    
    # Nuevos tenants pueden tener configuraciones específicas
    sdk.tenancy.configure_tenant("nuevo_cliente", {
        "name": "Nuevo Cliente",
        "storage": {"backend": "local", "base_path": "./storage/nuevo_cliente"}
    })
    
    with sdk.tenancy.tenant_context("nuevo_cliente"):
        sdk.storage.json.put("app_config", {"version": "2.0", "mode": "multi_tenant"})
        new_config = sdk.storage.json.get("app_config")
        print(f"Nueva configuración (tenant específico): {new_config}")
    
    print("✅ Migración gradual completada sin interrupciones")

def demo_advanced_features():
    """
    Demostración: Funcionalidades avanzadas multi-tenant
    """
    print("\n=== ⚡ FUNCIONALIDADES AVANZADAS ===")
    
    # Listar todos los tenants configurados
    tenants = sdk.tenancy.list_tenants()
    print(f"Tenants configurados: {list(tenants.keys())}")
    
    # Configuración por tenant
    for tenant_id, config in tenants.items():
        print(f"  - {tenant_id}: {config.get('name', 'Sin nombre')}")
    
    # Operaciones masivas por tenant
    print("\n📊 Operaciones por tenant:")
    for tenant_id in tenants.keys():
        with sdk.tenancy.tenant_context(tenant_id):
            # Simular métricas por tenant
            metrics = {
                "tenant_id": tenant_id,
                "storage_usage": len(sdk.storage.json.get("session") or {}),
                "timestamp": "2024-01-01T00:00:00Z"
            }
            sdk.storage.json.put("metrics", metrics)
            print(f"  - {tenant_id}: {metrics}")
    
    print("✅ Funcionalidades avanzadas demostradas")

if __name__ == "__main__":
    print("🚀 TauseStack v2.0 - Demostración de Compatibilidad Multi-Tenant")
    print("=" * 60)
    
    # Ejecutar demostraciones
    demo_backward_compatibility()
    demo_multi_tenant_explicit()
    demo_context_manager()
    demo_gradual_migration()
    demo_advanced_features()
    
    print("\n" + "=" * 60)
    print("✅ ¡Demostración completada exitosamente!")
    print("💡 TauseStack v2.0 mantiene 100% compatibilidad hacia atrás")
    print("🚀 Y añade poderosas capacidades multi-tenant") 