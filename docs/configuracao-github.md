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
| `RELEASE_APP_PRIVATE_KEY` | Chave privada do GitHub App de release (seção 7) | Sim, para o `release.yml` |

| Variável (*Settings → Secrets and variables → Actions → Variables*) | Para quê |
|---|---|
| `RELEASE_APP_CLIENT_ID` | Client ID do GitHub App de release (não é segredo) |

O GHCR, o Cosign e as atestações usam o token efêmero e o OIDC do próprio
GitHub Actions, sem credenciais de longa duração. A chave do GitHub App é a
única exceção, e ela gera tokens que **expiram em 1 hora** e valem só para este
repositório.

### SonarQube Cloud
1. Entre em sonarcloud.io com a conta do GitHub e importe o repositório.
2. Em *Administration → Analysis Method*, desative **Automatic Analysis**.
3. Gere o token e salve como `SONAR_TOKEN`.

## 6. Pacote no GHCR

Depois da primeira release, em *Packages → kpi-academico → Package settings*,
deixe o pacote **público**. Assim o cluster local baixa a imagem sem credencial.

## 7. GitHub App para os PRs automáticos (release e GitOps)

**Problema:** PRs criados com o `GITHUB_TOKEN` não disparam workflows (proteção
contra loops) ou ficam aguardando aprovação manual. Sem CI, os checks
obrigatórios do ruleset nunca chegam e o PR fica bloqueado.

**Solução:** o `release.yml` gera, a cada execução, um token de curta duração de
um GitHub App próprio (`actions/create-github-app-token`). PRs abertos pelo App
disparam o CI normalmente.

1. *Settings* da sua conta → *Developer settings* → *GitHub Apps* → **New GitHub App**.
   - Nome: ex. `kpi-academico-release-<usuario>` (precisa ser único no GitHub).
   - Homepage URL: a URL do repositório.
   - **Webhook**: desmarque *Active*.
   - *Repository permissions*: **Contents: Read and write** e
     **Pull requests: Read and write**. Nada além disso (menor privilégio).
   - *Where can this GitHub App be installed?*: **Only on this account**.
2. Na página do App, anote o **Client ID** e gere uma **private key** (`.pem`).
3. *Install App* → instale **somente** no repositório `kpi-academico`.
4. No repositório:
   - variável `RELEASE_APP_CLIENT_ID` = Client ID;
   - segredo `RELEASE_APP_PRIVATE_KEY` = conteúdo inteiro do `.pem`.
5. Apague o `.pem` do computador depois de cadastrá-lo (ou guarde-o num cofre de senhas).

Se a chave vazar: gere outra na página do App, troque o segredo e revogue a antiga.
