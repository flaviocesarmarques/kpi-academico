"""Ponto de entrada da aplicação (factory `create_app`).

Health checks separados — fundamentais para Kubernetes e deploys sem downtime:
  • /health/live  → "o processo está vivo?" (livenessProbe: se falhar, reinicia)
  • /health/ready → "posso receber tráfego?" (readinessProbe: checa o banco;
                     se falhar, o pod sai do balanceamento mas NÃO é reiniciado)

Execução local:  uv run uvicorn kpi_academico.main:app --reload
Documentação interativa (OpenAPI): http://localhost:8000/docs
"""

import logging

from fastapi import FastAPI, Response, status
from sqlalchemy import text

from kpi_academico import __version__
from kpi_academico.api import router
from kpi_academico.config import get_settings
from kpi_academico.db import get_engine
from kpi_academico.observability import configurar_logs, configurar_metricas, configurar_traces

log = logging.getLogger(__name__)


def create_app() -> FastAPI:
    cfg = get_settings()
    configurar_logs(cfg.log_level)

    app = FastAPI(
        title="KPI Acadêmico",
        version=__version__,
        description="Indicadores acadêmicos por curso e período, com semáforo de metas.",
    )
    app.include_router(router)

    @app.get("/health/live", tags=["saúde"])
    def vivo() -> dict[str, str]:
        return {"status": "ok", "versao": __version__}

    @app.get("/health/ready", tags=["saúde"])
    def pronto(resposta: Response) -> dict[str, str]:
        try:
            with get_engine().connect() as conexao:
                conexao.execute(text("SELECT 1"))
        except Exception:
            log.exception("Banco indisponível")
            resposta.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
            return {"status": "indisponivel"}
        return {"status": "ok"}

    configurar_metricas(app)
    configurar_traces(app)
    log.info("KPI Acadêmico %s iniciado (ambiente=%s)", __version__, cfg.ambiente.value)
    return app


app = create_app()
