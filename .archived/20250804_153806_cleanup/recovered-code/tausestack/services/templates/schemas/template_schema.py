"""
Template schemas con soporte para shadcn/ui components
"""
from typing import Dict, List, Optional, Any, Union
from pydantic import BaseModel, Field
from enum import Enum


class UILibrary(str, Enum):
    SHADCN = "shadcn"
    MATERIAL_UI = "material-ui"
    CHAKRA_UI = "chakra-ui"
    ANTD = "antd"


class Framework(str, Enum):
    NEXTJS = "nextjs"
    REACT = "react"
    VUE = "vue"
    SVELTE = "svelte"


class TemplateCategory(str, Enum):
    BUSINESS = "business"
    ECOMMERCE = "ecommerce"
    CONTENT = "content"
    TOOLS = "tools"
    DASHBOARD = "dashboard"
    LANDING = "landing"


class ComponentType(str, Enum):
    # shadcn/ui components
    BUTTON = "button"
    CARD = "card"
    INPUT = "input"
    SELECT = "select"
    DIALOG = "dialog"
    FORM = "form"
    TABLE = "table"
    BADGE = "badge"
    ALERT_DIALOG = "alert-dialog"
    SHEET = "sheet"
    # Layout components
    CONTAINER = "container"
    GRID = "grid"
    FLEX = "flex"
    # Custom components
    NAVBAR = "navbar"
    SIDEBAR = "sidebar"
    FOOTER = "footer"
    HERO = "hero"
    FEATURE_GRID = "feature-grid"


class ComponentVariant(BaseModel):
    """Variantes de componentes shadcn/ui"""
    name: str
    props: Dict[str, Any] = Field(default_factory=dict)
    styles: Dict[str, str] = Field(default_factory=dict)


class ComponentSchema(BaseModel):
    """Schema para componentes individuales"""
    id: str
    type: ComponentType
    variant: str = "default"
    props: Dict[str, Any] = Field(default_factory=dict)
    styles: Dict[str, str] = Field(default_factory=dict)
    children: List['ComponentSchema'] = Field(default_factory=list)
    conditional_rendering: Optional[str] = None
    data_binding: Optional[str] = None


class PageSchema(BaseModel):
    """Schema para páginas completas"""
    name: str
    path: str
    components: List[ComponentSchema]
    layout: Optional[str] = "default"
    metadata: Dict[str, Any] = Field(default_factory=dict)
    auth_required: bool = False


class TemplateMetadata(BaseModel):
    """Metadata del template"""
    name: str
    description: str
    version: str = "1.0.0"
    author: str
    tags: List[str] = Field(default_factory=list)
    category: TemplateCategory
    subcategory: Optional[str] = None
    preview_image: Optional[str] = None
    demo_url: Optional[str] = None
    documentation_url: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


class TemplateDependencies(BaseModel):
    """Dependencias del template"""
    npm_packages: List[str] = Field(default_factory=list)
    python_packages: List[str] = Field(default_factory=list)
    shadcn_components: List[str] = Field(default_factory=list)
    external_apis: List[str] = Field(default_factory=list)


class TemplateConfiguration(BaseModel):
    """Configuración del template"""
    framework: Framework = Framework.NEXTJS
    ui_library: UILibrary = UILibrary.SHADCN
    typescript: bool = True
    tailwind: bool = True
    dark_mode: bool = True
    responsive: bool = True
    pwa: bool = False
    seo_optimized: bool = True


class TemplateSchema(BaseModel):
    """Schema completo del template"""
    id: str
    metadata: TemplateMetadata
    configuration: TemplateConfiguration
    dependencies: TemplateDependencies
    pages: List[PageSchema]
    components: List[ComponentSchema] = Field(default_factory=list)  # Componentes reutilizables
    theme: Dict[str, Any] = Field(default_factory=dict)
    environment_variables: List[str] = Field(default_factory=list)
    database_schema: Optional[Dict[str, Any]] = None
    api_routes: List[Dict[str, Any]] = Field(default_factory=list)


class TemplateGenerationRequest(BaseModel):
    """Request para generar código desde template"""
    template_id: str
    project_name: str
    customizations: Dict[str, Any] = Field(default_factory=dict)
    theme_overrides: Dict[str, Any] = Field(default_factory=dict)
    tenant_id: Optional[str] = None


class TemplateGenerationResponse(BaseModel):
    """Response de generación de template"""
    success: bool
    project_id: str
    generated_files: List[str]
    preview_url: Optional[str] = None
    deployment_url: Optional[str] = None
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)


# Enable forward references
ComponentSchema.model_rebuild() 