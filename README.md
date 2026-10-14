# KPI Acadêmico

[![CI](https://github.com/flaviocesarmarques/kpi-academico/actions/workflows/ci.yml/badge.svg)](https://github.com/flaviocesarmarques/kpi-academico/actions/workflows/ci.yml)
[![Segurança](https://github.com/flaviocesarmarques/kpi-academico/actions/workflows/security.yml/badge.svg)](https://github.com/flaviocesarmarques/kpi-academico/actions/workflows/security.yml)
[![OpenSSF Scorecard](https://api.scorecard.dev/projects/github.com/flaviocesarmarques/kpi-academico/badge)](https://scorecard.dev/viewer/?uri=github.com/flaviocesarmarques/kpi-academico)

API de **indicadores acadêmicos (KPIs)** para cursos de graduação de uma IES
privada, construída como **repositório-escola de DevOps**: cada arquivo aplica e
explica, em comentários, uma boa prática do ciclo completo. O ciclo vai do commit
à produção, passando por segurança, observabilidade e engenharia do caos.
Todas as ferramentas usadas são livres ou gratuitas.

## O sistema

- Indicadores organizados em **4 dimensões**: Formação e Currículo; Trajetória
  do Estudante; Corpo Docente e Inovação; Qualidade, Avaliação e Gestão.
- Cada indicador tem **meta**, **polaridade** (maior/menor é melhor) e vínculo
  com o eixo do instrumento de avaliação do Inep.
- **Painel por curso e período** com semáforo (verde/amarelo/vermelho) de
  atingimento da meta e, atrás de uma *feature flag*, a variação em relação ao
  período anterior.

| Rota | Descrição |
|---|---|
| `GET /api/v1/dimensoes` | Lista as dimensões |
| `GET /api/v1/indicadores?dimensao=` | Lista indicadores |
| `POST /api/v1/indicadores` 🔑 | Cria indicador |
| `POST /api/v1/medicoes` 🔑 | Registra o valor de um indicador para curso/período |
| `GET /api/v1/cursos/{curso}/painel?periodo=2026.1` | Painel com semáforo |
| `GET /health/live`, `/health/ready`, `/metrics` | Saúde e métricas |

🔑 = exige o cabeçalho `X-API-Key`. Documentação interativa em `/docs`.

## Início rápido (5 minutos)

Antes de tudo, verifique o que falta instalar
([guia completo de pré-requisitos](docs/pre-requisitos.md)):

```bash
bash scripts/verificar-ambiente.sh   # Linux, macOS ou WSL  (Windows: scripts\verificar-ambiente.ps1)
```

```bash
# Pré-requisitos: git, make, uv (instala o Python sozinho) e Docker
scripts/configurar-repo.sh <seu-usuario-github>   # personaliza o repositório (uma vez)
make setup        # dependências + hooks do pre-commit
make teste        # testes com cobertura
make seed rodar   # API local em http://localhost:8000/docs (SQLite)

# Ou o ambiente completo em containers (PostgreSQL + migração + API):
make compose compose-seed
```

## A trilha DevOps neste repositório

| Etapa | O que praticar | Onde está |
|---|---|---|
| 0. Preparar o ambiente | Diagnóstico de pré-requisitos, instalação idempotente com Ansible | `scripts/verificar-ambiente.*`, `docs/pre-requisitos.md` |
| 1. Planejar e codificar | Issues/PR templates, CODEOWNERS, trunk-based, Conventional Commits, pre-commit | `.github/`, `.pre-commit-config.yaml`, `CONTRIBUTING.md` |
| 2. Integração contínua | Lint, tipos, testes (unitários, API, migrações, PostgreSQL real), cobertura mínima, matriz | `.github/workflows/ci.yml`, `tests/` |
| 3. Qualidade e DevSecOps | SonarQube, CodeQL, Gitleaks, pip-audit, Dependabot, Trivy, Hadolint, Checkov, Scorecard | `security.yml`, `scorecard.yml`, `dependabot.yml` |
| 4. Empacotamento | Dockerfile multi-stage não-root, lockfile, imagem multi-arquitetura no GHCR | `Dockerfile`, `docker-compose.yml` |
| 5. Release e supply chain | SemVer automático, CHANGELOG, SBOM, Cosign keyless, proveniência SLSA | `release.yml`, `release-please-config.json` |
| 6. Infra como código | Ansible (estação), k3d (cluster), OpenTofu (plataforma) | `infra/` |
| 7. Entrega contínua (GitOps) | Kustomize, Argo CD, SOPS, Kyverno, promoção com aprovação | `deploy/`, `policies/`, `promover-producao.yml` |
| 8. Entrega progressiva e testes | Canary com rollback automático, feature flags, DAST (ZAP), carga (k6) | `deploy/base/rollout.yaml`, `dast-performance.yml` |
| 9. Observabilidade | Logs JSON, métricas RED, traces OpenTelemetry, SLOs, alertas, dashboard | `observability.py`, `deploy/base/alertas.yaml` |
| 10. Resiliência e melhoria | Chaos Mesh, postmortem sem culpa, métricas DORA, catálogo Backstage | `chaos/`, `docs/`, `catalog-info.yaml` |

O passo a passo completo, com exercícios, está em
**[docs/TRILHA-DEVOPS.md](docs/TRILHA-DEVOPS.md)**. A configuração única do
GitHub (segredos, ambientes, ruleset) está em
**[docs/configuracao-github.md](docs/configuracao-github.md)**.

## Estrutura

```
├── src/kpi_academico/     aplicação FastAPI (regras de negócio em kpis.py)
├── tests/                 unitários, API, migrações, integração, carga (k6), DAST (ZAP)
├── migrations/            migrações Alembic (schema como código)
├── .github/               workflows, ação composta, templates, ruleset, Dependabot
├── infra/                 ansible/ (estação) · k3d/ (cluster) · tofu/ (plataforma)
├── deploy/                base/ + overlays/{dev,prod} (Kustomize) · argocd/ · secrets/
├── policies/              Kyverno (políticas como código + testes)
├── chaos/                 experimentos do Chaos Mesh
└── docs/                  trilha, configuração do GitHub, runbooks, flags, DORA
```

## Licença

MIT. Veja [LICENSE](LICENSE).
