from logging.config import fileConfig

from sqlalchemy import create_engine, pool

from alembic import context
from api.config import Settings

config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# target_metadata = None оскільки ми не використовуємо SQLAlchemy ORM моделі
# міграції пишемо вручну через op.create_table() etc.
target_metadata = None

settings = Settings()


def run_migrations_offline() -> None:
    """Run migrations without a live DB connection (generates SQL script)."""
    context.configure(
        url=settings.database_url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations against a live DB connection."""
    connectable = create_engine(
        settings.database_url,
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
        )
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
