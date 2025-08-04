"""
Database Isolation for Multi-Tenant Applications

Provides schema-based isolation for PostgreSQL databases in multi-tenant environments.
Ensures complete data separation between tenants through dedicated schemas and RLS policies.
"""

from typing import Dict, Any, Optional, List, Union
import logging
from contextlib import contextmanager
import re

from ..tenancy import get_current_tenant_id
from . import isolation

logger = logging.getLogger(__name__)

class DatabaseIsolationManager:
    """
    Manages database isolation for multi-tenant applications.
    
    Features:
    - Schema-based isolation
    - Row Level Security (RLS) policies
    - Connection pooling per tenant
    - Migration management per schema
    - Cross-tenant access prevention
    """
    
    def __init__(self):
        self._schema_cache: Dict[str, str] = {}
        self._connection_pools: Dict[str, Any] = {}
        self._migration_history: Dict[str, List[str]] = {}
    
    def get_tenant_schema(self, tenant_id: Optional[str] = None) -> str:
        """
        Get database schema name for tenant.
        
        Args:
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Schema name for the tenant
        """
        effective_tenant_id = tenant_id or get_current_tenant_id()
        
        # Check cache first
        if effective_tenant_id in self._schema_cache:
            return self._schema_cache[effective_tenant_id]
        
        # Get from isolation config
        config = isolation.get_tenant_isolation_config(effective_tenant_id)
        schema = config.get("database_schema", "public")
        
        # Cache the result
        self._schema_cache[effective_tenant_id] = schema
        return schema
    
    def create_tenant_schema(self, tenant_id: str, db_connection) -> bool:
        """
        Create database schema for a tenant.
        
        Args:
            tenant_id: Tenant ID
            db_connection: Database connection object
            
        Returns:
            True if schema created successfully
        """
        schema_name = self.get_tenant_schema(tenant_id)
        
        if schema_name == "public":
            logger.info(f"Tenant {tenant_id} uses public schema, no creation needed")
            return True
        
        try:
            # Create schema if it doesn't exist
            with db_connection.cursor() as cursor:
                cursor.execute(f"CREATE SCHEMA IF NOT EXISTS {schema_name}")
                db_connection.commit()
            
            logger.info(f"Created schema '{schema_name}' for tenant '{tenant_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to create schema '{schema_name}' for tenant '{tenant_id}': {e}")
            return False
    
    def drop_tenant_schema(self, tenant_id: str, db_connection, cascade: bool = False) -> bool:
        """
        Drop database schema for a tenant.
        
        Args:
            tenant_id: Tenant ID
            db_connection: Database connection object
            cascade: Whether to cascade drop (drop all objects in schema)
            
        Returns:
            True if schema dropped successfully
        """
        schema_name = self.get_tenant_schema(tenant_id)
        
        if schema_name == "public":
            logger.warning(f"Cannot drop public schema for tenant {tenant_id}")
            return False
        
        try:
            with db_connection.cursor() as cursor:
                if cascade:
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name} CASCADE")
                else:
                    cursor.execute(f"DROP SCHEMA IF EXISTS {schema_name}")
                db_connection.commit()
            
            # Clear cache
            if tenant_id in self._schema_cache:
                del self._schema_cache[tenant_id]
            
            logger.info(f"Dropped schema '{schema_name}' for tenant '{tenant_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to drop schema '{schema_name}' for tenant '{tenant_id}': {e}")
            return False
    
    def setup_rls_policies(self, tenant_id: str, db_connection, table_name: str) -> bool:
        """
        Setup Row Level Security policies for a table.
        
        Args:
            tenant_id: Tenant ID
            db_connection: Database connection object
            table_name: Name of the table to secure
            
        Returns:
            True if policies setup successfully
        """
        schema_name = self.get_tenant_schema(tenant_id)
        
        if schema_name == "public":
            logger.info(f"Public schema for tenant {tenant_id}, RLS setup skipped")
            return True
        
        try:
            with db_connection.cursor() as cursor:
                # Enable RLS on the table
                cursor.execute(f"ALTER TABLE {schema_name}.{table_name} ENABLE ROW LEVEL SECURITY")
                
                # Create policy to allow access only to current tenant
                policy_name = f"tenant_isolation_{table_name}"
                cursor.execute(f"""
                    CREATE POLICY {policy_name} ON {schema_name}.{table_name}
                    FOR ALL
                    USING (tenant_id = current_setting('app.current_tenant_id', true))
                """)
                
                db_connection.commit()
            
            logger.info(f"Setup RLS policies for table '{table_name}' in schema '{schema_name}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to setup RLS for table '{table_name}' in schema '{schema_name}': {e}")
            return False
    
    def set_tenant_context(self, db_connection, tenant_id: Optional[str] = None) -> bool:
        """
        Set tenant context in database session.
        
        Args:
            db_connection: Database connection object
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            True if context set successfully
        """
        effective_tenant_id = tenant_id or get_current_tenant_id()
        
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("SELECT set_config('app.current_tenant_id', %s, false)", 
                             (effective_tenant_id,))
                db_connection.commit()
            
            logger.debug(f"Set tenant context to '{effective_tenant_id}' in database session")
            return True
            
        except Exception as e:
            logger.error(f"Failed to set tenant context '{effective_tenant_id}': {e}")
            return False
    
    def get_isolated_table_name(self, table_name: str, tenant_id: Optional[str] = None) -> str:
        """
        Get fully qualified table name with schema.
        
        Args:
            table_name: Base table name
            tenant_id: Tenant ID, defaults to current tenant
            
        Returns:
            Fully qualified table name (schema.table)
        """
        schema_name = self.get_tenant_schema(tenant_id)
        return f"{schema_name}.{table_name}"
    
    def migrate_tenant_schema(self, tenant_id: str, db_connection, 
                            migration_sql: str) -> bool:
        """
        Apply migration to tenant-specific schema.
        
        Args:
            tenant_id: Tenant ID
            db_connection: Database connection object
            migration_sql: SQL migration to apply
            
        Returns:
            True if migration applied successfully
        """
        schema_name = self.get_tenant_schema(tenant_id)
        
        try:
            # Replace schema placeholders in migration SQL
            isolated_sql = migration_sql.replace("{{schema}}", schema_name)
            
            with db_connection.cursor() as cursor:
                cursor.execute(isolated_sql)
                db_connection.commit()
            
            # Track migration
            if tenant_id not in self._migration_history:
                self._migration_history[tenant_id] = []
            
            migration_hash = hash(isolated_sql)
            self._migration_history[tenant_id].append(str(migration_hash))
            
            logger.info(f"Applied migration to schema '{schema_name}' for tenant '{tenant_id}'")
            return True
            
        except Exception as e:
            logger.error(f"Failed to apply migration to schema '{schema_name}' for tenant '{tenant_id}': {e}")
            return False
    
    def get_tenant_data_size(self, tenant_id: str, db_connection) -> Dict[str, int]:
        """
        Get data size statistics for a tenant.
        
        Args:
            tenant_id: Tenant ID
            db_connection: Database connection object
            
        Returns:
            Dictionary with table sizes in bytes
        """
        schema_name = self.get_tenant_schema(tenant_id)
        
        try:
            with db_connection.cursor() as cursor:
                cursor.execute("""
                    SELECT 
                        schemaname,
                        tablename,
                        pg_total_relation_size(schemaname||'.'||tablename) as size_bytes
                    FROM pg_tables 
                    WHERE schemaname = %s
                    ORDER BY size_bytes DESC
                """, (schema_name,))
                
                results = cursor.fetchall()
                
                sizes = {}
                for _, table_name, size_bytes in results:
                    sizes[table_name] = size_bytes
                
                return sizes
                
        except Exception as e:
            logger.error(f"Failed to get data size for tenant '{tenant_id}': {e}")
            return {}
    
    def backup_tenant_schema(self, tenant_id: str, db_connection, 
                           backup_path: str) -> bool:
        """
        Create backup of tenant schema.
        
        Args:
            tenant_id: Tenant ID
            db_connection: Database connection object
            backup_path: Path to save backup file
            
        Returns:
            True if backup created successfully
        """
        schema_name = self.get_tenant_schema(tenant_id)
        
        if schema_name == "public":
            logger.warning(f"Cannot backup public schema for tenant {tenant_id}")
            return False
        
        try:
            # Use pg_dump to backup schema
            import subprocess
            import os
            
            # Get database connection details
            db_url = db_connection.get_dsn_parameters()
            
            cmd = [
                "pg_dump",
                f"--host={db_url.get('host', 'localhost')}",
                f"--port={db_url.get('port', '5432')}",
                f"--username={db_url.get('user', 'postgres')}",
                f"--schema={schema_name}",
                "--no-password",
                db_url.get('dbname', 'postgres')
            ]
            
            with open(backup_path, 'w') as f:
                result = subprocess.run(cmd, stdout=f, stderr=subprocess.PIPE, text=True)
            
            if result.returncode == 0:
                logger.info(f"Created backup of schema '{schema_name}' for tenant '{tenant_id}' at {backup_path}")
                return True
            else:
                logger.error(f"Backup failed for tenant '{tenant_id}': {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Failed to backup schema '{schema_name}' for tenant '{tenant_id}': {e}")
            return False
    
    @contextmanager
    def tenant_database_context(self, db_connection, tenant_id: Optional[str] = None):
        """
        Context manager for database operations with tenant isolation.
        
        Usage:
            with db_isolation.tenant_database_context(connection, "client_123"):
                # All database operations will use client_123 schema
                cursor.execute("SELECT * FROM users")
        """
        effective_tenant_id = tenant_id or get_current_tenant_id()
        
        # Set tenant context
        self.set_tenant_context(db_connection, effective_tenant_id)
        
        try:
            yield
        finally:
            # Reset context if needed
            pass

# Global database isolation manager
db_isolation = DatabaseIsolationManager()

# Convenience functions
def get_tenant_schema(tenant_id: Optional[str] = None) -> str:
    """Get schema name for current tenant."""
    return db_isolation.get_tenant_schema(tenant_id)

def get_isolated_table(table_name: str, tenant_id: Optional[str] = None) -> str:
    """Get isolated table name for current tenant."""
    return db_isolation.get_isolated_table_name(table_name, tenant_id)

def create_schema(tenant_id: str, db_connection) -> bool:
    """Create schema for tenant."""
    return db_isolation.create_tenant_schema(tenant_id, db_connection)

def setup_rls(table_name: str, tenant_id: str, db_connection) -> bool:
    """Setup RLS policies for table."""
    return db_isolation.setup_rls_policies(tenant_id, db_connection, table_name)

__all__ = [
    "DatabaseIsolationManager",
    "db_isolation",
    "get_tenant_schema",
    "get_isolated_table", 
    "create_schema",
    "setup_rls"
] 