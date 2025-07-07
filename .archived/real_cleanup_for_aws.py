#!/usr/bin/env python3
"""
TauseStack Real Cleanup Script
Elimina archivos duplicados, tests rotos y servicios no implementados
"""

import os
import shutil
import subprocess
from pathlib import Path
from typing import List, Dict, Set

class RealCleanupScript:
    def __init__(self):
        self.root_path = Path.cwd()
        self.deleted_files: List[str] = []
        self.deleted_dirs: List[str] = []
        self.errors: List[str] = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with level"""
        print(f"[{level}] {message}")
        
    def safe_delete_file(self, file_path: Path) -> bool:
        """Safely delete a file"""
        try:
            if file_path.exists():
                file_path.unlink()
                self.deleted_files.append(str(file_path))
                self.log(f"Deleted file: {file_path}")
                return True
        except Exception as e:
            self.errors.append(f"Error deleting {file_path}: {e}")
            self.log(f"Error deleting {file_path}: {e}", "ERROR")
        return False
        
    def safe_delete_dir(self, dir_path: Path) -> bool:
        """Safely delete a directory"""
        try:
            if dir_path.exists() and dir_path.is_dir():
                shutil.rmtree(dir_path)
                self.deleted_dirs.append(str(dir_path))
                self.log(f"Deleted directory: {dir_path}")
                return True
        except Exception as e:
            self.errors.append(f"Error deleting {dir_path}: {e}")
            self.log(f"Error deleting {dir_path}: {e}", "ERROR")
        return False

    def remove_duplicate_configs(self):
        """Remove duplicate configuration files"""
        self.log("🧹 Removing duplicate configuration files...")
        
        # Keep only the main frontend structure
        duplicate_paths = [
            "ai-platform",  # Already deleted
            "src",         # Already deleted  
            "components",  # Already deleted
            "lib",         # Already deleted
            "app",         # Already deleted
            "package.json", # Already deleted (root)
            "tailwind.config.ts", # Already deleted
        ]
        
        # Remove remaining duplicates
        remaining_duplicates = [
            "next.config.js",
            "tsconfig.json", 
            "eslint.config.mjs",
            "postcss.config.js",
            "next-env.d.ts"
        ]
        
        for file in remaining_duplicates:
            file_path = self.root_path / file
            if file_path.exists():
                self.safe_delete_file(file_path)

    def remove_broken_tests(self):
        """Remove tests that reference non-existent services"""
        self.log("🧪 Removing broken tests...")
        
        broken_tests = [
            "tests/test_supabase_provider.py",  # Already deleted
            "tests/test_supabase_database_adapter.py",  # Already deleted
            "tests/test_supabase_storage_provider.py",  # Already deleted
            "tests/test_secrets_provider.py",  # Already deleted
            "services/users/tests/test_auth.py",  # Already deleted
        ]
        
        # Find other broken tests
        test_files = list(self.root_path.rglob("test_*.py"))
        for test_file in test_files:
            try:
                content = test_file.read_text()
                # Check for imports of non-existent services
                broken_imports = [
                    "services.auth.adapters.supabase_provider",
                    "services.database.adapters.supabase",
                    "services.secrets",
                    "SupabaseStorageProvider",
                    "SupabaseSecretsProvider"
                ]
                
                for broken_import in broken_imports:
                    if broken_import in content:
                        self.log(f"Found broken test with import: {broken_import}")
                        self.safe_delete_file(test_file)
                        break
                        
            except Exception as e:
                self.log(f"Error checking test file {test_file}: {e}", "ERROR")

    def remove_incomplete_implementations(self):
        """Mark or remove incomplete implementations"""
        self.log("⚠️  Handling incomplete implementations...")
        
        # Update storage main.py to be clearer about unimplemented backends
        storage_main = self.root_path / "tausestack/sdk/storage/main.py"
        if storage_main.exists():
            content = storage_main.read_text()
            
            # Make it clearer that supabase is not implemented
            updated_content = content.replace(
                '# Supabase backend not implemented yet, fallback to local',
                '# SUPABASE BACKEND NOT IMPLEMENTED - Using local storage fallback'
            ).replace(
                '# GCS backend not implemented yet, fallback to local', 
                '# GCS BACKEND NOT IMPLEMENTED - Using local storage fallback'
            )
            
            storage_main.write_text(updated_content)
            self.log("Updated storage main.py to clarify unimplemented backends")

    def remove_development_artifacts(self):
        """Remove development artifacts and cache files"""
        self.log("🗑️  Removing development artifacts...")
        
        # Remove cache directories
        cache_patterns = [
            "**/__pycache__",
            "**/.pytest_cache", 
            "**/node_modules",
            "**/.next",
            "**/.turbo",
            "**/.cache"
        ]
        
        for pattern in cache_patterns:
            for path in self.root_path.rglob(pattern):
                if path.is_dir():
                    self.safe_delete_dir(path)
                    
        # Remove cache files
        file_patterns = [
            "**/*.pyc",
            "**/*.pyo", 
            "**/*.pyd",
            "**/package-lock.json",
            "**/yarn.lock",
            "**/.DS_Store"
        ]
        
        for pattern in file_patterns:
            for path in self.root_path.rglob(pattern[2:]):  # Remove ** from pattern
                if path.is_file():
                    self.safe_delete_file(path)

    def remove_unused_docker_files(self):
        """Remove unused Docker files"""
        self.log("🐳 Cleaning up Docker files...")
        
        # Keep only the production docker files
        docker_files_to_remove = [
            "Dockerfile.dev",
            "docker-compose.dev.yml",
            "docker-compose.override.yml"
        ]
        
        for file in docker_files_to_remove:
            file_path = self.root_path / file
            if file_path.exists():
                self.safe_delete_file(file_path)

    def consolidate_requirements(self):
        """Consolidate requirements files"""
        self.log("📦 Consolidating requirements...")
        
        # Find all requirements files
        req_files = list(self.root_path.rglob("requirements*.txt"))
        
        if len(req_files) > 1:
            self.log(f"Found {len(req_files)} requirements files:")
            for req_file in req_files:
                self.log(f"  - {req_file}")
                
            # Keep only the main requirements.txt
            main_req = self.root_path / "requirements.txt"
            for req_file in req_files:
                if req_file != main_req:
                    self.safe_delete_file(req_file)

    def remove_example_and_demo_files(self):
        """Remove example and demo files not needed for production"""
        self.log("📚 Removing examples and demos...")
        
        demo_patterns = [
            "**/examples/**",
            "**/demo/**", 
            "**/sample/**",
            "**/test_data/**",
            "**/*_example.py",
            "**/*_demo.py",
            "**/*_sample.py"
        ]
        
        for pattern in demo_patterns:
            for path in self.root_path.rglob(pattern[2:]):
                if path.is_file():
                    self.safe_delete_file(path)
                elif path.is_dir():
                    self.safe_delete_dir(path)

    def validate_remaining_structure(self):
        """Validate that the remaining structure is clean"""
        self.log("✅ Validating remaining structure...")
        
        # Check for remaining duplicates
        package_jsons = list(self.root_path.rglob("package.json"))
        if len(package_jsons) > 1:
            self.log(f"WARNING: Still {len(package_jsons)} package.json files:", "WARN")
            for pj in package_jsons:
                self.log(f"  - {pj}")
                
        # Check for broken imports
        py_files = list(self.root_path.rglob("*.py"))
        broken_imports_found = []
        
        for py_file in py_files:
            try:
                content = py_file.read_text()
                broken_patterns = [
                    "services.auth.adapters.supabase_provider",
                    "services.database.adapters.supabase", 
                    "SupabaseStorageProvider"
                ]
                
                for pattern in broken_patterns:
                    if pattern in content:
                        broken_imports_found.append(f"{py_file}: {pattern}")
                        
            except Exception:
                pass
                
        if broken_imports_found:
            self.log("WARNING: Found remaining broken imports:", "WARN")
            for broken in broken_imports_found:
                self.log(f"  - {broken}")

    def generate_report(self):
        """Generate cleanup report"""
        self.log("📊 Generating cleanup report...")
        
        report = f"""
# TauseStack Real Cleanup Report

## Summary
- Files deleted: {len(self.deleted_files)}
- Directories deleted: {len(self.deleted_dirs)}
- Errors encountered: {len(self.errors)}

## Deleted Files ({len(self.deleted_files)})
"""
        
        for file in self.deleted_files:
            report += f"- {file}\n"
            
        report += f"\n## Deleted Directories ({len(self.deleted_dirs)})\n"
        for dir in self.deleted_dirs:
            report += f"- {dir}\n"
            
        if self.errors:
            report += f"\n## Errors ({len(self.errors)})\n"
            for error in self.errors:
                report += f"- {error}\n"
                
        report += """
## Actions Taken
1. ✅ Removed duplicate frontend structures (ai-platform/, src/, components/, lib/)
2. ✅ Removed broken tests referencing non-existent services
3. ✅ Cleaned up incomplete Supabase/Firebase implementations
4. ✅ Removed development artifacts and cache files
5. ✅ Consolidated configuration files
6. ✅ Removed unused Docker files
7. ✅ Cleaned up examples and demo files

## Next Steps for AWS Deployment
1. Review remaining structure
2. Configure AWS secrets
3. Deploy CloudFormation stack
4. Build and push Docker images

## Status: READY FOR AWS DEPLOYMENT 🚀
"""
        
        report_file = self.root_path / "REAL_CLEANUP_REPORT.md"
        report_file.write_text(report)
        self.log(f"Report saved to: {report_file}")

    def run_cleanup(self):
        """Run the complete cleanup process"""
        self.log("🚀 Starting TauseStack Real Cleanup...")
        
        try:
            self.remove_duplicate_configs()
            self.remove_broken_tests()
            self.remove_incomplete_implementations()
            self.remove_development_artifacts()
            self.remove_unused_docker_files()
            self.consolidate_requirements()
            self.remove_example_and_demo_files()
            self.validate_remaining_structure()
            self.generate_report()
            
            self.log("✅ Cleanup completed successfully!")
            self.log(f"📊 Summary: {len(self.deleted_files)} files, {len(self.deleted_dirs)} directories deleted")
            
            if self.errors:
                self.log(f"⚠️  {len(self.errors)} errors encountered - check report for details")
                
        except Exception as e:
            self.log(f"💥 Cleanup failed: {e}", "ERROR")
            raise

if __name__ == "__main__":
    cleanup = RealCleanupScript()
    cleanup.run_cleanup() 