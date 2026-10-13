<!--
Título do PR no padrão Conventional Commits — ele vira a mensagem do squash merge
e alimenta o CHANGELOG. Ex.: "feat(painel): adiciona tendência por período".
PRs pequenos (< 400 linhas) são revisados mais rápido e com mais qualidade.
-->

## O que muda e por quê
<!-- Contexto para quem revisa. Link da issue: "Closes #123" fecha a issue no merge. -->

## Tipo de mudança
- [ ] `feat` — nova funcionalidade (versão minor)
- [ ] `fix` — correção (versão patch)
- [ ] `feat!` / `BREAKING CHANGE` — quebra de contrato da API (versão major)
- [ ] `docs` / `refactor` / `test` / `ci` / `build` / `chore`

## Checklist (Definition of Done)
- [ ] Testes adicionados/atualizados e passando (`make teste`)
- [ ] `make lint` sem erros (pre-commit instalado)
- [ ] Alteração em `models.py` acompanhada de migração Alembic **compatível com a versão anterior**
- [ ] Nenhum segredo, dado pessoal de estudante ou credencial no código (LGPD)
- [ ] Documentação/README atualizados, se aplicável
- [ ] Funcionalidade arriscada protegida por **feature flag** (registrada em `docs/feature-flags.md`)
- [ ] Métricas/logs/alertas pensados para a mudança (como saberemos se quebrou?)

## Como testar
<!-- Passos para o revisor validar localmente. -->

## Riscos e rollback
<!-- O que pode dar errado em produção e como desfazer (flag, revert, rollback do Argo). -->
