#!/usr/bin/env python3
"""
Script de limpieza para TauseStack antes del despliegue en AWS
Elimina archivos innecesarios, código duplicado y prepara el proyecto para producción
"""

import os
import shutil
import sys
from pathlib import Path
import json
import subprocess
from typing import List, Dict, Set

class TauseStackCleaner:
    def __init__(self):
        self.project_root = Path.cwd()
        self.files_to_delete = []
        self.dirs_to_delete = []
        self.files_cleaned = 0
        self.bytes_saved = 0
        
    def log(self, message: str, level: str = "INFO"):
        """Log con colores"""
        colors = {
            "INFO": "\033[94m",
            "SUCCESS": "\033[92m", 
            "WARNING": "\033[93m",
            "ERROR": "\033[91m",
            "RESET": "\033[0m"
        }
        print(f"{colors.get(level, '')}{message}{colors['RESET']}")
    
    def get_file_size(self, path: Path) -> int:
        """Obtener tamaño de archivo o directorio"""
        if path.is_file():
            return path.stat().st_size
        elif path.is_dir():
            return sum(f.stat().st_size for f in path.rglob('*') if f.is_file())
        return 0
    
    def safe_delete(self, path: Path, is_dir: bool = False):
        """Eliminar archivo o directorio de forma segura"""
        if not path.exists():
            return
            
        size = self.get_file_size(path)
        
        try:
            if is_dir:
                shutil.rmtree(path)
                self.log(f"🗂️  Eliminado directorio: {path}", "SUCCESS")
            else:
                path.unlink()
                self.log(f"🗑️  Eliminado archivo: {path}", "SUCCESS")
            
            self.files_cleaned += 1
            self.bytes_saved += size
            
        except Exception as e:
            self.log(f"❌ Error eliminando {path}: {e}", "ERROR")
    
    def clean_pycache(self):
        """Eliminar todos los archivos __pycache__"""
        self.log("🧹 Limpiando archivos __pycache__...")
        
        pycache_dirs = list(self.project_root.rglob("__pycache__"))
        for pycache_dir in pycache_dirs:
            self.safe_delete(pycache_dir, is_dir=True)
        
        pyc_files = list(self.project_root.rglob("*.pyc"))
        for pyc_file in pyc_files:
            self.safe_delete(pyc_file)
    
    def clean_node_modules(self):
        """Eliminar node_modules innecesarios"""
        self.log("📦 Limpiando node_modules...")
        
        # Solo mantener node_modules en el directorio raíz del frontend
        node_modules_dirs = []
        for nm_dir in self.project_root.rglob("node_modules"):
            # Mantener solo el node_modules principal
            if nm_dir.parent.name not in ["frontend", "."]:
                node_modules_dirs.append(nm_dir)
        
        for nm_dir in node_modules_dirs:
            self.safe_delete(nm_dir, is_dir=True)
    
    def clean_temporary_files(self):
        """Eliminar archivos temporales"""
        self.log("🧽 Limpiando archivos temporales...")
        
        temp_patterns = [
            "*.tmp", "*.temp", "*.log", "*.bak", "*.swp", "*.swo",
            "*~", "*.orig", "*.rej", ".DS_Store", "Thumbs.db"
        ]
        
        for pattern in temp_patterns:
            for temp_file in self.project_root.rglob(pattern):
                self.safe_delete(temp_file)
    
    def clean_development_files(self):
        """Eliminar archivos específicos de desarrollo"""
        self.log("🔧 Limpiando archivos de desarrollo...")
        
        dev_files = [
            ".vscode/settings.json",
            ".idea/",
            "*.code-workspace",
            "debug.log",
            "npm-debug.log*",
            "yarn-debug.log*",
            "yarn-error.log*"
        ]
        
        for pattern in dev_files:
            for dev_file in self.project_root.rglob(pattern):
                if dev_file.exists():
                    self.safe_delete(dev_file, is_dir=dev_file.is_dir())
    
    def clean_test_files(self):
        """Eliminar archivos de test innecesarios para producción"""
        self.log("🧪 Limpiando archivos de test...")
        
        # Mantener solo tests esenciales
        test_dirs_to_keep = {"tests", "test"}
        
        for test_dir in self.project_root.rglob("*test*"):
            if test_dir.is_dir() and test_dir.name not in test_dirs_to_keep:
                # Eliminar directorios de test específicos
                if any(keyword in test_dir.name.lower() for keyword in ["__test__", "spec", "mock"]):
                    self.safe_delete(test_dir, is_dir=True)
    
    def clean_documentation_files(self):
        """Eliminar documentación innecesaria para producción"""
        self.log("📚 Limpiando documentación innecesaria...")
        
        # Mantener solo documentación esencial
        docs_to_delete = [
            "CHANGELOG.md",
            "CONTRIBUTING.md", 
            "CODE_OF_CONDUCT.md",
            "SECURITY.md",
            "docs/development/",
            "docs/tutorials/",
            "*.draft.md"
        ]
        
        for pattern in docs_to_delete:
            for doc_file in self.project_root.rglob(pattern):
                if doc_file.exists():
                    self.safe_delete(doc_file, is_dir=doc_file.is_dir())
    
    def clean_example_files(self):
        """Limpiar archivos de ejemplo innecesarios"""
        self.log("📋 Limpiando archivos de ejemplo...")
        
        # Mantener solo ejemplos esenciales
        example_dirs = list(self.project_root.rglob("example*"))
        for example_dir in example_dirs:
            if example_dir.is_dir():
                # Mantener solo demos esenciales
                essential_examples = ["api_gateway_demo.py", "mcp_complete_demo.py"]
                if not any(essential in str(example_dir) for essential in essential_examples):
                    self.safe_delete(example_dir, is_dir=True)
    
    def clean_duplicate_configs(self):
        """Eliminar archivos de configuración duplicados"""
        self.log("⚙️  Limpiando configuraciones duplicadas...")
        
        # Eliminar configs duplicados
        duplicate_configs = [
            "docker-compose.yml",  # Mantener solo production
            "docker-compose.dev.yml",
            "docker-compose.test.yml",
            "requirements-dev.txt",
            "requirements-test.txt",
            ".env.example",  # Usar environment.template en su lugar
            "config.json",
            "settings.json"
        ]
        
        for config in duplicate_configs:
            config_path = self.project_root / config
            if config_path.exists():
                self.safe_delete(config_path)
    
    def clean_build_artifacts(self):
        """Eliminar artefactos de build"""
        self.log("🏗️  Limpiando artefactos de build...")
        
        build_dirs = [
            "build/", "dist/", ".next/", "out/", 
            "target/", "bin/", "obj/", ".nuxt/"
        ]
        
        for build_dir in build_dirs:
            build_path = self.project_root / build_dir
            if build_path.exists():
                self.safe_delete(build_path, is_dir=True)
    
    def optimize_package_json(self):
        """Optimizar package.json para producción"""
        self.log("📦 Optimizando package.json...")
        
        package_json_path = self.project_root / "package.json"
        if package_json_path.exists():
            try:
                with open(package_json_path, 'r') as f:
                    package_data = json.load(f)
                
                # Eliminar scripts de desarrollo
                dev_scripts = ["test", "test:watch", "dev", "debug", "lint:fix"]
                if "scripts" in package_data:
                    for script in dev_scripts:
                        package_data["scripts"].pop(script, None)
                
                # Eliminar devDependencies para producción
                package_data.pop("devDependencies", None)
                
                with open(package_json_path, 'w') as f:
                    json.dump(package_data, f, indent=2)
                
                self.log("✅ package.json optimizado", "SUCCESS")
                
            except Exception as e:
                self.log(f"❌ Error optimizando package.json: {e}", "ERROR")
    
    def create_production_env(self):
        """Crear archivo .env.production desde template"""
        self.log("🔧 Creando archivo .env.production...")
        
        template_path = self.project_root / "config" / "environment.template"
        aws_template_path = self.project_root / "infrastructure" / "aws" / "environment.aws.template"
        env_prod_path = self.project_root / ".env.production"
        
        if aws_template_path.exists():
            shutil.copy2(aws_template_path, env_prod_path)
            self.log("✅ .env.production creado desde template AWS", "SUCCESS")
        elif template_path.exists():
            shutil.copy2(template_path, env_prod_path)
            self.log("✅ .env.production creado desde template base", "SUCCESS")
        else:
            self.log("⚠️  No se encontró template de environment", "WARNING")
    
    def verify_essential_files(self):
        """Verificar que archivos esenciales estén presentes"""
        self.log("🔍 Verificando archivos esenciales...")
        
        essential_files = [
            "Dockerfile",
            "docker-compose.production.yml",
            "requirements.txt",
            "tausestack/config/settings.py",
            "services/api_gateway.py",
            "services/mcp_client/__init__.py"
        ]
        
        missing_files = []
        for file_path in essential_files:
            if not (self.project_root / file_path).exists():
                missing_files.append(file_path)
        
        if missing_files:
            self.log("❌ Archivos esenciales faltantes:", "ERROR")
            for missing in missing_files:
                self.log(f"   - {missing}", "ERROR")
            return False
        
        self.log("✅ Todos los archivos esenciales presentes", "SUCCESS")
        return True
    
    def generate_report(self):
        """Generar reporte de limpieza"""
        self.log("\n" + "="*60, "INFO")
        self.log("📊 REPORTE DE LIMPIEZA COMPLETADO", "SUCCESS")
        self.log("="*60, "INFO")
        self.log(f"🗑️  Archivos eliminados: {self.files_cleaned}", "INFO")
        self.log(f"💾 Espacio liberado: {self.bytes_saved / 1024 / 1024:.1f} MB", "INFO")
        self.log(f"📁 Directorio del proyecto: {self.project_root}", "INFO")
        self.log("="*60, "INFO")
        
        # Crear reporte detallado
        report_path = self.project_root / "CLEANUP_REPORT.md"
        with open(report_path, 'w') as f:
            f.write(f"""# TauseStack Cleanup Report

## Resumen
- **Archivos eliminados**: {self.files_cleaned}
- **Espacio liberado**: {self.bytes_saved / 1024 / 1024:.1f} MB
- **Fecha**: {subprocess.check_output(['date']).decode().strip()}

## Archivos Eliminados
- Archivos __pycache__ y .pyc
- node_modules innecesarios
- Archivos temporales
- Archivos de desarrollo
- Tests innecesarios
- Documentación de desarrollo
- Ejemplos no esenciales
- Configuraciones duplicadas
- Artefactos de build

## Archivos Mantenidos
- Dockerfile y docker-compose.production.yml
- requirements.txt y pyproject.toml
- Configuración centralizada (config/settings.py)
- Servicios principales
- SDK de TauseStack
- Documentación esencial
- Scripts de producción

## Siguiente Paso
El proyecto está listo para el despliegue en AWS.
""")
        
        self.log(f"📄 Reporte guardado en: {report_path}", "SUCCESS")
    
    def run_cleanup(self):
        """Ejecutar limpieza completa"""
        self.log("🚀 INICIANDO LIMPIEZA DE TAUSESTACK PARA AWS", "INFO")
        self.log("="*60, "INFO")
        
        # Verificar que estamos en el directorio correcto
        if not (self.project_root / "tausestack").exists():
            self.log("❌ Error: No se encontró el directorio tausestack", "ERROR")
            self.log("   Ejecutar desde el directorio raíz del proyecto", "ERROR")
            sys.exit(1)
        
        # Ejecutar limpieza
        self.clean_pycache()
        self.clean_node_modules()
        self.clean_temporary_files()
        self.clean_development_files()
        self.clean_test_files()
        self.clean_documentation_files()
        self.clean_example_files()
        self.clean_duplicate_configs()
        self.clean_build_artifacts()
        self.optimize_package_json()
        self.create_production_env()
        
        # Verificar archivos esenciales
        if not self.verify_essential_files():
            self.log("❌ Limpieza completada con advertencias", "WARNING")
            sys.exit(1)
        
        # Generar reporte
        self.generate_report()
        
        self.log("🎉 LIMPIEZA COMPLETADA EXITOSAMENTE", "SUCCESS")
        self.log("🚀 Proyecto listo para despliegue en AWS", "SUCCESS")

def main():
    """Función principal"""
    cleaner = TauseStackCleaner()
    
    # Confirmar antes de ejecutar
    print("🧹 TauseStack AWS Cleanup Script")
    print("="*40)
    print("Este script eliminará archivos innecesarios para preparar el proyecto para AWS.")
    print("⚠️  ADVERTENCIA: Esta operación no se puede deshacer.")
    
    confirm = input("\n¿Continuar con la limpieza? (y/N): ").strip().lower()
    if confirm not in ['y', 'yes', 'sí', 'si']:
        print("❌ Limpieza cancelada")
        sys.exit(0)
    
    cleaner.run_cleanup()

if __name__ == "__main__":
    main() 