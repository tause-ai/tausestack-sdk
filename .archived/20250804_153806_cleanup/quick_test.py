#!/usr/bin/env python3
"""
Script de verificación rápida del Builder
"""

import asyncio
import sys
import os

# Añadir el directorio actual al path
sys.path.insert(0, os.getcwd())

async def test_builder():
    print("🧪 Probando TauseStack Builder...")
    
    try:
        # Test 1: Importar servicios
        print("📦 Importando servicios...")
        from tausestack.services.builder.core.builder_service import BuilderService, ProjectType
        from tausestack.services.builder.tools.builder_tools import BuilderMCPServer
        from tausestack.services.builder.config.builder_config import get_config, list_available_templates
        print("✅ Importaciones exitosas")
        
        # Test 2: Configuración
        print("⚙️  Verificando configuración...")
        config = get_config()
        print(f"✅ Configuración cargada: {config.SERVICE_NAME} v{config.SERVICE_VERSION}")
        
        # Test 3: Templates
        print("📋 Verificando templates...")
        templates = list_available_templates()
        print(f"✅ Templates disponibles: {len(templates)}")
        for template in templates:
            print(f"   • {template['name']} ({template['type']})")
        
        # Test 4: Builder Service
        print("🏗️  Probando Builder Service...")
        tenant_id = "test-tenant"
        builder_service = BuilderService(tenant_id)
        print(f"✅ Builder Service creado para tenant: {tenant_id}")
        
        # Test 5: Crear proyecto de prueba
        print("🎯 Creando proyecto de prueba...")
        project = await builder_service.create_project(
            name="Test Project",
            description="Proyecto de prueba del Builder",
            project_type=ProjectType.WEB,
            template_id="web-basic"
        )
        print(f"✅ Proyecto creado: {project.name} ({project.id})")
        
        # Test 6: Listar proyectos
        print("📋 Listando proyectos...")
        projects = await builder_service.list_projects()
        print(f"✅ Proyectos encontrados: {len(projects)}")
        
        # Test 7: MCP Tools
        print("🔧 Probando MCP Tools...")
        mcp_server = BuilderMCPServer(tenant_id)
        server = mcp_server.get_server()
        print(f"✅ MCP Server creado con {len(server.list_tools)} herramientas")
        
        # Test 8: Estadísticas
        print("📊 Obteniendo estadísticas...")
        stats = await builder_service.get_stats()
        print(f"✅ Estadísticas: {stats.total_projects} proyectos totales")
        
        # Test 9: Eliminar proyecto de prueba
        print("🗑️  Limpiando proyecto de prueba...")
        deleted = await builder_service.delete_project(project.id)
        if deleted:
            print("✅ Proyecto de prueba eliminado")
        else:
            print("⚠️  No se pudo eliminar el proyecto de prueba")
        
        print("\n🎉 ¡Todas las pruebas pasaron exitosamente!")
        print("\n📋 Resumen del Builder:")
        print(f"   • Servicio: {config.SERVICE_NAME} v{config.SERVICE_VERSION}")
        print(f"   • Templates: {len(templates)} disponibles")
        print(f"   • MCP Tools: {len(server.list_tools)} herramientas")
        print(f"   • Puerto: {config.SERVICE_PORT}")
        
        print("\n🚀 El Builder está listo para usar!")
        print("   • Ejecuta: python launch_builder.py")
        print("   • Visita: http://localhost:9001/admin/builder")
        
    except Exception as e:
        print(f"❌ Error en las pruebas: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == "__main__":
    success = asyncio.run(test_builder())
    sys.exit(0 if success else 1) 