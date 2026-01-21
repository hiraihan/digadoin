import sys
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config
from sqlalchemy import pool

from alembic import context

# ----------------------------------------------------------------------
# [BAGIAN PENTING 1]: Setup Path
# Menambahkan folder root project ke sys.path agar folder 'app' terbaca
# ----------------------------------------------------------------------
sys.path.append(os.path.join(sys.path[0], '..'))

# ----------------------------------------------------------------------
# [BAGIAN PENTING 2]: Import Config & Models
# Kita import settings untuk ambil URL database dari .env Docker
# Kita import Base untuk metadata, dan models modul Anda agar terdeteksi
# ----------------------------------------------------------------------
from app.core.config import settings
from app.core.database import Base

# Import Model Dev 3 (Service Delivery)
# Jika nanti Dev 1 & Dev 2 sudah selesai, model mereka juga di-import disini
from app.modules.service_delivery.models import * # Setup Config Object Alembic
config = context.config

# Setup Logging (membaca dari alembic.ini)
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ----------------------------------------------------------------------
# [BAGIAN PENTING 3]: Target Metadata
# Menghubungkan Alembic dengan definisi tabel SQLAlchemy kita
# ----------------------------------------------------------------------
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode.

    This configures the context with just a URL
    and not an Engine, though an Engine is acceptable
    here as well.  By skipping the Engine creation
    we don't even need a DBAPI to be available.

    Calls to context.execute() here emit the given string to the
    script output.

    """
    # Mengambil URL database langsung dari config.py (app/core/config.py)
    url = settings.SQLALCHEMY_DATABASE_URI
    
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
    # ------------------------------------------------------------------
    # [BAGIAN PENTING 4]: Inject Database URL
    # Kita memaksa Alembic menggunakan URL dari settings.py (Docker env)
    # dan mengabaikan URL 'dummy' yang ada di alembic.ini
    # ------------------------------------------------------------------
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = settings.SQLALCHEMY_DATABASE_URI

    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()