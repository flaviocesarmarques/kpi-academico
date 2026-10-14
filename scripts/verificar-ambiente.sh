#!/usr/bin/env bash
# =============================================================================
# Diagnóstico do ambiente para a trilha DevOps (Linux, macOS e WSL2)
# -----------------------------------------------------------------------------
# Verifica, ETAPA POR ETAPA, se as ferramentas necessárias estão instaladas e
# mostra como instalar o que estiver faltando. Não instala nada sozinho.
#
# Uso:   bash scripts/verificar-ambiente.sh          (ou: make verificar)
#        bash scripts/verificar-ambiente.sh --tudo   (inclui etapas 6 a 10)
#
# Boa prática DevOps: "verifique pré-requisitos antes de começar" (fail fast).
# Um ambiente incompleto descoberto na etapa 7 custa muito mais caro.
#
# Saída: 0 se as ferramentas OBRIGATÓRIAS das etapas verificadas existem;
#        1 caso contrário (útil para usar em scripts e no Makefile).
# No Windows sem WSL, use scripts/verificar-ambiente.ps1.
# =============================================================================
set -uo pipefail

TUDO=0
[[ "${1:-}" == "--tudo" ]] && TUDO=1

# ---------- Detecção do sistema ----------------------------------------------
SO="linux"
if [[ "$(uname -s)" == "Darwin" ]]; then
  SO="macos"
elif grep -qi microsoft /proc/version 2>/dev/null; then
  SO="wsl"
fi

if [[ -t 1 ]]; then
  VERDE=$'\033[32m'; VERMELHO=$'\033[31m'; AMARELO=$'\033[33m'; NEGRITO=$'\033[1m'; FIM=$'\033[0m'
else
  VERDE=""; VERMELHO=""; AMARELO=""; NEGRITO=""; FIM=""
fi

FALTANDO_OBRIGATORIO=0
PENDENCIAS=()
LISTAR_PENDENCIAS=1   # 0 = só mostra o item, sem incluí-lo no resumo de instalação

# Instrução de instalação por sistema: dica <linux/wsl> <macos>
dica() {
  if [[ "$SO" == "macos" ]]; then echo "$2"; else echo "$1"; fi
}

# verificar <comando> <obrigatorio:1|0> <descricao> <instalacao linux/wsl> <instalacao macos> [args de versão]
verificar() {
  local cmd="$1" obrig="$2" desc="$3" inst_linux="$4" inst_mac="$5" args="${6:---version}"
  if command -v "$cmd" >/dev/null 2>&1; then
    local versao
    # shellcheck disable=SC2086 # args de versão podem ter mais de uma palavra
    versao="$("$cmd" $args 2>&1 | head -n1 | cut -c1-60)"
    printf "  %s✔%s %-22s %s\n" "$VERDE" "$FIM" "$cmd" "$versao"
  else
    if [[ "$obrig" == "1" ]]; then
      printf "  %s✘%s %-22s %s(obrigatório)%s %s\n" "$VERMELHO" "$FIM" "$cmd" "$VERMELHO" "$FIM" "$desc"
      FALTANDO_OBRIGATORIO=1
    else
      printf "  %s●%s %-22s %s(recomendado)%s %s\n" "$AMARELO" "$FIM" "$cmd" "$AMARELO" "$FIM" "$desc"
    fi
    if [[ "$obrig" == "1" || "$LISTAR_PENDENCIAS" == "1" ]]; then
      PENDENCIAS+=("$cmd: $(dica "$inst_linux" "$inst_mac")")
    fi
  fi
}

titulo() { printf "\n%s%s%s\n" "$NEGRITO" "$1" "$FIM"; }

APT="sudo apt update && sudo apt install -y"
PLAYBOOK="uvx --from ansible-core ansible-playbook -i infra/ansible/inventario.ini infra/ansible/estacao-devops.yml -K"

printf "%sDiagnóstico do ambiente — trilha DevOps kpi-academico%s\n" "$NEGRITO" "$FIM"
printf "Sistema: %s (%s)\n" "$SO" "$(uname -m)"

# ---------- Etapas 1 a 5: desenvolvimento, CI, segurança, container, release --
titulo "Etapas 1–5 · Código, CI, segurança, containers e release"
verificar git     1 "controle de versão" \
  "$APT git" "xcode-select --install"
verificar make    1 "atalhos do Makefile" \
  "$APT make" "xcode-select --install"
verificar curl    1 "downloads e testes de API" \
  "$APT curl" "já vem no macOS"
verificar uv      1 "Python, dependências e ferramentas (instala o Python sozinho)" \
  "curl -LsSf https://astral.sh/uv/install.sh | sh   (depois abra um novo terminal)" \
  "brew install uv   ou   curl -LsSf https://astral.sh/uv/install.sh | sh"
verificar docker  1 "containers (docker compose, Testcontainers, k3d)" \
  "$( [[ "$SO" == "wsl" ]] \
      && echo "instale o Docker Desktop no Windows (docker.com/products/docker-desktop) e ative Settings → Resources → WSL integration → Ubuntu" \
      || echo "curl -fsSL https://get.docker.com | sh && sudo usermod -aG docker \$USER   (depois saia e entre na sessão)")" \
  "instale o Docker Desktop (docker.com/products/docker-desktop) ou: brew install --cask docker"
verificar jq      0 "ler JSON no terminal (respostas da API, relatórios)" \
  "$APT jq" "brew install jq"
verificar openssl 0 "gerar senhas fortes (scripts/criar-segredos.sh)" \
  "$APT openssl" "já vem no macOS" "version"
verificar gh      0 "GitHub CLI: PRs, execuções do Actions, verificar atestados" \
  "$APT gh   (ou veja https://github.com/cli/cli#installation)" "brew install gh"
verificar cosign  0 "verificar assinatura das imagens publicadas (etapa 5)" \
  "use o playbook Ansible (abaixo)" "brew install cosign"

# Estado do Docker: instalado não significa funcionando.
if command -v docker >/dev/null 2>&1; then
  if docker info >/dev/null 2>&1; then
    printf "  %s✔%s %-22s %s\n" "$VERDE" "$FIM" "docker (serviço)" "em execução"
  else
    printf "  %s✘%s %-22s %s\n" "$VERMELHO" "$FIM" "docker (serviço)" "instalado, mas parado ou sem permissão"
    FALTANDO_OBRIGATORIO=1
    if [[ "$SO" == "wsl" ]]; then
      PENDENCIAS+=("docker (serviço): no WSL use o Docker Desktop do Windows, não um Docker instalado no Ubuntu. Abra o Docker Desktop, ative Settings → Resources → WSL integration → Ubuntu e clique em Apply & restart. Se houver Docker instalado no Ubuntu, remova-o (veja docs/pre-requisitos.md, 'Problemas comuns'). Depois, no PowerShell: wsl --shutdown, e reabra o Ubuntu")
    else
      PENDENCIAS+=("docker (serviço): $(dica \
        "sudo systemctl start docker e confirme 'docker run --rm hello-world'; sem sudo: sudo usermod -aG docker \$USER e reabra a sessão" \
        "abra o aplicativo Docker Desktop e aguarde ficar 'running'")")
    fi
  fi
  if [[ "$SO" == "wsl" ]] && dpkg -l docker.io docker-ce 2>/dev/null | grep -q '^ii'; then
    printf "  %s●%s %-22s %s\n" "$AMARELO" "$FIM" "docker (Ubuntu)" "Docker Engine instalado no Ubuntu: conflita com o Docker Desktop"
    PENDENCIAS+=("docker (Ubuntu): remova o Docker do Ubuntu e use só o Docker Desktop: sudo systemctl disable --now docker.service docker.socket; sudo apt remove -y docker.io docker-ce docker-ce-cli containerd.io docker-compose-v2 docker-compose-plugin")
  fi
  if docker compose version >/dev/null 2>&1; then
    printf "  %s✔%s %-22s %s\n" "$VERDE" "$FIM" "docker compose" "$(docker compose version --short 2>/dev/null)"
  else
    printf "  %s✘%s %-22s %s\n" "$VERMELHO" "$FIM" "docker compose" "plugin v2 ausente"
    FALTANDO_OBRIGATORIO=1
    PENDENCIAS+=("docker compose: $(dica "$APT docker-compose-v2   (ou atualize o Docker Desktop)" "atualize o Docker Desktop")")
  fi
fi

# ---------- Etapas 6 a 10: Kubernetes local, GitOps, observabilidade ----------
OBRIG_K8S=$TUDO
titulo "Etapas 6–10 · Kubernetes local, IaC, GitOps, observabilidade e caos"
if [[ $TUDO -eq 0 ]]; then
  echo "  (ainda não obrigatórias; rode com --tudo ao chegar na etapa 6)"
  LISTAR_PENDENCIAS=0
fi
verificar kubectl "$OBRIG_K8S" "cliente Kubernetes" \
  "use o playbook Ansible (abaixo)" "brew install kubectl" "version --client"
verificar k3d     "$OBRIG_K8S" "cluster Kubernetes local em Docker" \
  "use o playbook Ansible (abaixo)" "brew install k3d" "version"
verificar helm    "$OBRIG_K8S" "instalação de charts (usado pelo OpenTofu)" \
  "use o playbook Ansible (abaixo)" "brew install helm" "version --short"
verificar tofu    "$OBRIG_K8S" "OpenTofu: infraestrutura como código" \
  "use o playbook Ansible (abaixo)" "brew install opentofu" "version"
verificar sops    "$OBRIG_K8S" "segredos criptografados no Git" \
  "use o playbook Ansible (abaixo)" "brew install sops"
verificar age     "$OBRIG_K8S" "chaves de criptografia do SOPS" \
  "use o playbook Ansible (abaixo)" "brew install age"
verificar kubectl-argo-rollouts 0 "acompanhar e promover deploys canary" \
  "use o playbook Ansible (abaixo)" "brew install argoproj/tap/kubectl-argo-rollouts" "version --short"
verificar argocd  0 "CLI do Argo CD (opcional; a interface web basta)" \
  "use o playbook Ansible (abaixo)" "brew install argocd" "version --client --short"
verificar k6      0 "teste de carga (alternativa: via Docker, make carga)" \
  "use o playbook Ansible (abaixo)" "brew install k6" "version"

LISTAR_PENDENCIAS=1

# ---------- Recursos da máquina -----------------------------------------------
titulo "Recursos da máquina (cluster com observabilidade completa)"
if [[ "$SO" == "macos" ]]; then
  MEM_GB=$(( ($(sysctl -n hw.memsize) / 1024 / 1024 + 512) / 1024 ))
else
  # Arredonda para o GB mais próximo (8 GB físicos aparecem como ~7,7 GB úteis).
  MEM_GB=$(( ($(awk '/MemTotal/ {print $2}' /proc/meminfo) / 1024 + 512) / 1024 ))
fi
DISCO_GB=$(df -Pk . | awk 'NR==2 {print int($4/1024/1024)}')
CPUS=$(getconf _NPROCESSORS_ONLN 2>/dev/null || echo "?")

recurso() { # rotulo valor minimo unidade
  if [[ "$2" =~ ^[0-9]+$ ]] && (( $2 >= $3 )); then
    printf "  %s✔%s %-22s %s %s\n" "$VERDE" "$FIM" "$1" "$2" "$4"
  else
    printf "  %s●%s %-22s %s %s (recomendado: %s)\n" "$AMARELO" "$FIM" "$1" "$2" "$4" "$3"
  fi
}
recurso "Memória (RAM)" "$MEM_GB" 8 "GB"
recurso "Disco livre" "$DISCO_GB" 20 "GB"
recurso "CPUs" "$CPUS" 4 "núcleos"
if [[ "$SO" == "wsl" ]]; then
  echo "  i  No WSL a memória é limitada pelo Windows: ajuste em %UserProfile%\\.wslconfig ([wsl2] memory=8GB)"
  if [[ "$PWD" == /mnt/* ]]; then
    printf "  %s●%s O projeto está no disco do Windows (%s): mova para ~/ (muito mais rápido)\n" "$AMARELO" "$FIM" "$PWD"
  fi
fi

# ---------- Resumo -------------------------------------------------------------
titulo "Resumo"
if [[ ${#PENDENCIAS[@]} -eq 0 ]]; then
  printf "  %sTudo pronto!%s Próximo passo: make setup\n" "$VERDE" "$FIM"
else
  echo "  Instale o que falta:"
  for p in "${PENDENCIAS[@]}"; do echo "   - $p"; done
  if [[ "$SO" != "macos" ]]; then
    printf "\n  %sAtalho para as etapas 6–10%s (instala kubectl, k3d, helm, tofu, sops, age,\n" "$NEGRITO" "$FIM"
    echo "  argo rollouts, argocd, cosign, k6 e gh com versões fixas; requer uv e sudo):"
    echo "    $PLAYBOOK"
  fi
fi

if [[ $FALTANDO_OBRIGATORIO -eq 1 ]]; then
  printf "\n  %sFaltam itens obrigatórios.%s Instale-os, abra um novo terminal e rode de novo.\n" "$VERMELHO" "$FIM"
  exit 1
fi
exit 0
