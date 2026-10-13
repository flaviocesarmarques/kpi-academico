"""Observabilidade: logs estruturados, métricas e traces (etapa 9 da trilha).

Os "três pilares":
  • LOGS em JSON no stdout → coletados pelo Grafana Alloy e enviados ao Loki.
    (12-Factor, fator XI: a aplicação não gerencia arquivos de log.)
  • MÉTRICAS Prometheus em /metrics → coletadas via ServiceMonitor; base para
    alertas (SLOs) e para a análise automática do canary (Argo Rollouts).
    Seguem o método RED: Rate (taxa), Errors (erros), Duration (latência).
  • TRACES OpenTelemetry → enviados por OTLP ao Tempo. Só são ativados se a
    variável padrão OTEL_EXPORTER_OTLP_ENDPOINT existir, então o
    desenvolvimento local não depende de nenhum coletor.

Nota de manutenção: as métricas HTTP são coletadas por um middleware próprio
(poucas linhas) em vez de uma biblioteca de terceiros. Menos dependências =
menor superfície de ataque e menos quebras quando o framework atualiza.
"""

import json
import logging
import os
import sys
import time
from collections.abc import Awaitable, Callable
from datetime import UTC, datetime

from fastapi import FastAPI, Request, Response
from opentelemetry import trace
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest

from kpi_academico import __version__

# Métricas HTTP (RED). Rótulo "rota" usa o MOLDE da rota (/cursos/{curso}/painel),
# nunca a URL real — evita explosão de cardinalidade no Prometheus.
REQUISICOES = Counter("http_requests_total", "Requisições HTTP", ["metodo", "rota", "status"])
LATENCIA = Histogram(
    "http_request_duration_seconds",
    "Latência das requisições HTTP",
    ["metodo", "rota"],
    buckets=(0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5),
)
# Métricas de NEGÓCIO. Rótulos de baixa cardinalidade: curso sim, id de aluno nunca.
MEDICOES_REGISTRADAS = Counter(
    "kpi_medicoes_registradas_total", "Medições de KPI registradas", ["curso"]
)
INFO_BUILD = Gauge("kpi_build_info", "Versão em execução", ["versao"])

_IGNORADAS = ("/metrics", "/health/")


class FormatadorJson(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        dados = {
            "ts": datetime.fromtimestamp(record.created, UTC).isoformat(),
            "nivel": record.levelname,
            "logger": record.name,
            "msg": record.getMessage(),
        }
        # Correlação log ↔ trace: o Grafana abre o trace no Tempo a partir do log.
        contexto = trace.get_current_span().get_span_context()
        if contexto.is_valid:
            dados["trace_id"] = format(contexto.trace_id, "032x")
        if record.exc_info:
            dados["exc"] = self.formatException(record.exc_info)
        return json.dumps(dados, ensure_ascii=False)


def configurar_logs(nivel: str) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(FormatadorJson())
    logging.basicConfig(level=nivel.upper(), handlers=[handler], force=True)


def configurar_metricas(app: FastAPI) -> None:
    INFO_BUILD.labels(versao=__version__).set(1)

    @app.middleware("http")
    async def medir(
        request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        if request.url.path.startswith(_IGNORADAS):
            return await call_next(request)
        inicio = time.perf_counter()
        status = 500
        try:
            resposta = await call_next(request)
            status = resposta.status_code
            return resposta
        finally:
            rota = getattr(request.scope.get("route"), "path", "nao_mapeada")
            REQUISICOES.labels(request.method, rota, str(status)).inc()
            LATENCIA.labels(request.method, rota).observe(time.perf_counter() - inicio)

    @app.get("/metrics", include_in_schema=False)
    def metricas() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


def configurar_traces(app: FastAPI) -> None:  # pragma: no cover - depende de coletor externo
    if not os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):
        return
    from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
    from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
    from opentelemetry.sdk.resources import Resource
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import BatchSpanProcessor

    provedor = TracerProvider(
        resource=Resource.create({"service.name": "kpi-academico", "service.version": __version__})
    )
    provedor.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provedor)
    FastAPIInstrumentor.instrument_app(app, excluded_urls="health,metrics")
