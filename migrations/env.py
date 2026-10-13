"""Ambiente de execução do Alembic.

Lê a URL do banco da MESMA configuração da aplicação (KPI_DATABASE_URL),
garantindo que app e migrações nunca apontem para bancos diferentes.
"""

from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from kpi_academico import models  # noqa: F401 - registra as tabelas no metadata
from kpi_academico.config import get_settings
from kpi_academico.db import Base

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Permite que os testes passem a URL explicitamente (config.set_main_option).
if not config.get_main_option("sqlalchemy.url"):
    config.set_main_option("sqlalchemy.url", get_settings().database_url)

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Gera SQL sem conectar (útil para revisão pelo DBA: alembic upgrade head --sql)."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        render_as_batch=True,
    )
    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    conectavel = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with conectavel.connect() as conexao:
        # render_as_batch: necessário para ALTER TABLE no SQLite (usado em dev/testes).
        context.configure(connection=conexao, target_metadata=target_metadata, render_as_batch=True)
        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
