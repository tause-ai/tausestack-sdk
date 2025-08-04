"""
Template Registry - Gestión de templates con storage y validación
"""
import json
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from datetime import datetime
import asyncio

from ..schemas.template_schema import (
    TemplateSchema, TemplateMetadata, TemplateCategory, ComponentSchema
)


class TemplateRegistry:
    """Registry para gestión de templates con storage local y validación"""
    
    def __init__(self, storage_path: str = "templates/registry"):
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        self.metadata_cache: Dict[str, TemplateMetadata] = {}
        self._load_metadata_cache()
    
    def _load_metadata_cache(self):
        """Carga metadata cache desde disco"""
        cache_file = self.storage_path / "metadata_cache.json"
        if cache_file.exists():
            try:
                with open(cache_file, 'r', encoding='utf-8') as f:
                    cache_data = json.load(f)
                    self.metadata_cache = {
                        k: TemplateMetadata(**v) for k, v in cache_data.items()
                    }
            except Exception as e:
                print(f"Error loading metadata cache: {e}")
                self.metadata_cache = {}
    
    def _save_metadata_cache(self):
        """Guarda metadata cache a disco"""
        cache_file = self.storage_path / "metadata_cache.json"
        try:
            cache_data = {
                k: v.model_dump() for k, v in self.metadata_cache.items()
            }
            with open(cache_file, 'w', encoding='utf-8') as f:
                json.dump(cache_data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving metadata cache: {e}")
    
    async def list_templates(
        self,
        category: Optional[TemplateCategory] = None,
        search: Optional[str] = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[TemplateMetadata]:
        """Lista templates con filtros"""
        templates = list(self.metadata_cache.values())
        
        # Filtrar por categoría
        if category:
            templates = [t for t in templates if t.category == category]
        
        # Filtrar por búsqueda
        if search:
            search_lower = search.lower()
            templates = [
                t for t in templates 
                if (search_lower in t.name.lower() or 
                    search_lower in t.description.lower() or
                    any(search_lower in tag.lower() for tag in t.tags))
            ]
        
        # Ordenar por fecha de actualización (más recientes primero)
        templates.sort(
            key=lambda t: t.updated_at or t.created_at or "",
            reverse=True
        )
        
        # Paginación
        return templates[offset:offset + limit]
    
    async def get_template(self, template_id: str) -> Optional[TemplateSchema]:
        """Obtiene template completo por ID"""
        template_file = self.storage_path / f"{template_id}.json"
        if not template_file.exists():
            return None
        
        try:
            with open(template_file, 'r', encoding='utf-8') as f:
                template_data = json.load(f)
            return TemplateSchema(**template_data)
        except Exception as e:
            print(f"Error loading template {template_id}: {e}")
            return None
    
    async def save_template(self, template: TemplateSchema) -> TemplateSchema:
        """Guarda template y actualiza metadata cache"""
        # Actualizar timestamps
        now = datetime.utcnow().isoformat()
        if not template.metadata.created_at:
            template.metadata.created_at = now
        template.metadata.updated_at = now
        
        # Guardar template completo
        template_file = self.storage_path / f"{template.id}.json"
        with open(template_file, 'w', encoding='utf-8') as f:
            json.dump(template.model_dump(), f, indent=2, ensure_ascii=False)
        
        # Actualizar metadata cache
        self.metadata_cache[template.id] = template.metadata
        self._save_metadata_cache()
        
        return template
    
    async def delete_template(self, template_id: str) -> bool:
        """Elimina template"""
        template_file = self.storage_path / f"{template_id}.json"
        if not template_file.exists():
            return False
        
        try:
            # Eliminar archivo
            template_file.unlink()
            
            # Eliminar de cache
            if template_id in self.metadata_cache:
                del self.metadata_cache[template_id]
                self._save_metadata_cache()
            
            return True
        except Exception as e:
            print(f"Error deleting template {template_id}: {e}")
            return False
    
    async def validate_template(self, template: TemplateSchema) -> List[str]:
        """Valida template y retorna lista de errores"""
        errors = []
        
        # Validación básica
        if not template.id:
            errors.append("Template ID is required")
        
        if not template.metadata.name:
            errors.append("Template name is required")
        
        if not template.metadata.description:
            errors.append("Template description is required")
        
        if not template.pages:
            errors.append("Template must have at least one page")
        
        # Validar páginas
        for i, page in enumerate(template.pages):
            page_errors = await self._validate_page(page, f"Page {i+1}")
            errors.extend(page_errors)
        
        # Validar componentes reutilizables
        for i, component in enumerate(template.components):
            comp_errors = await self._validate_component(component, f"Component {i+1}")
            errors.extend(comp_errors)
        
        # Validar dependencias
        dep_errors = await self._validate_dependencies(template)
        errors.extend(dep_errors)
        
        return errors
    
    async def _validate_page(self, page, context: str) -> List[str]:
        """Valida una página"""
        errors = []
        
        if not page.name:
            errors.append(f"{context}: Page name is required")
        
        if not page.path:
            errors.append(f"{context}: Page path is required")
        
        if not page.components:
            errors.append(f"{context}: Page must have at least one component")
        
        # Validar componentes de la página
        for i, component in enumerate(page.components):
            comp_errors = await self._validate_component(
                component, f"{context} Component {i+1}"
            )
            errors.extend(comp_errors)
        
        return errors
    
    async def _validate_component(self, component: ComponentSchema, context: str) -> List[str]:
        """Valida un componente"""
        errors = []
        
        if not component.id:
            errors.append(f"{context}: Component ID is required")
        
        if not component.type:
            errors.append(f"{context}: Component type is required")
        
        # Validar componentes hijos recursivamente
        for i, child in enumerate(component.children):
            child_errors = await self._validate_component(
                child, f"{context} Child {i+1}"
            )
            errors.extend(child_errors)
        
        return errors
    
    async def _validate_dependencies(self, template: TemplateSchema) -> List[str]:
        """Valida dependencias del template"""
        errors = []
        
        # Validar que las dependencias shadcn/ui sean válidas
        valid_shadcn_components = [
            "button", "card", "input", "select", "dialog", "form", 
            "table", "badge", "alert-dialog", "sheet"
        ]
        
        for component in template.dependencies.shadcn_components:
            if component not in valid_shadcn_components:
                errors.append(f"Invalid shadcn/ui component: {component}")
        
        return errors
    
    async def create_sample_templates(self):
        """Crea templates de ejemplo para testing"""
        
        # Template 1: Dashboard empresarial
        dashboard_template = TemplateSchema(
            id="business-dashboard",
            metadata=TemplateMetadata(
                name="Business Dashboard",
                description="Dashboard empresarial completo con métricas y tablas",
                author="TauseStack Team",
                category=TemplateCategory.BUSINESS,
                tags=["dashboard", "analytics", "business", "shadcn"]
            ),
            configuration={
                "framework": "nextjs",
                "ui_library": "shadcn",
                "typescript": True,
                "tailwind": True,
                "dark_mode": True,
                "responsive": True
            },
            dependencies={
                "npm_packages": ["recharts", "date-fns"],
                "shadcn_components": ["card", "table", "badge", "button"]
            },
            pages=[
                {
                    "name": "dashboard",
                    "path": "/",
                    "components": [
                        {
                            "id": "stats-grid",
                            "type": "grid",
                            "children": [
                                {
                                    "id": "revenue-card",
                                    "type": "card",
                                    "props": {"title": "Revenue", "value": "$45,231.89"},
                                    "children": []
                                },
                                {
                                    "id": "orders-card",
                                    "type": "card", 
                                    "props": {"title": "Orders", "value": "2,350"},
                                    "children": []
                                }
                            ]
                        },
                        {
                            "id": "orders-table",
                            "type": "table",
                            "props": {"caption": "Recent Orders"},
                            "children": []
                        }
                    ]
                }
            ],
            components=[],
            theme={
                "primary": "#0f172a",
                "secondary": "#64748b"
            }
        )
        
        # Template 2: E-commerce store
        ecommerce_template = TemplateSchema(
            id="ecommerce-store",
            metadata=TemplateMetadata(
                name="E-commerce Store",
                description="Tienda online completa con catálogo y carrito",
                author="TauseStack Team",
                category=TemplateCategory.ECOMMERCE,
                tags=["ecommerce", "store", "shopping", "shadcn"]
            ),
            configuration={
                "framework": "nextjs",
                "ui_library": "shadcn",
                "typescript": True,
                "tailwind": True,
                "dark_mode": True,
                "responsive": True
            },
            dependencies={
                "npm_packages": ["stripe", "next-auth"],
                "shadcn_components": ["card", "button", "badge", "dialog"]
            },
            pages=[
                {
                    "name": "home",
                    "path": "/",
                    "components": [
                        {
                            "id": "hero-section",
                            "type": "hero",
                            "props": {"title": "Welcome to our Store"},
                            "children": []
                        },
                        {
                            "id": "products-grid",
                            "type": "grid",
                            "children": [
                                {
                                    "id": "product-card",
                                    "type": "card",
                                    "props": {"title": "Product Name", "price": "$99.99"},
                                    "children": []
                                }
                            ]
                        }
                    ]
                }
            ],
            components=[],
            theme={
                "primary": "#059669",
                "secondary": "#10b981"
            }
        )
        
        # Guardar templates de ejemplo
        await self.save_template(dashboard_template)
        await self.save_template(ecommerce_template)
        
        print("Sample templates created successfully!")


# Instancia global
template_registry = TemplateRegistry()