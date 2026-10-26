import os
from pathlib import Path
from alembic import context
from dotenv import load_dotenv
from core.database import Base, build_engine
import core.models

load_dotenv(Path(__file__).resolve().parents[1] / '.env')
url = os.getenv('MIGRATION_DATABASE_URL') or os.getenv('DATABASE_URL')
if not url:
    raise RuntimeError('MIGRATION_DATABASE_URL or DATABASE_URL required')
if context.is_offline_mode():
    context.configure(url=url, target_metadata=Base.metadata, literal_binds=True,
                      include_schemas=True, version_table_schema='familycare')
    with context.begin_transaction():
        context.run_migrations()
else:
    engine = build_engine(url, {'DB_POOL_SIZE': 1, 'DB_MAX_OVERFLOW': 0})
    with engine.connect() as connection:
        # Required before Alembic creates its version table in this private schema.
        connection.exec_driver_sql('CREATE SCHEMA IF NOT EXISTS familycare')
        connection.commit()
        context.configure(connection=connection, target_metadata=Base.metadata,
                          include_schemas=True, version_table_schema='familycare')
        with context.begin_transaction():
            context.run_migrations()
