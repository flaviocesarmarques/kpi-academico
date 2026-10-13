# Runbook — KpiApiIndisponivel

**Severidade:** crítica · nenhum pod da API está sendo coletado pelo Prometheus.

1. **Os pods existem?**
   ```bash
   kubectl -n <ns> get pods -l app.kubernetes.io/name=kpi-api
   kubectl -n <ns> describe pod <pod>          # eventos: ImagePullBackOff? CrashLoopBackOff?
   kubectl -n <ns> logs <pod> --previous       # logs da execução que caiu
   ```
2. **Imagem recusada pelo Kyverno?** Veja `kubectl get events -n <ns> | grep -i policy`.
   Imagem sem assinatura válida indica que não veio do pipeline: **não** contorne a política.
3. **Segredo ausente?** Erro de configuração ao iniciar → `make segredos-aplicar`.
4. **Argo CD fora de sincronia?** `argocd app get kpi-<ambiente>` ou veja pela interface web.
5. **Rollback:** reverta o último PR GitOps do ambiente.

Registre um postmortem ao final.
