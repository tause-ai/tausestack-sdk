import os
import sys
from importlib import import_module
from logging.config import fileConfig

import asyncio
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.sql.schema import MetaData # Import MetaData for type checking

from alembic import context

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# --- TauseStack SDK Customizations ---
# Adjust sys.path to include project root for importing user's models
# env.py is in project_root/tausestack/sdk/database/migrations_alembic/
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

def get_user_metadata() -> MetaData | None:
    """
    Imports and returns the SQLAlchemy MetaData object from the user's application.
    The path to the MetaData object is specified by the environment variable
    TAUSESTACK_ALEMBIC_METADATA_TARGET (e.g., "myapp.models:Base.metadata").
    """
    metadata_target_str = os.getenv("TAUSESTACK_ALEMBIC_METADATA_TARGET")
    if not metadata_target_str:
        print(
            "Error: TAUSESTACK_ALEMBIC_METADATA_TARGET environment variable not set.\n"
            "Please set it to the import path of your SQLAlchemy MetaData object\n"
            "(e.g., 'myapp.models:Base.metadata' or 'myapp.db_setup:metadata_obj')."
        )
        return None

    try:
        module_path, object_path_str = metadata_target_str.split(":", 1)
        imported_module = import_module(module_path)
        
        metadata_obj = imported_module
        for attr_name in object_path_str.split("."):
            metadata_obj = getattr(metadata_obj, attr_name)
        
        if not isinstance(metadata_obj, MetaData):
           print(f"Error: TAUSESTACK_ALEMBIC_METADATA_TARGET ('{metadata_target_str}') "
                 f"did not resolve to a SQLAlchemy MetaData instance. Got: {type(metadata_obj)}")
           return None
        return metadata_obj
    except Exception as e:
        print(f"Error importing TAUSESTACK_ALEMBIC_METADATA_TARGET ('{metadata_target_str}'): {e}")
        return None

target_metadata = get_user_metadata()

def get_db_url() -> str:
    """
    Returns the database URL from the TAUSESTACK_DATABASE_URL environment variable.
    Raises ValueError if the variable is not set.
    """
    db_url = os.getenv("TAUSESTACK_DATABASE_URL")
    if not db_url:
        raise ValueError(
            "Error: TAUSESTACK_DATABASE_URL environment variable not set.\n"
            "Please set it to your SQLAlchemy database connection string."
        )
    return db_url

# Set the database URL on the Alembic config object for other parts of Alembic to use.
# This ensures that both offline and online mode can access it consistently.
try:
    db_url_for_alembic = get_db_url()
    config.set_main_option("sqlalchemy.url", db_url_for_alembic)
except ValueError as e:
    # Print error and exit if DB URL is not set, as Alembic cannot proceed.
    print(e)
    sys.exit(1)
# --- End TauseStack SDK Customizations ---

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # URL is now set on config object from TAUSESTACK_DATABASE_URL
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """Run migrations in 'online' mode.

    In this scenario we need to create an Engine
    and associate a connection with the context.

    """
    # Get the database URL from the Alembic config (set from TAUSESTACK_DATABASE_URL)
    db_url = config.get_main_option("sqlalchemy.url")
    if not db_url:
        print("Error: sqlalchemy.url not set in Alembic configuration.")
        sys.exit(1)

    connectable = create_async_engine(db_url, poolclass=pool.NullPool)

    def do_run_migrations(connection):
        # Re-configure context with the dialect of the current connection if needed for autogen
        # context.configure(connection=connection, target_metadata=target_metadata, dialect_name=connection.dialect.name)
        # For general migrations, just the connection and target_metadata are usually sufficient.
        context.configure(connection=connection, target_metadata=target_metadata)

        with context.begin_transaction():
            context.run_migrations()

    async def async_main():
        async with connectable.connect() as connection:
            await connection.run_sync(do_run_migrations)
        await connectable.dispose()

    # Try to apply nest_asyncio to allow asyncio.run() from a running loop (e.g., pytest-asyncio)
    try:
        import nest_asyncio
        nest_asyncio.apply()
    except ImportError:
        # nest_asyncio not available. If run from an already running loop without it,
        # asyncio.run() might raise a RuntimeError.
        # Consider adding nest_asyncio to your dev dependencies if you encounter this.
        print(
            "Hint: nest_asyncio not found. If running migrations from an environment "
            "with an active asyncio loop (e.g., pytest-asyncio, Jupyter), "
            "consider installing nest_asyncio."
        )
        pass
    
    asyncio.run(async_main())

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
