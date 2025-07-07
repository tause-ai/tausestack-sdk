import os
import shutil
import pytest
import asyncio
from pathlib import Path
from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine
from alembic.config import CommandLine

# Define paths relative to this test file or project root
PROJECT_ROOT = Path(__file__).parent.parent.parent.parent
MIGRATIONS_DIR = PROJECT_ROOT / "tausestack" / "sdk" / "database" / "migrations_alembic"
VERSIONS_DIR = MIGRATIONS_DIR / "versions"
SAMPLE_MODELS_METADATA_TARGET = "tests.sdk.database.sample_app_for_alembic.models:metadata_obj"

@pytest.fixture(scope="function")
async def test_db_env():
    """Fixture to set up a temporary SQLite DB and Alembic environment for tests."""
    # Ensure versions directory exists, create if not (Alembic needs it)
    VERSIONS_DIR.mkdir(parents=True, exist_ok=True)

    # Use a unique name for the test database to avoid conflicts if tests run in parallel (though pytest usually serializes)
    db_file = PROJECT_ROOT / f"test_alembic_db_{os.urandom(4).hex()}.sqlite"
    db_url = f"sqlite+aiosqlite:///{db_file.resolve()}"

    # Set environment variables for Alembic's env.py
    os.environ["TAUSESTACK_DATABASE_URL"] = db_url
    os.environ["TAUSESTACK_ALEMBIC_METADATA_TARGET"] = SAMPLE_MODELS_METADATA_TARGET

    # Initial cleanup of any previous test migration files to avoid conflicts
    # This is a simple approach; more sophisticated management might be needed for complex scenarios
    for f in VERSIONS_DIR.glob("*.py"):
        if f.name != "__init__.py":
            f.unlink()
    if (VERSIONS_DIR / "__pycache__").exists():
        shutil.rmtree(VERSIONS_DIR / "__pycache__")

    yield db_url, db_file # Provide the db_url and db_file to the test

    # Teardown: Clean up environment variables, migration files, and database file
    del os.environ["TAUSESTACK_DATABASE_URL"]
    del os.environ["TAUSESTACK_ALEMBIC_METADATA_TARGET"]

    for f in VERSIONS_DIR.glob("*.py"):
        if f.name != "__init__.py":
            f.unlink(missing_ok=True)
    if (VERSIONS_DIR / "__pycache__").exists():
        shutil.rmtree(VERSIONS_DIR / "__pycache__")
    
    if db_file.exists():
        db_file.unlink()

def run_alembic_command(command: list[str]):
    """Helper to run Alembic commands programmatically."""
    # Alembic commands should be run from the migrations directory
    # Store original CWD and change to migrations_dir, then restore
    original_cwd = Path.cwd()
    os.chdir(MIGRATIONS_DIR)
    try:
        cmd = CommandLine()
        cmd.main(argv=command)
    finally:
        os.chdir(original_cwd)

async def table_exists(db_url: str, table_name: str) -> bool:
    """Check if a table exists in the database."""
    engine = create_async_engine(db_url)
    async with engine.connect() as connection:
        # For SQLite, query sqlite_master
        # For PostgreSQL, query information_schema.tables
        # This example is for SQLite, adjust if your default test DB changes
        if "sqlite" in db_url:
            result = await connection.execute(
                text(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            )
        elif "postgresql" in db_url: # Basic check for PostgreSQL
             result = await connection.execute(
                text(f"SELECT EXISTS (SELECT FROM information_schema.tables WHERE table_name = '{table_name}')")
            )
             return result.scalar_one() if result else False # type: ignore
        else:
            # Fallback or raise error for unsupported DBs in test
            # This simple check might not be robust for all DBs
            # For a generic SQLAlchemy approach, one might try reflecting the table
            # from sqlalchemy.inspection import inspect
            # inspector = inspect(connection)
            # return await connection.run_sync(inspector.has_table, table_name)
            # However, inspect(connection) needs a sync connection for some operations.
            # The raw query is often simpler for tests if the DB type is known.
            raise NotImplementedError(f"Table existence check not implemented for DB URL: {db_url}")
        
        return result.scalar_one_or_none() is not None
    await engine.dispose()

@pytest.mark.asyncio
async def test_alembic_full_migration_cycle(test_db_env):
    db_url, _ = test_db_env

    # 1. Generate a new revision
    # Ensure no prior migrations exist that could cause 'Target database is not up to date.'
    # The fixture should handle cleaning versions dir.
    run_alembic_command(["revision", "-m", "test_create_sample_table", "--autogenerate"])
    
    # Check that a migration file was created
    migration_files = list(VERSIONS_DIR.glob("*_test_create_sample_table.py"))
    assert len(migration_files) == 1, "Migration file not generated or multiple generated"
    migration_file = migration_files[0]

    # 2. Apply the migration
    run_alembic_command(["upgrade", "head"])
    assert await table_exists(db_url, "sample_table"), "Table 'sample_table' not created after upgrade"

    # 3. Check current revision (optional, good for sanity)
    # output = subprocess.run(["alembic", "current"], cwd=MIGRATIONS_DIR, capture_output=True, text=True)
    # assert migration_file.stem.split('_')[0] in output.stdout, "Current revision not updated correctly"

    # 4. Downgrade the migration
    run_alembic_command(["downgrade", "-1"])
    assert not await table_exists(db_url, "sample_table"), "Table 'sample_table' still exists after downgrade"

    # 5. Upgrade again to ensure it works (optional)
    run_alembic_command(["upgrade", "head"])
    assert await table_exists(db_url, "sample_table"), "Table 'sample_table' not re-created after second upgrade"

    # Fixture will handle cleanup of the migration file and DB
