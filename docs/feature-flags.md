# Registro de feature flags

Toda flag é dívida técnica temporária. Registre aqui ao criar e **remova o código
da flag** quando a funcionalidade estiver liberada para todos.

| Flag | O que controla | Dono | Criada em | Remover até | Estado |
|---|---|---|---|---|---|
| `painel_tendencia` | Variação do indicador em relação ao período anterior no painel | Coordenação de TI | 2026-10 | 2027-03 | Ligada em dev |

## Como funciona

- Sem Unleash: o valor vem da variável `KPI_FLAG_<NOME>` (ConfigMap do ambiente).
- Com Unleash (`KPI_UNLEASH_URL` definida): o valor vem do servidor e pode ser
  mudado em segundos, por ambiente, por percentual de usuários ou por grupo.
- Se o servidor de flags cair, vale o valor local: a aplicação **falha para o lado seguro**.

## Ciclo de vida

1. Crie a flag desligada e faça o merge do código. O deploy não muda o comportamento.
2. Ligue em dev, depois para um grupo piloto em produção e acompanhe o dashboard.
3. Ligue para todos.
4. Remova a flag e o caminho antigo do código em um PR `refactor:`.
