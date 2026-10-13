# syntax=docker/dockerfile:1
# =============================================================================
# Dockerfile multi-stage — imagem pequena, reproduzível e segura (etapa 4)
# -----------------------------------------------------------------------------
# Boas práticas aplicadas:
#   1. MULTI-STAGE: ferramentas de build ficam no estágio "builder"; a imagem
#      final só tem o runtime → menor tamanho e menor superfície de ataque.
#   2. VERSÕES FIXAS das imagens base. Em produção, fixe também o DIGEST
#      (python:3.13-slim@sha256:...) — o Dependabot atualiza para você.
#   3. Dependências instaladas do uv.lock com --locked: a imagem contém
#      EXATAMENTE as versões testadas no CI.
#   4. Cache de camadas: dependências antes do código (mudar código não
#      reinstala dependências).
#   5. USUÁRIO NÃO-ROOT com UID numérico (exigido pela política Kyverno).
#   6. Sem segredos na imagem: tudo vem de variáveis de ambiente em runtime.
#   7. Labels OCI: rastreabilidade imagem ↔ commit (preenchidos pelo CI).
#   8. HEALTHCHECK para docker-compose (no Kubernetes valem as probes).
#
# Build local:  docker build -t kpi-academico:dev .
# =============================================================================

ARG PYTHON_VERSION=3.13

# ---------- Estágio 1: build -------------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS builder

# uv copiado de imagem oficial com versão fixa (não "latest").
COPY --from=ghcr.io/astral-sh/uv:0.13.0 /uv /usr/local/bin/uv

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=never \
    UV_PROJECT_ENVIRONMENT=/app/.venv

WORKDIR /app

# Somente os manifestos de dependências primeiro → camada cacheada.
COPY pyproject.toml uv.lock ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-install-project

# Agora o código da aplicação.
COPY README.md LICENSE alembic.ini ./
COPY src/ src/
COPY migrations/ migrations/
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-dev --no-editable

# ---------- Estágio 2: runtime ----------------------------------------------
FROM python:${PYTHON_VERSION}-slim AS runtime

ARG VERSION=dev
ARG REVISION=unknown
LABEL org.opencontainers.image.title="kpi-academico" \
      org.opencontainers.image.description="API de indicadores acadêmicos" \
      org.opencontainers.image.licenses="MIT" \
      org.opencontainers.image.version="${VERSION}" \
      org.opencontainers.image.revision="${REVISION}"

# Usuário sem privilégios, UID/GID fixos (10001) — nunca rode como root.
RUN groupadd --gid 10001 app && \
    useradd --uid 10001 --gid app --no-create-home --shell /usr/sbin/nologin app

WORKDIR /app
COPY --from=builder --chown=app:app /app/.venv /app/.venv
COPY --from=builder --chown=app:app /app/alembic.ini /app/alembic.ini
COPY --from=builder --chown=app:app /app/migrations /app/migrations

ENV PATH="/app/.venv/bin:${PATH}" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

USER 10001
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=3s --start-period=10s --retries=3 \
  CMD ["python", "-c", "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2).status == 200 else 1)"]

# Forma "exec" (JSON): o processo recebe SIGTERM direto → desligamento gracioso.
# Para migrações, o Kubernetes/compose sobrescreve o comando com:
#   alembic upgrade head
CMD ["uvicorn", "kpi_academico.main:app", "--host", "0.0.0.0", "--port", "8000", "--proxy-headers"]
