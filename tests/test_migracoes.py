"""Garante que as migrações Alembic e os modelos estão SINCRONIZADOS.

Erro clássico em produção: alguém altera models.py e esquece a migração.
Este teste aplica as migrações num banco vazio, compara com os modelos e
falha se houver diferença. Também testa o downgrade (rollback de schema).
"""

from pathlib import Path

from alembic import command
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from sqlalchemy import create_engine, inspect

from kpi_academico.db import Base

RAIZ = Path(__file__).resolve().parents[1]


def _config(url: str) -> Config:
    cfg = Config(str(RAIZ / "alembic.ini"))
    cfg.set_main_option("sqlalchemy.url", url)
    return cfg


def test_migracoes_sincronizadas_com_modelos(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    command.upgrade(_config(url), "head")
    with create_engine(url).connect() as conexao:
        diferencas = compare_metadata(MigrationContext.configure(conexao), Base.metadata)
    assert diferencas == [], f"Modelos sem migração correspondente: {diferencas}"


def test_downgrade_completo(tmp_path: Path) -> None:
    url = f"sqlite:///{tmp_path / 'mig.db'}"
    cfg = _config(url)
    command.upgrade(cfg, "head")
    command.downgrade(cfg, "base")
    assert set(inspect(create_engine(url)).get_table_names()) <= {"alembic_version"}
