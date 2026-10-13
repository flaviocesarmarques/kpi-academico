# Como contribuir

## Fluxo de trabalho (trunk-based development)

1. Crie uma branch curta a partir da `main`: `git switch -c feat/tendencia-painel`
2. Faça commits pequenos no padrão **Conventional Commits**.
3. Abra um Pull Request cedo (pode ser *draft*) e mantenha-o pequeno.
4. O CI precisa ficar verde e o PR precisa de aprovação do CODEOWNER.
5. Merge com **squash**: a `main` fica com um commit por mudança, sempre implantável.

Branches devem durar horas ou poucos dias, não semanas. Para trabalho grande e
inacabado, faça merge escondido atrás de uma **feature flag**.

## Conventional Commits

```
<tipo>(<escopo opcional>): <descrição no imperativo>

feat(painel): adiciona variação em relação ao período anterior
fix(api): corrige cálculo de atingimento para metas zeradas
docs: explica a promoção para produção
feat!: remove o campo "fonte" da resposta da API   ← quebra de contrato (major)
```

| Tipo | Efeito na versão |
|---|---|
| `fix` | patch (0.1.0 → 0.1.1) |
| `feat` | minor (0.1.0 → 0.2.0) |
| `feat!` ou rodapé `BREAKING CHANGE:` | major (1.0.0 → 2.0.0) |
| `docs`, `test`, `ci`, `chore`, `refactor`, `build` | não gera release sozinho |

## Ambiente de desenvolvimento

```bash
make setup     # instala dependências e hooks do pre-commit
make teste     # testes com cobertura
make lint      # todos os hooks em todos os arquivos
make rodar     # API local com recarga automática (SQLite)
```

## Mudanças no banco

Toda alteração em `src/kpi_academico/models.py` precisa de migração:

```bash
uv run alembic revision --autogenerate -m "adiciona coluna x"
```

Revise o arquivo gerado. Ele deve ser **compatível com a versão anterior** da
aplicação (padrão *expand → migrate → contract*). Por exemplo, para renomear
uma coluna: crie a nova, copie os dados, mude o código e só depois remova a antiga.
