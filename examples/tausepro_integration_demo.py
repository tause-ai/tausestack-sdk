#!/usr/bin/env python3
"""
Demo de Integración TausePro → TauseStack
=====================================

Demuestra cómo la futura plataforma TausePro consumiría TauseStack
usando el nuevo SDK External v0.7.0
"""

import asyncio
import json
from typing import Dict, Any
from datetime import datetime

# Importar el nuevo SDK External
from tausestack.sdk.external import (
    TauseStackBuilder, 
    TemplateManager, 
    DeploymentManager, 
    ExternalAuth,
    AppConfig,
    DeploymentConfig,
    DeploymentEnvironment
)


class TauseProBuilder:
    """
    Simulación de cómo sería el builder de TausePro
    consumiendo TauseStack via API
    """
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.tausestack_url = "http://localhost:9001"
        
    async def create_saas_app_from_template(self, user_config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simula el flujo completo de TausePro:
        1. Usuario selecciona template en UI
        2. Configura app via visual builder
        3. TausePro llama a TauseStack para crear app
        4. Deploy automático
        5. Return URLs para el usuario
        """
        
        print("🚀 TausePro → TauseStack Integration Demo")
        print("=" * 50)
        
        # Step 1: Autenticación
        print("\n1️⃣ Authenticating with TauseStack...")
        async with ExternalAuth(self.tausestack_url) as auth:
            try:
                # En producción, esto sería con OAuth o API keys
                user = await auth.verify_api_key(self.api_key)
                print(f"✅ Authenticated as: {user.name} ({user.role.value})")
            except Exception as e:
                print(f"❌ Auth failed: {e}")
                return {"error": "Authentication failed"}
        
        # Step 2: Listar templates disponibles
        print("\n2️⃣ Fetching available templates...")
        async with TemplateManager(self.api_key, self.tausestack_url) as templates:
            try:
                available_templates = await templates.list_templates("saas")
                print(f"✅ Found {len(available_templates)} SaaS templates")
                
                # En TausePro UI, usuario vería gallery de templates
                for template in available_templates[:3]:  # Show first 3
                    print(f"   📋 {template.name} - {template.description}")
                    
            except Exception as e:
                print(f"❌ Failed to fetch templates: {e}")
                # En TausePro, mostraríamos templates por defecto
                return {"error": "Could not fetch templates"}
        
        # Step 3: Validar configuración del usuario
        print("\n3️⃣ Validating user configuration...")
        template_id = available_templates[0].id if available_templates else "default-saas"
        
        try:
            validation = await templates.validate_template_config(template_id, user_config)
            if not validation.valid:
                print(f"❌ Configuration invalid: {validation.errors}")
                return {"error": "Invalid configuration", "details": validation.errors}
            print("✅ Configuration is valid")
            
            if validation.warnings:
                print(f"⚠️  Warnings: {validation.warnings}")
                
        except Exception as e:
            print(f"⚠️  Validation failed, proceeding anyway: {e}")
        
        # Step 4: Crear aplicación
        print("\n4️⃣ Creating application via TauseStack...")
        async with TauseStackBuilder(self.api_key, self.tausestack_url) as builder:
            try:
                app_config = AppConfig(
                    template_id=template_id,
                    name=user_config.get("app_name", "My SaaS App"),
                    tenant_id=user_config.get("tenant_id", f"tenant-{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    environment={
                        "DATABASE_URL": "postgresql://user:pass@localhost:5432/myapp",
                        "REDIS_URL": "redis://localhost:6379",
                        "APP_SECRET": "super-secret-key",
                        "STRIPE_API_KEY": user_config.get("stripe_key", "sk_test_..."),
                        "DOMAIN": user_config.get("domain", "myapp.tause.pro")
                    },
                    custom_config=user_config.get("features", {})
                )
                
                app = await builder.create_app(app_config)
                print(f"✅ App created: {app.name} (ID: {app.id})")
                print(f"   Status: {app.status.value}")
                
            except Exception as e:
                print(f"❌ App creation failed: {e}")
                return {"error": "App creation failed"}
        
        # Step 5: Deploy automático
        print("\n5️⃣ Starting automatic deployment...")
        async with DeploymentManager(self.api_key, self.tausestack_url) as deployer:
            try:
                deploy_config = DeploymentConfig(
                    app_id=app.id,
                    environment=DeploymentEnvironment.PRODUCTION,
                    config={
                        "replicas": 2,
                        "auto_scale": True,
                        "health_check": True,
                        "ssl": True,
                        "cdn": True
                    },
                    auto_deploy=True,
                    rollback_on_failure=True
                )
                
                deployment = await deployer.start_deployment(deploy_config)
                print(f"✅ Deployment started: {deployment.id}")
                print(f"   Status: {deployment.status.value}")
                print(f"   Version: {deployment.version}")
                
                # En TausePro, mostraríamos progress bar
                print("⏳ Waiting for deployment to complete...")
                
                # Simular espera (en producción sería real)
                await asyncio.sleep(3)
                
                # Check deployment status
                final_deployment = await deployer.get_deployment(deployment.id)
                print(f"✅ Deployment completed!")
                print(f"   Final status: {final_deployment.status.value}")
                
            except Exception as e:
                print(f"❌ Deployment failed: {e}")
                return {"error": "Deployment failed", "app_id": app.id}
        
        # Step 6: Return success con URLs
        print("\n6️⃣ Application ready! 🎉")
        
        result = {
            "success": True,
            "app": {
                "id": app.id,
                "name": app.name,
                "status": app.status.value,
                "urls": app.urls,
                "tenant_id": app.tenant_id
            },
            "deployment": {
                "id": deployment.id,
                "status": final_deployment.status.value,
                "version": final_deployment.version,
                "urls": final_deployment.urls
            },
            "next_steps": [
                "Configure your domain DNS",
                "Set up payment webhooks", 
                "Customize your app appearance",
                "Invite team members"
            ]
        }
        
        print("\n📊 Application Summary:")
        print(f"   🌐 Frontend URL: {app.urls.get('frontend_url', 'https://myapp.tause.pro')}")
        print(f"   🔧 Admin URL: {app.urls.get('admin_url', 'https://admin.myapp.tause.pro')}")
        print(f"   📡 API URL: {app.urls.get('api_url', 'https://api.myapp.tause.pro')}")
        
        return result

    async def monitor_app_health(self, app_id: str) -> Dict[str, Any]:
        """
        Monitorear salud de la aplicación
        Esto se usaría en el dashboard de TausePro
        """
        print(f"\n🔍 Monitoring app health: {app_id}")
        
        async with TauseStackBuilder(self.api_key, self.tausestack_url) as builder:
            try:
                # Get app info
                app = await builder.get_app(app_id)
                print(f"📱 App: {app.name} - Status: {app.status.value}")
                
                # Health check
                health = await builder.health_check()
                print(f"🏥 System Health: {health.get('status', 'unknown')}")
                
                return {
                    "app_status": app.status.value,
                    "system_health": health,
                    "last_checked": datetime.now().isoformat()
                }
                
            except Exception as e:
                print(f"❌ Health check failed: {e}")
                return {"error": str(e)}

    async def scale_app(self, app_id: str, replicas: int) -> bool:
        """
        Escalar aplicación
        Feature que tendría TausePro para manejo de tráfico
        """
        print(f"\n📈 Scaling app {app_id} to {replicas} replicas...")
        
        async with TauseStackBuilder(self.api_key, self.tausestack_url) as builder:
            try:
                # Update app config
                scaling_config = {
                    "deployment": {
                        "replicas": replicas,
                        "auto_scale": replicas > 1
                    }
                }
                
                updated_app = await builder.update_app_config(app_id, scaling_config)
                print(f"✅ App scaled successfully!")
                return True
                
            except Exception as e:
                print(f"❌ Scaling failed: {e}")
                return False


# Demo scenarios
async def demo_e_commerce_store():
    """Simular creación de tienda e-commerce"""
    
    # Simular API key (en producción vendría de auth)
    api_key = "tsp_demo_key_123"
    
    builder = TauseProBuilder(api_key)
    
    user_config = {
        "app_name": "Mi Tienda Online",
        "tenant_id": "ecommerce-demo-001",
        "domain": "mitienda.com",
        "stripe_key": "sk_test_ecommerce123",
        "features": {
            "payments": True,
            "inventory": True,
            "shipping": True,
            "analytics": True,
            "multi_currency": False
        }
    }
    
    result = await builder.create_saas_app_from_template(user_config)
    
    if result.get("success"):
        print("\n🛒 E-commerce store created successfully!")
        print("User can now:")
        print("- Add products via admin panel")
        print("- Configure payment methods")
        print("- Set up shipping zones")
        print("- Launch marketing campaigns")
    
    return result


async def demo_crm_system():
    """Simular creación de sistema CRM"""
    
    api_key = "tsp_demo_key_456"
    builder = TauseProBuilder(api_key)
    
    user_config = {
        "app_name": "CRM Empresarial",
        "tenant_id": "crm-demo-002", 
        "domain": "crm.miempresa.com",
        "features": {
            "contact_management": True,
            "sales_pipeline": True,
            "email_automation": True,
            "reporting": True,
            "integrations": ["mailchimp", "salesforce"]
        }
    }
    
    result = await builder.create_saas_app_from_template(user_config)
    
    if result.get("success"):
        print("\n👥 CRM system created successfully!")
        app_id = result["app"]["id"]
        
        # Demo additional operations
        await builder.monitor_app_health(app_id)
        await builder.scale_app(app_id, 3)  # Scale for high usage
    
    return result


async def main():
    """Run all demo scenarios"""
    
    print("🎯 TausePro Integration Scenarios")
    print("This demonstrates how TausePro would consume TauseStack")
    print("Note: These are mock scenarios, real integration would require:")
    print("- TauseStack API Gateway running on port 9001")
    print("- Valid API keys and authentication")
    print("- Template registry with actual templates")
    print("\n" + "="*60)
    
    # Scenario 1: E-commerce
    print("\n🛒 SCENARIO 1: Creating E-commerce Store")
    try:
        await demo_e_commerce_store()
    except Exception as e:
        print(f"❌ E-commerce demo failed: {e}")
    
    # Scenario 2: CRM
    print("\n👥 SCENARIO 2: Creating CRM System")
    try:
        await demo_crm_system()
    except Exception as e:
        print(f"❌ CRM demo failed: {e}")
    
    print("\n✨ Demo completed!")
    print("\nNext steps for TausePro development:")
    print("1. Implement visual drag & drop builder")
    print("2. Create template marketplace UI")
    print("3. Add AI-powered code generation")
    print("4. Build user dashboard for app management")
    print("5. Integrate payment processing")


if __name__ == "__main__":
    asyncio.run(main()) 