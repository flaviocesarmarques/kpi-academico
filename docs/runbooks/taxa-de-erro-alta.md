# Runbook — KpiTaxaErroAlta

**Severidade:** crítica · **SLO:** até 0,5% de respostas 5xx

## 1. Houve deploy recente?
```bash
kubectl argo rollouts get rollout kpi-api -n <namespace>
```
- **Canary em andamento:** aborte e volte para a versão estável:
  `kubectl argo rollouts abort kpi-api -n <namespace>`
- **Deploy concluído há pouco:** reverta o PR GitOps (`git revert`) e faça o
  merge. O Argo CD volta para a versão anterior.

## 2. Qual rota está falhando?
No Grafana, painel *Requisições por segundo (por rota)*, ou no Prometheus:
```promql
sum by (rota, status) (rate(http_requests_total{namespace="<ns>", status=~"5.."}[5m]))
```

## 3. O que os logs dizem?
Loki: `{namespace="<ns>", app="kpi-api"} | json | nivel="ERROR"`.
Abra o `trace_id` no Tempo para ver em que etapa a requisição falhou.

## 4. Dependências
- Banco: `kubectl -n <ns> get pods -l app.kubernetes.io/name=kpi-db`
- Readiness: `kubectl -n <ns> get pods -l app.kubernetes.io/name=kpi-api`

## 5. Funcionalidade nova?
Se o erro começou ao ligar uma *feature flag*, desligue-a no Unleash ou no
ConfigMap. É a forma mais rápida de mitigar.

## Depois
Abra um **postmortem** (template de issue) em até 5 dias úteis.
