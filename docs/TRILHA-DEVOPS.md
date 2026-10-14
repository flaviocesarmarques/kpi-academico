# Trilha DevOps — passo a passo

Cada etapa traz o **objetivo**, o **roteiro** de comandos, o **ponto de verificação**
(como saber que deu certo) e um **exercício** que provoca uma falha de propósito.
É vendo o pipeline barrar o erro que a boa prática fica clara.

As etapas são cumulativas. As etapas 1 a 5 precisam só de GitHub e Docker; as
etapas 6 a 10 sobem um cluster Kubernetes local, que pede cerca de 8 GB de RAM livres.

---

## Etapa 0 — Preparação

1. **Verifique o ambiente antes de tudo.** O diagnóstico mostra o que falta e
   como instalar ([detalhes em pre-requisitos.md](pre-requisitos.md)):
   ```bash
   bash scripts/verificar-ambiente.sh        # Linux, macOS ou WSL
   ```
   No Windows, rode antes no PowerShell:
   `powershell -ExecutionPolicy Bypass -File scripts\verificar-ambiente.ps1`.
   Siga só quando o diagnóstico terminar com **"Tudo pronto!"**.
2. Crie um repositório **público** vazio chamado `kpi-academico` no GitHub.
3. Extraia este projeto, personalize e envie:
   ```bash
   scripts/configurar-repo.sh <seu-usuario>
   git init -b main && git add -A
   git commit -m "chore: estrutura inicial do repositório"
   git remote add origin https://github.com/<seu-usuario>/kpi-academico.git
   git push -u origin main
   ```
4. Faça a configuração única descrita em [configuracao-github.md](configuracao-github.md).
5. Antes da etapa 6, rode `make verificar-tudo`. O playbook Ansible instala de
   uma vez kubectl, k3d, helm, tofu, sops, age, argo rollouts, argocd, cosign e k6:
   ```bash
   make estacao        # em "BECOME password:", digite a senha do usuário do Ubuntu
   ```

---

## Etapa 1 — Planejar e codificar

**Objetivo:** fluxo de trabalho padronizado antes de qualquer automação.

- Crie uma issue usando o formulário "Novo indicador (KPI)".
- `make setup` instala os hooks do pre-commit, que passam a rodar a cada commit.
- Crie uma branch curta: `git switch -c feat/indicador-retencao`.

**Ponto de verificação:** tente `git commit -m "mudanças"`. O hook
*conventional-pre-commit* recusa, porque a mensagem não segue o padrão.
`git commit -m "feat(kpi): adiciona indicador de retenção"` é aceito.

**Exercício:** grave `AWS_SECRET_ACCESS_KEY=AKIA...` em um arquivo e tente commitar.
O Gitleaks bloqueia o commit antes que o segredo entre no histórico.

---

## Etapa 2 — Integração contínua

**Objetivo:** todo PR é verificado automaticamente; a `main` está sempre verde.

- Abra um PR. Os jobs de `ci.yml` rodam em paralelo: pre-commit, mypy,
  testes em Python 3.12 e 3.13 (com PostgreSQL real via Testcontainers),
  build e scan da imagem.
- Com o ruleset ativo, o botão de merge só libera com todos os checks verdes
  e a aprovação do CODEOWNER.

**Ponto de verificação:** a aba *Checks* do PR mostra todos os jobs verdes e
o artefato `relatorios-testes` contém a cobertura.

**Exercícios:**
1. Mude a fórmula de `atingimento` em `kpis.py` e veja os testes unitários falharem.
2. Adicione uma coluna em `models.py` **sem** criar migração. O teste
   `test_migracoes_sincronizadas_com_modelos` falha e explica o motivo.
3. Apague testes até a cobertura cair abaixo de 85% e veja o quality gate barrar o PR.

---

## Etapa 3 — Qualidade e DevSecOps

**Objetivo:** segurança em camadas, automatizada e no início do ciclo (*shift-left*).

- Ative o SonarQube Cloud (veja configuracao-github.md) e observe o Quality Gate no PR.
- Explore **Security → Code scanning**: CodeQL, Hadolint, Checkov, Trivy e
  Scorecard publicam alertas no mesmo lugar.
- O Dependabot abre PRs semanais de atualização. Revise e faça o merge.

**Exercícios:**
1. Em `api.py`, monte uma consulta SQL concatenando texto do usuário
   (`text(f"... {curso}")`). O CodeQL aponta *SQL injection*.
2. Fixe uma versão antiga e vulnerável de uma biblioteca no `pyproject.toml`
   (`uv add "jinja2==2.10"`). O `pip-audit` e o *dependency review* bloqueiam.
3. Remova `USER 10001` do Dockerfile. Checkov e Trivy acusam o container rodando como root.

---

## Etapa 4 — Empacotamento

**Objetivo:** um artefato imutável, pequeno e reproduzível.

```bash
docker build -t kpi-academico:dev .
docker image ls kpi-academico               # compare o tamanho com uma imagem single-stage
docker run --rm kpi-academico:dev id        # uid=10001, nunca root
make compose compose-seed                    # ambiente local completo
```

**Ponto de verificação:** `http://localhost:8000/api/v1/cursos/CC/painel?periodo=2026.1`
responde com o semáforo calculado.

**Exercício:** altere só um arquivo `.py` e reconstrua. A camada de dependências
vem do cache, porque a ordem das instruções no Dockerfile foi pensada para isso.

---

## Etapa 5 — Release e cadeia de suprimentos

**Objetivo:** versionamento automático e artefatos verificáveis.

1. Faça merge de um PR `feat: ...`. O release-please abre o PR **"chore(main): release 0.2.0"**
   com o CHANGELOG gerado.
2. Faça merge do PR de release. O workflow `release.yml` cria a tag, publica a
   imagem no GHCR, gera o SBOM, assina a imagem e atesta a proveniência.
3. Verifique a imagem como um auditor faria:
   ```bash
   cosign verify ghcr.io/<usuario>/kpi-academico:0.2.0 \
     --certificate-identity-regexp 'https://github.com/<usuario>/kpi-academico/.*' \
     --certificate-oidc-issuer https://token.actions.githubusercontent.com
   gh attestation verify oci://ghcr.io/<usuario>/kpi-academico:0.2.0 --owner <usuario>
   ```

**Ponto de verificação:** a GitHub Release tem o `sbom.spdx.json` anexado, e um
PR `chore(deploy): dev -> 0.2.0` foi aberto automaticamente.

**Exercício:** faça um commit `feat!: muda o formato do painel` (quebra de contrato).
O release-please propõe uma versão **major**.

---

## Etapa 6 — Infraestrutura como código

**Objetivo:** recriar o ambiente inteiro a partir do Git.

```bash
make verificar-tudo                            # confira kubectl, k3d, helm, tofu, sops...
make cluster                                   # k3d: 1 servidor + 2 agentes
cp infra/tofu/terraform.tfvars.exemplo infra/tofu/terraform.tfvars
cd infra/tofu && tofu init && tofu plan        # LEIA o plano antes de aplicar
tofu apply && tofu output enderecos
```

**Ponto de verificação:** `kubectl get pods -A` mostra Argo CD, Kyverno,
Prometheus, Grafana, Loki, Tempo e Chaos Mesh rodando.

**Exercício:** destrua tudo (`make cluster-destruir`) e recrie com os mesmos
comandos. Infra descartável e reproduzível deixa de ser tratada como um "animal de estimação".

---

## Etapa 7 — Entrega contínua com GitOps

**Objetivo:** o cluster reflete o Git, e nada além do Git.

```bash
make segredos-chave                    # cole a chave pública em .sops.yaml
scripts/criar-segredos.sh dev && scripts/criar-segredos.sh prod
git add deploy/secrets .sops.yaml && git commit -m "chore(deploy): segredos criptografados"
make segredos-aplicar
kubectl apply -f policies/kyverno/ -f policies/kyverno-cluster/
kubectl apply -f deploy/argocd/
```

Acesse `http://argocd.localhost:8080`. O comando da senha está em `tofu output`.
Faça merge do PR GitOps de dev e veja o Argo CD sincronizar na ordem: banco, migração, API.

**Pontos de verificação:**
- `http://kpi-dev.localhost:8080/docs` responde.
- `kubectl -n kpi-dev scale rollout kpi-api --replicas=5`: em até 1 minuto o
  Argo CD desfaz a mudança (*selfHeal*). O cluster não aceita mudança fora do Git.

**Exercícios:**
1. Tente `kubectl run teste --image=nginx:latest -n kpi-dev -l app.kubernetes.io/part-of=kpi-academico`.
   O Kyverno recusa.
2. Promova para produção: *Actions → Promover para produção → versão*. O workflow
   espera a aprovação no Environment `producao`, verifica a assinatura e abre o PR.

---

## Etapa 8 — Entrega progressiva e testes da aplicação em execução

**Objetivo:** reduzir o risco de cada deploy e testar como um atacante e como um pico de acesso.

- Acompanhe um canary: `kubectl argo rollouts get rollout kpi-api -n kpi-prod --watch`.
  Em produção ele **pausa** depois do primeiro passo e só segue com
  `kubectl argo rollouts promote kpi-api -n kpi-prod`.
- *Feature flag*: em dev, `KPI_FLAG_PAINEL_TENDENCIA=true` (overlay dev) mostra a
  variação no painel. Para controle em tempo real, suba o Unleash
  (`docker compose --profile flags up -d`), crie a flag `painel_tendencia` e
  defina `KPI_UNLEASH_URL`/`KPI_UNLEASH_TOKEN`.
- O workflow `dast-performance.yml` roda o OWASP ZAP e o k6 toda noite.

**Exercício:** publique uma versão que retorne erro 500 em 10% das requisições
(por exemplo, `if random() < 0.1: raise`). Gere tráfego com `make carga`. A análise
do canary detecta o aumento de erros e o **rollback é automático**. Escreva o
postmortem usando o template de issue.

---

## Etapa 9 — Observabilidade

**Objetivo:** saber que algo quebrou antes do usuário avisar.

- Grafana (`http://grafana.localhost:8080`), dashboard **KPI Acadêmico — API**:
  taxa de requisições, erro, latência p95 e medições por curso.
- *Explore → Loki*: `{namespace="kpi-dev", app="kpi-api"} | json | nivel="ERROR"`.
- *Explore → Tempo*: veja o caminho completo de uma requisição. A partir de
  um log com `trace_id`, abra o trace correspondente.
- Alertas em `deploy/base/alertas.yaml` usam os SLOs e apontam para runbooks em `docs/runbooks/`.

**Exercício:** pare o PostgreSQL (`kubectl -n kpi-dev scale sts kpi-db --replicas=0`).
Os pods saem do balanceamento (*readiness*), mas não são reiniciados (*liveness*).
O alerta dispara e o runbook diz o que fazer.

---

## Etapa 10 — Resiliência e melhoria contínua

**Objetivo:** provar a resiliência em vez de supor, e medir a evolução do time.

- **Caos:** com `make carga` rodando, execute `make caos`. Confira a hipótese
  descrita em `chaos/pod-kill.yaml` no dashboard.
- **Postmortem sem culpa:** registre o resultado do experimento ou de um
  incidente com o template de issue.
- **Métricas DORA:** veja [metricas-dora.md](metricas-dora.md) para medir
  frequência de deploy, lead time, taxa de falha e tempo de recuperação com o Apache DevLake.
- **Catálogo:** `catalog-info.yaml` registra o serviço no Backstage.

**Exercício final:** escolha uma métrica DORA, defina uma meta para o próximo
mês e proponha uma mudança no pipeline para alcançá-la.
