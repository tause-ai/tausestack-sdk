"""
Template Engine Core - Generación de código desde templates
"""
import os
import json
from typing import Dict, List, Any, Optional
from pathlib import Path
from jinja2 import Environment, FileSystemLoader, Template
from ..schemas.template_schema import (
    TemplateSchema, ComponentSchema, PageSchema, 
    TemplateGenerationRequest, TemplateGenerationResponse,
    ComponentType, UILibrary, Framework
)


class ShadcnComponentMapper:
    """Mapea componentes shadcn/ui a código React/TypeScript"""
    
    COMPONENT_IMPORTS = {
        ComponentType.BUTTON: 'import { Button } from "@/components/ui/button"',
        ComponentType.CARD: 'import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from "@/components/ui/card"',
        ComponentType.INPUT: 'import { Input } from "@/components/ui/input"',
        ComponentType.SELECT: 'import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"',
        ComponentType.DIALOG: 'import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle, DialogTrigger } from "@/components/ui/dialog"',
        ComponentType.FORM: 'import { Form, FormControl, FormDescription, FormField, FormItem, FormLabel, FormMessage } from "@/components/ui/form"',
        ComponentType.TABLE: 'import { Table, TableBody, TableCaption, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"',
        ComponentType.BADGE: 'import { Badge } from "@/components/ui/badge"',
        ComponentType.ALERT_DIALOG: 'import { AlertDialog, AlertDialogAction, AlertDialogCancel, AlertDialogContent, AlertDialogDescription, AlertDialogFooter, AlertDialogHeader, AlertDialogTitle, AlertDialogTrigger } from "@/components/ui/alert-dialog"',
        ComponentType.SHEET: 'import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle, SheetTrigger } from "@/components/ui/sheet"',
    }
    
    COMPONENT_TEMPLATES = {
        ComponentType.BUTTON: """
<Button variant="{variant}" {props}>
  {children}
</Button>
""",
        ComponentType.CARD: """
<Card {props}>
  <CardHeader>
    <CardTitle>{title}</CardTitle>
    <CardDescription>{description}</CardDescription>
  </CardHeader>
  <CardContent>
    {children}
  </CardContent>
  {footer}
</Card>
""",
        ComponentType.INPUT: """
<Input
  type="{input_type}"
  placeholder="{placeholder}"
  {props}
/>
""",
        ComponentType.TABLE: """
<Table {props}>
  <TableCaption>{caption}</TableCaption>
  <TableHeader>
    <TableRow>
      {headers}
    </TableRow>
  </TableHeader>
  <TableBody>
    {rows}
  </TableBody>
</Table>
""",
    }
    
    @classmethod
    def get_imports(cls, components: List[ComponentSchema]) -> List[str]:
        """Obtiene imports necesarios para los componentes"""
        imports = set()
        for component in components:
            if component.type in cls.COMPONENT_IMPORTS:
                imports.add(cls.COMPONENT_IMPORTS[component.type])
        return list(imports)
    
    @classmethod
    def render_component(cls, component: ComponentSchema) -> str:
        """Renderiza un componente individual"""
        if component.type not in cls.COMPONENT_TEMPLATES:
            return f"<!-- Component {component.type} not implemented -->"
        
        template_str = cls.COMPONENT_TEMPLATES[component.type]
        template = Template(template_str)
        
        # Procesar props
        props_str = " ".join([f'{k}="{v}"' for k, v in component.props.items()])
        
        # Procesar children
        children_str = ""
        if component.children:
            children_str = "\n".join([cls.render_component(child) for child in component.children])
        
        return template.render(
            variant=component.variant,
            props=props_str,
            children=children_str,
            **component.props
        )


class TemplateEngine:
    """Motor principal de generación de templates"""
    
    def __init__(self, templates_dir: str = "templates"):
        self.templates_dir = Path(templates_dir)
        self.jinja_env = Environment(
            loader=FileSystemLoader(str(self.templates_dir)),
            autoescape=True
        )
        self.component_mapper = ShadcnComponentMapper()
    
    def load_template(self, template_id: str) -> Optional[TemplateSchema]:
        """Carga un template desde el registry"""
        template_path = self.templates_dir / f"{template_id}.json"
        if not template_path.exists():
            return None
        
        with open(template_path, 'r', encoding='utf-8') as f:
            template_data = json.load(f)
        
        return TemplateSchema(**template_data)
    
    def generate_page(self, page: PageSchema, template: TemplateSchema) -> str:
        """Genera código React/TypeScript para una página"""
        # Obtener imports necesarios
        all_components = []
        for component in page.components:
            all_components.extend(self._flatten_components(component))
        
        imports = self.component_mapper.get_imports(all_components)
        
        # Generar componentes
        components_jsx = []
        for component in page.components:
            components_jsx.append(self.component_mapper.render_component(component))
        
        # Template de página
        page_template = """
{imports}
import React from 'react'

interface {page_name}Props {{
  // Props del componente
}}

export default function {page_name}({{ }: {page_name}Props) {{
  return (
    <div className="min-h-screen bg-background">
      {components}
    </div>
  )
}}
"""
        
        return page_template.format(
            imports="\n".join(imports),
            page_name=page.name.replace("-", "").replace("_", "").title(),
            components="\n      ".join(components_jsx)
        )
    
    def generate_project(self, request: TemplateGenerationRequest) -> TemplateGenerationResponse:
        """Genera proyecto completo desde template"""
        template = self.load_template(request.template_id)
        if not template:
            return TemplateGenerationResponse(
                success=False,
                project_id="",
                generated_files=[],
                errors=[f"Template {request.template_id} not found"]
            )
        
        try:
            project_id = f"{request.project_name}-{request.template_id}"
            generated_files = []
            
            # Crear estructura de proyecto
            project_dir = Path(f"generated/{project_id}")
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Generar package.json
            package_json = self._generate_package_json(template, request.project_name)
            package_json_path = project_dir / "package.json"
            with open(package_json_path, 'w') as f:
                json.dump(package_json, f, indent=2)
            generated_files.append(str(package_json_path))
            
            # Generar páginas
            pages_dir = project_dir / "src" / "app"
            pages_dir.mkdir(parents=True, exist_ok=True)
            
            for page in template.pages:
                page_code = self.generate_page(page, template)
                page_path = pages_dir / f"{page.name}.tsx"
                with open(page_path, 'w') as f:
                    f.write(page_code)
                generated_files.append(str(page_path))
            
            # Generar configuración
            self._generate_config_files(project_dir, template)
            
            # Generar componentes shadcn/ui
            self._copy_shadcn_components(project_dir, template)
            
            return TemplateGenerationResponse(
                success=True,
                project_id=project_id,
                generated_files=generated_files,
                preview_url=f"/preview/{project_id}",
                deployment_url=None
            )
            
        except Exception as e:
            return TemplateGenerationResponse(
                success=False,
                project_id="",
                generated_files=[],
                errors=[str(e)]
            )
    
    def _flatten_components(self, component: ComponentSchema) -> List[ComponentSchema]:
        """Aplana la jerarquía de componentes"""
        result = [component]
        for child in component.children:
            result.extend(self._flatten_components(child))
        return result
    
    def _generate_package_json(self, template: TemplateSchema, project_name: str) -> Dict[str, Any]:
        """Genera package.json con dependencias shadcn/ui"""
        base_dependencies = {
            "react": "^18.0.0",
            "react-dom": "^18.0.0",
            "next": "^14.0.0",
            "@types/react": "^18.0.0",
            "@types/react-dom": "^18.0.0",
            "typescript": "^5.0.0",
            "tailwindcss": "^3.3.0",
            "autoprefixer": "^10.4.0",
            "postcss": "^8.4.0",
            "class-variance-authority": "^0.7.0",
            "clsx": "^2.0.0",
            "tailwind-merge": "^2.0.0",
            "lucide-react": "^0.400.0"
        }
        
        # Agregar dependencias específicas del template
        for package in template.dependencies.npm_packages:
            base_dependencies[package] = "latest"
        
        # Agregar dependencias de shadcn/ui
        shadcn_deps = {
            "@radix-ui/react-dialog": "^1.0.5",
            "@radix-ui/react-select": "^2.0.0",
            "@radix-ui/react-slot": "^1.0.2",
            "@radix-ui/react-label": "^2.0.2",
            "@radix-ui/react-alert-dialog": "^1.0.5",
        }
        base_dependencies.update(shadcn_deps)
        
        return {
            "name": project_name.lower().replace(" ", "-"),
            "version": "0.1.0",
            "private": True,
            "scripts": {
                "dev": "next dev",
                "build": "next build",
                "start": "next start",
                "lint": "next lint"
            },
            "dependencies": base_dependencies,
            "devDependencies": {
                "@types/node": "^20.0.0",
                "eslint": "^8.0.0",
                "eslint-config-next": "^14.0.0"
            }
        }
    
    def _generate_config_files(self, project_dir: Path, template: TemplateSchema):
        """Genera archivos de configuración (tailwind.config.js, etc.)"""
        # tailwind.config.js
        tailwind_config = '''/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: ["class"],
  content: [
    './pages/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
    './app/**/*.{ts,tsx}',
    './src/**/*.{ts,tsx}',
  ],
  theme: {
    container: {
      center: true,
      padding: "2rem",
      screens: {
        "2xl": "1400px",
      },
    },
    extend: {
      colors: {
        border: "hsl(var(--border))",
        input: "hsl(var(--input))",
        ring: "hsl(var(--ring))",
        background: "hsl(var(--background))",
        foreground: "hsl(var(--foreground))",
        primary: {
          DEFAULT: "hsl(var(--primary))",
          foreground: "hsl(var(--primary-foreground))",
        },
        secondary: {
          DEFAULT: "hsl(var(--secondary))",
          foreground: "hsl(var(--secondary-foreground))",
        },
        destructive: {
          DEFAULT: "hsl(var(--destructive))",
          foreground: "hsl(var(--destructive-foreground))",
        },
        muted: {
          DEFAULT: "hsl(var(--muted))",
          foreground: "hsl(var(--muted-foreground))",
        },
        accent: {
          DEFAULT: "hsl(var(--accent))",
          foreground: "hsl(var(--accent-foreground))",
        },
        popover: {
          DEFAULT: "hsl(var(--popover))",
          foreground: "hsl(var(--popover-foreground))",
        },
        card: {
          DEFAULT: "hsl(var(--card))",
          foreground: "hsl(var(--card-foreground))",
        },
      },
      borderRadius: {
        lg: "var(--radius)",
        md: "calc(var(--radius) - 2px)",
        sm: "calc(var(--radius) - 4px)",
      },
      keyframes: {
        "accordion-down": {
          from: { height: 0 },
          to: { height: "var(--radix-accordion-content-height)" },
        },
        "accordion-up": {
          from: { height: "var(--radix-accordion-content-height)" },
          to: { height: 0 },
        },
      },
      animation: {
        "accordion-down": "accordion-down 0.2s ease-out",
        "accordion-up": "accordion-up 0.2s ease-out",
      },
    },
  },
  plugins: [require("tailwindcss-animate")],
}'''
        
        with open(project_dir / "tailwind.config.js", 'w') as f:
            f.write(tailwind_config)
    
    def _copy_shadcn_components(self, project_dir: Path, template: TemplateSchema):
        """Copia componentes shadcn/ui necesarios"""
        components_dir = project_dir / "src" / "components" / "ui"
        components_dir.mkdir(parents=True, exist_ok=True)
        
        # Aquí copiaríamos los componentes shadcn/ui desde nuestro frontend
        # Por ahora, creamos un placeholder
        utils_path = project_dir / "src" / "lib" / "utils.ts"
        utils_path.parent.mkdir(parents=True, exist_ok=True)
        
        utils_content = '''import { type ClassValue, clsx } from "clsx"
import { twMerge } from "tailwind-merge"

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs))
}'''
        
        with open(utils_path, 'w') as f:
            f.write(utils_content)