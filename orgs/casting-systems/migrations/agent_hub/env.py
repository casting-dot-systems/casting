from __future__ import annotations

import os
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

config = getattr(context, "config", None)

if config and config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = None


def get_url() -> str:
    return os.environ.get("CAST_DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/casting_dev")


def run_migrations_offline() -> None:
    url = get_url()
    context.configure(url=url, target_metadata=target_metadata, literal_binds=True)
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    if not config:
        raise RuntimeError("Alembic context configuration is unavailable")

    configuration = config.get_section(config.config_ini_section, {})
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(configuration, prefix="sqlalchemy.", poolclass=pool.NullPool)
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


def run() -> None:
    if not config:
        return

    if context.is_offline_mode():
        run_migrations_offline()
    else:
        run_migrations_online()


run()
