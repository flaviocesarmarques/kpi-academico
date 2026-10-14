# Pré-requisitos do ambiente

Antes de começar a trilha, **verifique o ambiente**. O diagnóstico lista o que
está instalado, o que falta e como instalar cada item. Ele não instala nada sozinho.

| Sistema | Comando |
|---|---|
| Linux, macOS ou WSL (Ubuntu) | `bash scripts/verificar-ambiente.sh` (ou `make verificar`) |
| Windows (PowerShell) | `powershell -ExecutionPolicy Bypass -File scripts\verificar-ambiente.ps1` |
| Ao chegar na etapa 6 | `bash scripts/verificar-ambiente.sh --tudo` (ou `make verificar-tudo`) |

> **Windows:** a trilha roda dentro do **WSL2 com Ubuntu**. O Makefile usa bash,
> e Docker, k3d e Ansible são ferramentas Linux. Rode primeiro o diagnóstico em
> PowerShell, que confere WSL2, virtualização e Docker Desktop. Depois, clone o
> repositório **dentro do Ubuntu** (em `~/`, não em `/mnt/c`) e rode o diagnóstico bash.

## O que é necessário em cada etapa

| Ferramenta | Etapas | Obrigatória? | Para quê |
|---|---|---|---|
| git | 1–10 | Sim | Controle de versão |
| make | 1–10 | Sim | Atalhos do Makefile |
| curl | 1–10 | Sim | Downloads e testes da API |
| **uv** | 1–10 | Sim | Instala o Python, as dependências e ferramentas como pre-commit e Ansible |
| **Docker** (com Compose v2) | 2–10 | Sim | Containers, Testcontainers, ZAP, k6 e o cluster k3d |
| jq, openssl | 4–7 | Recomendada | Ler JSON e gerar senhas dos segredos |
| gh (GitHub CLI) | 1–10 | Recomendada | PRs, execuções do Actions e verificação de atestados |
| cosign | 5 | Recomendada | Verificar a assinatura das imagens |
| kubectl, k3d, helm | 6–10 | Sim, a partir da 6 | Cluster Kubernetes local |
| tofu (OpenTofu) | 6–10 | Sim, a partir da 6 | Infraestrutura como código (o hook `tofu_fmt` usa ao editar `.tf`) |
| sops, age | 7–10 | Sim, a partir da 7 | Segredos criptografados no Git |
| kubectl-argo-rollouts | 8–10 | Recomendada | Acompanhar e promover o canary |
| argocd | 7–10 | Opcional | CLI do Argo CD (a interface web basta) |
| k6 | 8 | Opcional | Teste de carga (`make carga` usa Docker) |

O Python **não** precisa ser instalado à parte: o `uv` baixa a versão certa.

**Recursos da máquina:** as etapas 1 a 5 rodam em qualquer computador. As
etapas 6 a 10 (cluster com Argo CD, Kyverno e observabilidade) pedem cerca de
**8 GB de RAM livres, 4 núcleos e 20 GB de disco**. Com menos, desligue
componentes em `infra/tofu/terraform.tfvars`.

## Instalação rápida

### Windows
```powershell
# PowerShell como administrador; reinicie o computador ao final
wsl --install -d Ubuntu
winget install -e --id Docker.DockerDesktop
```
No Docker Desktop, ative *Settings → Resources → WSL integration → Ubuntu*.
Depois, no terminal **Ubuntu**, siga as instruções de Linux abaixo, exceto a do Docker.

### Linux / WSL (Ubuntu)
```bash
sudo apt update && sudo apt install -y git make curl jq openssl gh
curl -LsSf https://astral.sh/uv/install.sh | sh          # depois: exec $SHELL
# Docker (somente Linux nativo; no WSL use o Docker Desktop):
curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker $USER   # saia e entre na sessão
```
Ferramentas das etapas 6 a 10, com versões fixas, num único comando idempotente:
```bash
uvx --from ansible-core ansible-playbook -i infra/ansible/inventario.ini \
    infra/ansible/estacao-devops.yml -K
```

### macOS (Homebrew)
```bash
xcode-select --install
brew install uv jq gh cosign
brew install --cask docker                                  # abra o Docker Desktop uma vez
# Etapas 6–10:
brew install kubectl k3d helm opentofu sops age k6 argocd argoproj/tap/kubectl-argo-rollouts
```

## Depois de instalar

Abra um **novo terminal**, para que o PATH seja recarregado, e confirme:
```bash
make verificar      # deve terminar com "Tudo pronto!"
make setup          # dependências do projeto e hooks do pre-commit
```

## Problemas comuns

| Sintoma | Causa e solução |
|---|---|
| `uv: command not found` logo após instalar | O terminal não recarregou o PATH. Abra outro terminal ou rode `exec $SHELL`. Persistindo: `echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc` |
| `make: command not found` no Windows | O Windows não tem make. Use o terminal Ubuntu (WSL) |
| `permission denied ... docker.sock` | Usuário fora do grupo docker: `sudo usermod -aG docker $USER` e entre de novo na sessão |
| `Cannot connect to the Docker daemon` | O Docker está parado. No Windows, abra o Docker Desktop e confira se a integração WSL com o Ubuntu está ativa |
| `Failed to start docker.service` (WSL) | Há um Docker Engine instalado **dentro** do Ubuntu, conflitando com o Docker Desktop. Remova-o: `sudo systemctl disable --now docker.service docker.socket` e `sudo apt remove -y docker.io docker-ce docker-ce-cli containerd.io docker-compose-v2 docker-compose-plugin`. Depois rode `wsl --shutdown` no PowerShell, reabra o Ubuntu e teste `docker run --rm hello-world` |
| Tudo muito lento no WSL | O projeto está em `/mnt/c/...`. Clone em `~/` dentro do Ubuntu |
| `tofu: command not found` ao commitar | Você editou um arquivo `.tf` sem ter o OpenTofu instalado. Instale-o (etapa 6) |
