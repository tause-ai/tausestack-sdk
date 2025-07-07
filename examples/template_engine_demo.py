#!/usr/bin/env python3
"""
TauseStack Template Engine Demo v0.8.0
Demostración completa del sistema de templates con shadcn/ui
"""

import asyncio
import json
import sys
from pathlib import Path

# Agregar el directorio raíz al path
sys.path.append(str(Path(__file__).parent.parent))

from services.templates.core.engine import TemplateEngine
from services.templates.storage.template_loader import TemplateRegistry
from services.templates.schemas.template_schema import (
    TemplateSchema, TemplateMetadata, TemplateGenerationRequest,
    ComponentSchema, PageSchema, TemplateCategory, ComponentType,
    TemplateConfiguration, TemplateDependencies
)


class TemplateEngineDemo:
    """Demo completo del Template Engine"""
    
    def __init__(self):
        self.engine = TemplateEngine()
        self.registry = TemplateRegistry()
        print("🚀 TauseStack Template Engine Demo v0.8.0")
        print("=" * 50)
    
    async def run_demo(self):
        """Ejecuta demo completo"""
        print("\n1️⃣  Creando templates de ejemplo...")
        await self.create_sample_templates()
        
        print("\n2️⃣  Listando templates disponibles...")
        await self.list_templates()
        
        print("\n3️⃣  Generando proyecto desde template...")
        await self.generate_project_demo()
        
        print("\n4️⃣  Validando templates...")
        await self.validate_templates_demo()
        
        print("\n5️⃣  Demostrando componentes shadcn/ui...")
        await self.shadcn_components_demo()
        
        print("\n✅ Demo completado exitosamente!")
    
    async def create_sample_templates(self):
        """Crea templates de ejemplo avanzados"""
        
        # Template 1: Dashboard Avanzado
        advanced_dashboard = TemplateSchema(
            id="advanced-dashboard",
            metadata=TemplateMetadata(
                name="Advanced Dashboard",
                description="Dashboard avanzado con múltiples componentes shadcn/ui",
                author="TauseStack Team",
                category=TemplateCategory.DASHBOARD,
                tags=["dashboard", "analytics", "shadcn", "advanced"],
                version="1.0.0"
            ),
            configuration=TemplateConfiguration(
                framework="nextjs",
                ui_library="shadcn",
                typescript=True,
                tailwind=True,
                dark_mode=True,
                responsive=True
            ),
            dependencies=TemplateDependencies(
                npm_packages=["recharts", "date-fns", "lucide-react"],
                shadcn_components=["card", "table", "badge", "button", "dialog", "select"]
            ),
            pages=[
                PageSchema(
                    name="dashboard",
                    path="/",
                    components=[
                        ComponentSchema(
                            id="header",
                            type=ComponentType.CONTAINER,
                            children=[
                                ComponentSchema(
                                    id="title",
                                    type=ComponentType.CONTAINER,
                                    props={"className": "mb-8"},
                                    children=[]
                                )
                            ]
                        ),
                        ComponentSchema(
                            id="stats-grid",
                            type=ComponentType.GRID,
                            props={"className": "grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8"},
                            children=[
                                ComponentSchema(
                                    id="revenue-card",
                                    type=ComponentType.CARD,
                                    props={
                                        "title": "Total Revenue",
                                        "value": "$45,231.89",
                                        "change": "+20.1%",
                                        "trend": "up"
                                    },
                                    children=[]
                                ),
                                ComponentSchema(
                                    id="subscriptions-card",
                                    type=ComponentType.CARD,
                                    props={
                                        "title": "Subscriptions",
                                        "value": "2,350",
                                        "change": "+180.1%",
                                        "trend": "up"
                                    },
                                    children=[]
                                ),
                                ComponentSchema(
                                    id="sales-card",
                                    type=ComponentType.CARD,
                                    props={
                                        "title": "Sales",
                                        "value": "12,234",
                                        "change": "+19%",
                                        "trend": "up"
                                    },
                                    children=[]
                                ),
                                ComponentSchema(
                                    id="active-users-card",
                                    type=ComponentType.CARD,
                                    props={
                                        "title": "Active Now",
                                        "value": "573",
                                        "change": "+201",
                                        "trend": "up"
                                    },
                                    children=[]
                                )
                            ]
                        ),
                        ComponentSchema(
                            id="charts-section",
                            type=ComponentType.GRID,
                            props={"className": "grid-cols-1 lg:grid-cols-2 gap-8 mb-8"},
                            children=[
                                ComponentSchema(
                                    id="overview-chart",
                                    type=ComponentType.CARD,
                                    props={
                                        "title": "Overview",
                                        "description": "Revenue over time"
                                    },
                                    children=[]
                                ),
                                ComponentSchema(
                                    id="recent-sales",
                                    type=ComponentType.CARD,
                                    props={
                                        "title": "Recent Sales",
                                        "description": "You made 265 sales this month"
                                    },
                                    children=[]
                                )
                            ]
                        ),
                        ComponentSchema(
                            id="data-table",
                            type=ComponentType.TABLE,
                            props={
                                "caption": "A list of your recent invoices",
                                "headers": ["Invoice", "Status", "Method", "Amount"]
                            },
                            children=[]
                        )
                    ]
                )
            ],
            theme={
                "primary": "#0f172a",
                "secondary": "#64748b",
                "accent": "#3b82f6",
                "background": "#ffffff",
                "foreground": "#0f172a"
            }
        )
        
        # Template 2: E-commerce Completo
        ecommerce_complete = TemplateSchema(
            id="ecommerce-complete",
            metadata=TemplateMetadata(
                name="Complete E-commerce",
                description="E-commerce completo con todas las funcionalidades",
                author="TauseStack Team",
                category=TemplateCategory.ECOMMERCE,
                tags=["ecommerce", "store", "shadcn", "complete"],
                version="1.0.0"
            ),
            configuration=TemplateConfiguration(
                framework="nextjs",
                ui_library="shadcn",
                typescript=True,
                tailwind=True,
                dark_mode=True,
                responsive=True
            ),
            dependencies=TemplateDependencies(
                npm_packages=["stripe", "next-auth", "zustand"],
                shadcn_components=["card", "button", "badge", "dialog", "sheet", "select", "input"]
            ),
            pages=[
                PageSchema(
                    name="home",
                    path="/",
                    components=[
                        ComponentSchema(
                            id="hero-section",
                            type=ComponentType.HERO,
                            props={
                                "title": "Discover Amazing Products",
                                "subtitle": "Shop the best selection with unbeatable prices",
                                "cta": "Shop Now"
                            },
                            children=[]
                        ),
                        ComponentSchema(
                            id="featured-products",
                            type=ComponentType.GRID,
                            props={"className": "grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6"},
                            children=[
                                ComponentSchema(
                                    id="product-card-1",
                                    type=ComponentType.CARD,
                                    props={
                                        "title": "Premium Headphones",
                                        "price": "$299.99",
                                        "image": "/products/headphones.jpg",
                                        "rating": 4.8
                                    },
                                    children=[]
                                )
                            ]
                        )
                    ]
                ),
                PageSchema(
                    name="products",
                    path="/products",
                    components=[
                        ComponentSchema(
                            id="filters-sidebar",
                            type=ComponentType.SIDEBAR,
                            children=[
                                ComponentSchema(
                                    id="category-filter",
                                    type=ComponentType.SELECT,
                                    props={"placeholder": "Select Category"},
                                    children=[]
                                ),
                                ComponentSchema(
                                    id="price-filter",
                                    type=ComponentType.SELECT,
                                    props={"placeholder": "Price Range"},
                                    children=[]
                                )
                            ]
                        ),
                        ComponentSchema(
                            id="products-grid",
                            type=ComponentType.GRID,
                            props={"className": "grid-cols-1 md:grid-cols-3 lg:grid-cols-4 gap-6"},
                            children=[]
                        )
                    ]
                )
            ],
            theme={
                "primary": "#059669",
                "secondary": "#10b981",
                "accent": "#34d399",
                "background": "#ffffff",
                "foreground": "#0f172a"
            }
        )
        
        # Guardar templates
        await self.registry.save_template(advanced_dashboard)
        await self.registry.save_template(ecommerce_complete)
        
        print("✅ Templates creados:")
        print(f"   - {advanced_dashboard.metadata.name}")
        print(f"   - {ecommerce_complete.metadata.name}")
    
    async def list_templates(self):
        """Lista todos los templates disponibles"""
        templates = await self.registry.list_templates()
        
        print(f"📋 Templates disponibles ({len(templates)}):")
        for template in templates:
            print(f"   🎨 {template.name}")
            print(f"      ID: {template.category}")
            print(f"      Categoría: {template.category}")
            print(f"      Tags: {', '.join(template.tags)}")
            print(f"      Autor: {template.author}")
            print()
    
    async def generate_project_demo(self):
        """Demuestra generación de proyecto"""
        print("🏗️  Generando proyecto desde template...")
        
        request = TemplateGenerationRequest(
            template_id="advanced-dashboard",
            project_name="Mi Dashboard Empresarial",
            customizations={
                "theme": {
                    "primary": "#6366f1",
                    "secondary": "#8b5cf6"
                },
                "features": ["dark_mode", "responsive", "analytics"]
            },
            theme_overrides={
                "primary": "#6366f1"
            }
        )
        
        result = self.engine.generate_project(request)
        
        if result.success:
            print("✅ Proyecto generado exitosamente!")
            print(f"   📁 Project ID: {result.project_id}")
            print(f"   📄 Archivos generados: {len(result.generated_files)}")
            print(f"   🔗 Preview URL: {result.preview_url}")
            
            # Mostrar algunos archivos generados
            print("\n📄 Archivos generados:")
            for file in result.generated_files[:5]:  # Mostrar solo los primeros 5
                print(f"   - {file}")
            if len(result.generated_files) > 5:
                print(f"   ... y {len(result.generated_files) - 5} más")
        else:
            print("❌ Error generando proyecto:")
            for error in result.errors:
                print(f"   - {error}")
    
    async def validate_templates_demo(self):
        """Demuestra validación de templates"""
        print("🔍 Validando templates...")
        
        # Obtener template para validar
        template = await self.registry.get_template("advanced-dashboard")
        if template:
            errors = await self.registry.validate_template(template)
            if errors:
                print("❌ Errores de validación encontrados:")
                for error in errors:
                    print(f"   - {error}")
            else:
                print("✅ Template válido - sin errores")
        else:
            print("❌ Template no encontrado")
    
    async def shadcn_components_demo(self):
        """Demuestra mapeo de componentes shadcn/ui"""
        print("🎨 Componentes shadcn/ui disponibles:")
        
        from services.templates.core.engine import ShadcnComponentMapper
        
        # Mostrar componentes disponibles
        components = list(ShadcnComponentMapper.COMPONENT_IMPORTS.keys())
        print(f"   📦 {len(components)} componentes disponibles:")
        
        for component in components:
            print(f"   - {component.value}")
        
        # Demostrar generación de componente
        print("\n🔧 Ejemplo de generación de componente:")
        
        sample_component = ComponentSchema(
            id="sample-button",
            type=ComponentType.BUTTON,
            variant="default",
            props={"className": "w-full"},
            children=[]
        )
        
        rendered = ShadcnComponentMapper.render_component(sample_component)
        print("   Código generado:")
        print(f"   {rendered.strip()}")
    
    async def performance_demo(self):
        """Demuestra rendimiento del engine"""
        print("⚡ Test de rendimiento:")
        
        import time
        
        # Test de carga de templates
        start_time = time.time()
        templates = await self.registry.list_templates()
        load_time = time.time() - start_time
        
        print(f"   📋 Carga de {len(templates)} templates: {load_time:.3f}s")
        
        # Test de generación
        start_time = time.time()
        request = TemplateGenerationRequest(
            template_id="advanced-dashboard",
            project_name="Performance Test"
        )
        result = self.engine.generate_project(request)
        gen_time = time.time() - start_time
        
        print(f"   🏗️  Generación de proyecto: {gen_time:.3f}s")
        print(f"   📄 Archivos generados: {len(result.generated_files) if result.success else 0}")


async def main():
    """Función principal del demo"""
    demo = TemplateEngineDemo()
    
    try:
        await demo.run_demo()
        
        # Demo adicional de rendimiento
        print("\n" + "=" * 50)
        print("🚀 Demo de Rendimiento")
        print("=" * 50)
        await demo.performance_demo()
        
    except KeyboardInterrupt:
        print("\n\n⏹️  Demo interrumpido por el usuario")
    except Exception as e:
        print(f"\n❌ Error en el demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main()) 