# =============================================================================
# Makefile — atalhos para os comandos do dia a dia (documentação executável).
# `make` ou `make ajuda` lista os alvos. Os mesmos comandos rodam no CI.
# =============================================================================
.DEFAULT_GOAL := ajuda
SHELL := /bin/bash
CLUSTER := kpi
.PHONY: ajuda verificar verificar-tudo setup teste teste-integracao lint tipos rodar migrar seed compose compose-seed \
        cluster cluster-destruir plataforma segredos-chave segredos-aplicar carga caos

ajuda: ## Lista os alvos disponíveis
	@grep -E '^[a-zA-Z_-]+:.*?## ' $(MAKEFILE_LIST) | awk 'BEGIN{FS=":.*?## "}{printf "  \033[36m%-20s\033[0m %s\n",$$1,$$2}'

# ---------- Pré-requisitos (etapa 0) ----------------------------------------
verificar: ## Diagnóstico do ambiente: o que falta instalar (etapas 1–5)
	@bash scripts/verificar-ambiente.sh

verificar-tudo: ## Diagnóstico completo, incluindo Kubernetes local (etapas 6–10)
	@bash scripts/verificar-ambiente.sh --tudo

# ---------- Desenvolvimento (etapas 1–3) ------------------------------------
setup: ## Instala dependências (uv.lock) e hooks do pre-commit
	@command -v uv >/dev/null || { echo "uv não encontrado. Rode 'make verificar' para ver como instalar."; exit 1; }
	uv sync --extra dev
	uv run pre-commit install --install-hooks

teste: ## Testes com cobertura (pula integração se não houver Docker)
	uv run pytest

teste-integracao: ## Só os testes com PostgreSQL real (Testcontainers)
	uv run pytest -m integration --no-cov

lint: ## Todos os hooks do pre-commit em todos os arquivos
	uv run pre-commit run --all-files

tipos: ## Checagem de tipos com mypy
	uv run mypy

rodar: migrar ## API local com recarga automática em http://localhost:8000/docs
	uv run uvicorn kpi_academico.main:app --reload

migrar: ## Aplica as migrações no banco configurado em KPI_DATABASE_URL
	uv run alembic upgrade head

seed: migrar ## Popula dados de exemplo
	uv run kpi-seed

# ---------- Containers (etapa 4) --------------------------------------------
compose: ## Sobe PostgreSQL + migração + API com docker compose
	docker compose up --build -d api

compose-seed: ## Popula dados de exemplo no ambiente do compose
	docker compose run --rm seed

carga: ## Teste de carga k6 contra a API local
	docker run --rm --network host -v "$$PWD/tests/carga:/s:ro" \
	  -e BASE_URL=http://localhost:8000 grafana/k6:2.3.0 run /s/painel.js

# ---------- Plataforma local (etapas 6–10) ----------------------------------
cluster: ## Cria o cluster Kubernetes local (k3d)
	k3d cluster create --config infra/k3d/cluster.yaml

cluster-destruir: ## Remove o cluster local
	k3d cluster delete $(CLUSTER)

plataforma: ## Instala Argo CD, Kyverno, observabilidade etc. com OpenTofu
	cd infra/tofu && tofu init && tofu apply

segredos-chave: ## Gera a chave age para o SOPS (guarde-a fora do Git!)
	@test -f age.key || age-keygen -o age.key
	@echo "Chave pública (cole em .sops.yaml):"; grep -o 'age1.*' age.key

segredos-aplicar: ## Descriptografa (SOPS) e aplica os Secrets no cluster
	for f in deploy/secrets/*.enc.yaml; do SOPS_AGE_KEY_FILE=age.key sops -d "$$f" | kubectl apply -f -; done

caos: ## Executa o experimento de caos (derruba um pod da API)
	kubectl apply -f chaos/pod-kill.yaml
