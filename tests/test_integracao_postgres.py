"""Teste de INTEGRAÇÃO com PostgreSQL real (Testcontainers).

Por quê: SQLite e PostgreSQL diferem (tipos, constraints, transações).
Testar contra o banco de produção evita o "na minha máquina funciona".

Requer Docker. Localmente é pulado se o Docker não estiver disponível;
no CI (GitHub Actions, que tem Docker) roda sempre:
    uv run pytest -m integration
"""

from pathlib import Path

import pytest
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, func, select
from sqlalchemy.orm import Session

from kpi_academico.models import Medicao

# Passo 4 - from kpi_academico.seed import carregar
from kpi_academico.seed import CURSOS, INDICADORES, PERIODOS, carregar

pytestmark = pytest.mark.integration
postgres = pytest.importorskip("testcontainers.postgres")


def _docker_disponivel() -> bool:
    try:
        import docker

        docker.from_env().ping()
    except Exception:
        return False
    return True


@pytest.mark.skipif(not _docker_disponivel(), reason="Docker indisponível")
def test_migracoes_e_seed_no_postgres() -> None:
    # Mesma major version do PostgreSQL usada em produção (deploy/base/postgres.yaml).
    with postgres.PostgresContainer("postgres:17-alpine", driver="psycopg") as pg:
        url = pg.get_connection_url()
        cfg = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
        cfg.set_main_option("sqlalchemy.url", url)
        command.upgrade(cfg, "head")

        with Session(create_engine(url)) as sessao:
            assert carregar(sessao) > 0
            # Troca passo 4 - assert sessao.scalar(select(func.count(Medicao.id))) == 96
            assert sessao.scalar(select(func.count(Medicao.id))) == (
                len(INDICADORES) * len(CURSOS) * len(PERIODOS)
            )
