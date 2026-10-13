"""Fixtures compartilhadas dos testes.

Boas práticas:
  • Testes ISOLADOS: cada teste recebe um banco limpo (sem depender da ordem).
  • Configuração por variável de ambiente, igual à produção (nada de "if testing").
  • Banco SQLite temporário para testes rápidos; o comportamento em PostgreSQL
    real é coberto por tests/test_integracao_postgres.py (Testcontainers).
"""

import os
import tempfile
from pathlib import Path

# Deve vir ANTES de importar a aplicação, pois as configurações são cacheadas.
_DB = Path(tempfile.mkdtemp()) / "teste.db"
os.environ["KPI_DATABASE_URL"] = f"sqlite:///{_DB}"
os.environ["KPI_API_KEY"] = "chave-de-teste"
os.environ.pop("OTEL_EXPORTER_OTLP_ENDPOINT", None)
os.environ.pop("KPI_UNLEASH_URL", None)

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from kpi_academico import models  # noqa: E402, F401
from kpi_academico.db import Base, get_engine  # noqa: E402
from kpi_academico.main import app  # noqa: E402

CABECALHO = {"X-API-Key": "chave-de-teste"}


@pytest.fixture(autouse=True)
def banco_limpo() -> None:
    engine = get_engine()
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)


@pytest.fixture
def cliente() -> TestClient:
    return TestClient(app)


@pytest.fixture
def indicador_evasao(cliente: TestClient) -> dict[str, object]:
    dados = {
        "codigo": "EST-01",
        "nome": "Taxa de evasão",
        "dimensao": "trajetoria_estudante",
        "unidade": "%",
        "meta": 12,
        "polaridade": "menor_melhor",
    }
    resposta = cliente.post("/api/v1/indicadores", json=dados, headers=CABECALHO)
    assert resposta.status_code == 201
    return dict(resposta.json())
