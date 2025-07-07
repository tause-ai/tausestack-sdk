"""
Demostración Completa de Aislamiento Multi-Tenant en TauseStack

Este ejemplo muestra todas las capacidades de aislamiento implementadas:
- Aislamiento de base de datos (esquemas separados)
- Aislamiento de storage (rutas separadas)
- Aislamiento de cache (claves separadas)
- Límites de recursos por tenant
- Prevención de acceso cross-tenant
"""

import os
import tempfile
import shutil
from pathlib import Path

# Configurar modo multi-tenant
os.environ["TAUSESTACK_MULTI_TENANT_MODE"] = "true"

from tausestack.sdk import tenancy, isolation

def demo_basic_isolation():
    """Demostración básica de aislamiento multi-tenant."""
    print("=== 🏢 DEMOSTRACIÓN BÁSICA DE AISLAMIENTO ===")
    
    # Configurar tenants con aislamiento específico
    tenancy.configure_tenant("cliente_123", {
        "name": "Cliente Premium",
        "database_schema": "tenant_cliente_123",
        "storage_prefix": "tenants/cliente_123/",
        "cache_prefix": "tenant:cliente_123:",
        "resource_limits": {
            "storage_gb": 10,
            "api_calls_per_hour": 1000,
            "cache_memory_mb": 100
        }
    })
    
    tenancy.configure_tenant("cliente_456", {
        "name": "Cliente Básico", 
        "database_schema": "tenant_cliente_456",
        "storage_prefix": "tenants/cliente_456/",
        "cache_prefix": "tenant:cliente_456:",
        "resource_limits": {
            "storage_gb": 1,
            "api_calls_per_hour": 100,
            "cache_memory_mb": 10
        }
    })
    
    # Configurar aislamiento específico
    isolation.configure_tenant_isolation("cliente_123", {
        "database_schema": "tenant_cliente_123",
        "storage_prefix": "tenants/cliente_123/",
        "cache_prefix": "tenant:cliente_123:",
        "resource_limits": {
            "storage_gb": 10,
            "api_calls_per_hour": 1000,
            "cache_memory_mb": 100
        },
        "isolation_level": "strict"
    })
    
    isolation.configure_tenant_isolation("cliente_456", {
        "database_schema": "tenant_cliente_456", 
        "storage_prefix": "tenants/cliente_456/",
        "cache_prefix": "tenant:cliente_456:",
        "resource_limits": {
            "storage_gb": 1,
            "api_calls_per_hour": 100,
            "cache_memory_mb": 10
        },
        "isolation_level": "strict"
    })
    
    print("✅ Tenants configurados con aislamiento específico")

def demo_database_isolation():
    """Demostración de aislamiento de base de datos."""
    print("\n=== 🗄️ AISLAMIENTO DE BASE DE DATOS ===")
    
    from tausestack.sdk.isolation.database_isolation import db_isolation
    
    # Simular conexión de base de datos
    class MockDBConnection:
        def cursor(self):
            return MockCursor()
        def commit(self):
            pass
        def get_dsn_parameters(self):
            return {"host": "localhost", "port": "5432", "user": "postgres", "dbname": "test"}
    
    class MockCursor:
        def __enter__(self):
            return self
        def __exit__(self, *args):
            pass
        def execute(self, sql, params=None):
            print(f"  📝 SQL: {sql}")
            if params:
                print(f"  📝 Params: {params}")
    
    db_conn = MockDBConnection()
    
    # Demostrar aislamiento por tenant
    for tenant_id in ["cliente_123", "cliente_456"]:
        print(f"\n🏢 Tenant: {tenant_id}")
        
        # Obtener esquema aislado
        schema = db_isolation.get_tenant_schema(tenant_id)
        print(f"  📊 Esquema: {schema}")
        
        # Crear esquema (simulado)
        db_isolation.create_tenant_schema(tenant_id, db_conn)
        
        # Obtener nombre de tabla aislado
        table_name = db_isolation.get_isolated_table_name("users", tenant_id)
        print(f"  📋 Tabla aislada: {table_name}")
        
        # Configurar RLS (simulado)
        db_isolation.setup_rls_policies(tenant_id, db_conn, "users")
        
        # Establecer contexto de tenant
        db_isolation.set_tenant_context(db_conn, tenant_id)

def demo_storage_isolation():
    """Demostración de aislamiento de storage."""
    print("\n=== 💾 AISLAMIENTO DE STORAGE ===")
    
    from tausestack.sdk.isolation.storage_isolation import storage_isolation
    
    # Crear directorio temporal para demostración
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"📁 Directorio base: {temp_dir}")
        
        # Demostrar aislamiento por tenant
        for tenant_id in ["cliente_123", "cliente_456"]:
            print(f"\n🏢 Tenant: {tenant_id}")
            
            # Crear estructura de storage
            storage_isolation.create_tenant_storage(tenant_id, temp_dir)
            
            # Obtener rutas aisladas
            original_path = "documents/report.pdf"
            isolated_path = storage_isolation.get_tenant_storage_path(original_path, tenant_id)
            print(f"  📄 Ruta original: {original_path}")
            print(f"  📄 Ruta aislada: {isolated_path}")
            
            # Simular archivo
            full_path = os.path.join(temp_dir, isolated_path)
            os.makedirs(os.path.dirname(full_path), exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(f"Contenido del archivo para {tenant_id}")
            
            # Obtener uso de storage
            usage = storage_isolation.get_tenant_storage_usage(tenant_id, temp_dir)
            print(f"  📊 Uso: {usage['file_count']} archivos, {usage['total_size_bytes']} bytes")
            
            # Verificar cuota
            file_size = 1024  # 1KB
            within_quota = storage_isolation.check_storage_quota(tenant_id, file_size, temp_dir)
            print(f"  ✅ Dentro de cuota: {within_quota}")
        
        # Listar archivos por tenant
        for tenant_id in ["cliente_123", "cliente_456"]:
            print(f"\n📋 Archivos de {tenant_id}:")
            files = storage_isolation.list_tenant_files(tenant_id, temp_dir)
            for file_info in files:
                print(f"  - {file_info['path']} ({file_info['size_bytes']} bytes)")
    
    finally:
        # Limpiar
        shutil.rmtree(temp_dir)

def demo_cache_isolation():
    """Demostración de aislamiento de cache."""
    print("\n=== 🚀 AISLAMIENTO DE CACHE ===")
    
    from tausestack.sdk.isolation.cache_isolation import cache_isolation
    
    # Simular backend de cache
    class MockCacheBackend:
        def __init__(self):
            self._data = {}
        
        def set(self, key, value, ttl=None):
            self._data[key] = value
            print(f"  💾 Cache SET: {key} = {value}")
        
        def get(self, key):
            value = self._data.get(key)
            if value:
                print(f"  📖 Cache GET: {key} = {value}")
            return value
        
        def delete(self, key):
            if key in self._data:
                del self._data[key]
                print(f"  🗑️ Cache DELETE: {key}")
                return True
            return False
        
        def keys(self, pattern):
            # Simulación simple de pattern matching
            if pattern == "*":
                return list(self._data.keys())
            return [k for k in self._data.keys() if pattern.replace("*", "") in k]
    
    # Registrar backend
    mock_cache = MockCacheBackend()
    cache_isolation.register_cache_backend("mock", mock_cache)
    
    # Demostrar aislamiento por tenant
    for tenant_id in ["cliente_123", "cliente_456"]:
        print(f"\n🏢 Tenant: {tenant_id}")
        
        # Obtener prefijo de cache
        prefix = cache_isolation.get_tenant_cache_prefix(tenant_id)
        print(f"  🔑 Prefijo de cache: {prefix}")
        
        # Operaciones de cache aisladas
        cache_isolation.set_with_isolation("user:123", {"name": f"Usuario de {tenant_id}"}, 
                                         tenant_id=tenant_id, backend_name="mock")
        cache_isolation.set_with_isolation("config", {"theme": "dark"}, 
                                         tenant_id=tenant_id, backend_name="mock")
        
        # Obtener valores
        user_data = cache_isolation.get_with_isolation("user:123", tenant_id=tenant_id, backend_name="mock")
        config = cache_isolation.get_with_isolation("config", tenant_id=tenant_id, backend_name="mock")
        
        # Obtener uso de cache
        usage = cache_isolation.get_tenant_cache_usage(tenant_id, "mock")
        print(f"  📊 Uso de cache: {usage['key_count']} claves, {usage['memory_usage_bytes']} bytes")
        
        # Verificar cuota
        within_quota = cache_isolation.check_cache_quota(tenant_id, 1024, "mock")
        print(f"  ✅ Dentro de cuota: {within_quota}")
    
    # Demostrar invalidation por tenant
    print(f"\n🗑️ Invalidación de cache para cliente_123:")
    deleted_count = cache_isolation.invalidate_tenant_cache("cliente_123", "*", "mock")
    print(f"  🗑️ Claves eliminadas: {deleted_count}")

def demo_cross_tenant_isolation():
    """Demostración de prevención de acceso cross-tenant."""
    print("\n=== 🛡️ PREVENCIÓN DE ACCESO CROSS-TENANT ===")
    
    # Configurar tenant con aislamiento relajado para demostración
    isolation.configure_tenant_isolation("cliente_relaxed", {
        "isolation_level": "relaxed"
    })
    
    # Probar diferentes combinaciones de aislamiento
    test_cases = [
        ("cliente_123", "cliente_456"),  # Strict + Strict = Bloqueado
        ("cliente_123", "cliente_relaxed"),  # Strict + Relaxed = Bloqueado
        ("cliente_relaxed", "cliente_456"),  # Relaxed + Strict = Bloqueado
        ("cliente_relaxed", "cliente_relaxed"),  # Relaxed + Relaxed = Permitido
        ("cliente_123", "cliente_123"),  # Mismo tenant = Permitido
    ]
    
    for source, target in test_cases:
        allowed = isolation.enforce_cross_tenant_isolation(source, target)
        status = "✅ PERMITIDO" if allowed else "❌ BLOQUEADO"
        print(f"  {source} -> {target}: {status}")

def demo_resource_limits():
    """Demostración de límites de recursos."""
    print("\n=== 📊 LÍMITES DE RECURSOS ===")
    
    for tenant_id in ["cliente_123", "cliente_456"]:
        print(f"\n🏢 Tenant: {tenant_id}")
        
        # Obtener configuración de límites
        config = isolation.get_tenant_isolation_config(tenant_id)
        limits = config["resource_limits"]
        
        print(f"  📊 Límites configurados:")
        for resource, limit in limits.items():
            print(f"    - {resource}: {limit}")
        
        # Probar diferentes usos
        test_usage = {
            "storage_gb": 5,
            "api_calls_per_hour": 500,
            "cache_memory_mb": 50
        }
        
        print(f"  🧪 Pruebas de límites:")
        for resource, usage in test_usage.items():
            within_limit = isolation.check_resource_limits(resource, usage, tenant_id)
            status = "✅ DENTRO" if within_limit else "❌ EXCEDIDO"
            print(f"    - {resource}: {usage} {status}")

def demo_context_managers():
    """Demostración de context managers para aislamiento."""
    print("\n=== 🔄 CONTEXT MANAGERS ===")
    
    # Context manager de tenancy
    print("🏢 Context Manager de Tenancy:")
    with tenancy.tenant_context("cliente_123"):
        current_tenant = tenancy.get_current_tenant_id()
        print(f"  📍 Tenant actual: {current_tenant}")
        
        # Todas las operaciones usan cliente_123
        isolated_path = isolation.isolate_storage_path("data.json")
        print(f"  📄 Ruta aislada: {isolated_path}")
    
    # Context manager de aislamiento
    print("\n🛡️ Context Manager de Aislamiento:")
    with isolation.isolation_context("cliente_456"):
        current_tenant = tenancy.get_current_tenant_id()
        print(f"  📍 Tenant actual: {current_tenant}")
        
        # Todas las operaciones usan cliente_456
        isolated_path = isolation.isolate_storage_path("data.json")
        print(f"  📄 Ruta aislada: {isolated_path}")

def main():
    """Ejecutar todas las demostraciones."""
    print("🚀 TauseStack v2.0 - Demostración Completa de Aislamiento Multi-Tenant")
    print("=" * 70)
    
    try:
        demo_basic_isolation()
        demo_database_isolation()
        demo_storage_isolation()
        demo_cache_isolation()
        demo_cross_tenant_isolation()
        demo_resource_limits()
        demo_context_managers()
        
        print("\n" + "=" * 70)
        print("✅ Demostración completada exitosamente")
        print("\n🎯 Características implementadas:")
        print("  - Aislamiento completo de base de datos (esquemas separados)")
        print("  - Aislamiento de storage (rutas separadas)")
        print("  - Aislamiento de cache (claves separadas)")
        print("  - Límites de recursos por tenant")
        print("  - Prevención de acceso cross-tenant")
        print("  - Context managers para operaciones aisladas")
        print("  - Configuración granular por tenant")
        
    except Exception as e:
        print(f"\n❌ Error en demostración: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 