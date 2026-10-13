# Configuração única do repositório no GitHub

Estas configurações são feitas uma vez, na interface do GitHub, depois do primeiro push.

## 1. Proteção da `main` (ruleset)

*Settings → Rules → Rulesets → New ruleset → **Import a ruleset*** e escolha
`.github/rulesets/main.json`. O ruleset exige:

- PR obrigatório (sem push direto na main);
- todos os status checks do CI e de segurança verdes;
- histórico linear (squash merge) e commits assinados;
- bloqueio de push forçado e de exclusão da branch;
- nenhum alerta CodeQL de severidade alta.

> **Mantenedor único (configuração atual):** o GitHub não permite aprovar o próprio PR, por isso o ruleset vem com 0 aprovações. Ao trabalhar em equipe,
> mude `required_approving_review_count` para `1` e `require_code_owner_review` para `true`,
> mantenha os demais controles. Em turma, use um colega ou o professor como revisor.
>
> **Commits assinados:** configure a assinatura com chave SSH
> (`git config --global gpg.format ssh` e `git config --global commit.gpgsign true`)
> e cadastre a chave como *Signing key* no GitHub.

Em *Settings → General*: deixe apenas **Allow squash merging** e marque
**Automatically delete head branches**.

## 2. Segurança do código

*Settings → Code security*: ative **Dependency graph**, **Dependabot alerts**,
**Dependabot security updates**, **Secret scanning** com **Push protection** e
**Private vulnerability reporting**. Em **Code scanning**, mantenha a configuração
avançada, porque o CodeQL já roda pelo workflow `security.yml`.

## 3. Permissões do GitHub Actions

*Settings → Actions → General*:
- **Workflow permissions**: *Read repository contents* (o padrão mínimo; cada job pede o que precisa).
- Marque **Allow GitHub Actions to create and approve pull requests**, necessário
  para o release-please e para os PRs GitOps.

## 4. Ambientes (GitHub Environments)

*Settings → Environments*:

| Ambiente | Regras |
|---|---|
| `release` | Branch de deploy: somente `main` |
| `producao` | **Required reviewers** (ex.: coordenação + responsável técnico), somente `main`, *Prevent self-review* |

## 5. Segredos

| Segredo | Para quê | Obrigatório? |
|---|---|---|
| `SONAR_TOKEN` | Análise no SonarQube Cloud | Não. Sem ele, o job é pulado |

Nenhum outro segredo é necessário: o GHCR, o Cosign e as atestações usam o token
efêmero e o OIDC do próprio GitHub Actions. Esse é o padrão recomendado: sem
credenciais de longa duração guardadas.

### SonarQube Cloud
1. Entre em sonarcloud.io com a conta do GitHub e importe o repositório.
2. Em *Administration → Analysis Method*, desative **Automatic Analysis**.
3. Gere o token e salve como `SONAR_TOKEN`.

## 6. Pacote no GHCR

Depois da primeira release, em *Packages → kpi-academico → Package settings*,
deixe o pacote **público**. Assim o cluster local baixa a imagem sem credencial.

## 7. Opcional: GitHub App para PRs automáticos

PRs criados com o `GITHUB_TOKEN` não disparam outros workflows (proteção contra
loops). Para que o CI rode automaticamente nos PRs de release e GitOps, crie um
GitHub App com permissão de *Contents* e *Pull requests*, instale no repositório
e gere o token nos workflows com `actions/create-github-app-token`.
