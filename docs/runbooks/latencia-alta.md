# Runbook — KpiLatenciaAlta

**Severidade:** aviso · **SLO:** p95 abaixo de 500 ms

1. **Carga anormal?** Veja *Requisições por segundo* no dashboard. Em produção,
   confira se o HPA escalou: `kubectl -n kpi-prod get hpa kpi-api`.
2. **Banco lento?** Abra um trace lento no Tempo e veja quanto tempo foi gasto no banco.
   Consultas lentas no PostgreSQL:
   `kubectl -n <ns> exec -it kpi-db-0 -- psql -U kpi -c "select query, mean_exec_time from pg_stat_statements order by 2 desc limit 5"`
   (requer a extensão `pg_stat_statements`).
3. **Pods sem memória?** `kubectl -n <ns> top pods`. Reinícios por OOMKilled
   aparecem em `kubectl -n <ns> describe pod <pod>`.
4. **Experimento de caos ativo?** `kubectl get networkchaos,podchaos -A`.

Se a latência persistir por mais de 30 minutos, escale o incidente e abra um postmortem.
