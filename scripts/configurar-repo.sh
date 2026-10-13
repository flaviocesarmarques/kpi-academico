#!/usr/bin/env bash
# =============================================================================
# Personaliza o repositório para o SEU usuário/organização no GitHub.
# Troca o marcador SEU-USUARIO em manifestos, CODEOWNERS, Sonar e Argo CD.
#
# Uso:  scripts/configurar-repo.sh <usuario-ou-organizacao-github>
# Rode UMA vez, logo após clonar, e faça commit do resultado.
# =============================================================================
set -euo pipefail

DONO="${1:?Informe o usuário ou organização do GitHub}"
[[ "$DONO" =~ ^[A-Za-z0-9-]+$ ]] || { echo "Nome inválido: $DONO" >&2; exit 1; }
DONO_MINUSCULO="$(echo "$DONO" | tr '[:upper:]' '[:lower:]')" # o GHCR exige minúsculas

# Imagens do GHCR: sempre minúsculas
grep -rl 'ghcr.io/SEU-USUARIO' deploy policies | xargs -r sed -i "s#ghcr.io/SEU-USUARIO#ghcr.io/${DONO_MINUSCULO}#g"
# Demais referências (GitHub, CODEOWNERS, Sonar)
grep -rl 'SEU-USUARIO' --exclude-dir=.git --exclude-dir=.venv --exclude=configurar-repo.sh . \
  | xargs -r sed -i "s#SEU-USUARIO#${DONO}#g"

echo "Pronto. Revise com 'git diff' e faça commit:"
echo "  git commit -am 'chore: configura repositório para ${DONO}'"
