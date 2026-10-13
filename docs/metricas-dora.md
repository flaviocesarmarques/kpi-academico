# Métricas DORA

As quatro métricas do programa DORA medem a performance de entrega de software:

| Métrica | Pergunta | Fonte neste projeto |
|---|---|---|
| Frequência de deploy | Com que frequência entregamos em produção? | PRs `chore(deploy): prod -> X` mesclados |
| Lead time para mudanças | Quanto tempo do commit até produção? | Data do commit × merge do PR de produção |
| Taxa de falha de mudança | Quantos deploys causam incidente? | Issues `postmortem` com "causado por mudança = Sim" |
| Tempo de recuperação | Quanto tempo para restaurar o serviço? | Linha do tempo dos postmortems e alertas |

## Coletando com o Apache DevLake (livre)

O Apache DevLake lê GitHub e GitHub Actions e já traz um dashboard DORA no Grafana.

1. Siga o guia de instalação via Docker Compose em `https://devlake.apache.org`.
2. Crie uma conexão com o GitHub (token somente leitura) e adicione este repositório.
3. Em *Transformations*, ajuste:
   - **Deployment**: workflow `Promover para produção`;
   - **Incident**: issues com o rótulo `incidente`.
4. Abra o dashboard **DORA** no Grafana do DevLake.

## Boas práticas

- Use as métricas para melhorar o **sistema**, nunca para comparar pessoas.
- Olhe a tendência ao longo dos meses, não o número de uma semana.
- Velocidade (frequência, lead time) e estabilidade (falhas, recuperação)
  melhoram **juntas** quando as mudanças são pequenas e automatizadas.
