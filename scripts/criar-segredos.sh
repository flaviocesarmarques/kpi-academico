#!/usr/bin/env bash
# =============================================================================
# Gera o Secret da aplicação para um ambiente e o CRIPTOGRAFA com SOPS.
# Senhas aleatórias e fortes; o texto puro nunca toca o disco.
#
# Uso:  scripts/criar-segredos.sh dev     (ou prod)
# Saída: deploy/secrets/kpi-<ambiente>.enc.yaml  (pode e deve ser commitado)
# =============================================================================
set -euo pipefail

AMBIENTE="${1:?Informe o ambiente: dev ou prod}"
[[ "$AMBIENTE" =~ ^(dev|prod)$ ]] || { echo "Ambiente inválido: $AMBIENTE" >&2; exit 1; }
command -v sops >/dev/null || { echo "Instale o sops (veja infra/ansible)" >&2; exit 1; }
grep -q 'AGE-PUBLIC-KEY-AQUI' .sops.yaml && { echo "Configure sua chave pública em .sops.yaml" >&2; exit 1; }

SENHA_DB="$(openssl rand -hex 24)"
CHAVE_API="$(openssl rand -hex 32)"
DESTINO="deploy/secrets/kpi-${AMBIENTE}.enc.yaml"
mkdir -p deploy/secrets

# --filename-override só escolhe a regra do .sops.yaml; o arquivo não é lido.
# shellcheck disable=SC2094
cat <<EOF | sops --encrypt --filename-override "$DESTINO" --input-type yaml --output-type yaml /dev/stdin > "$DESTINO"
apiVersion: v1
kind: Secret
metadata:
  name: kpi-secrets
  namespace: kpi-${AMBIENTE}
type: Opaque
stringData:
  POSTGRES_PASSWORD: "${SENHA_DB}"
  KPI_API_KEY: "${CHAVE_API}"
  KPI_DATABASE_URL: "postgresql+psycopg://kpi:${SENHA_DB}@kpi-db:5432/kpi"
EOF

echo "Criado: $DESTINO (criptografado)."
echo "Chave de API do ambiente ${AMBIENTE} (guarde no cofre; não será mostrada de novo):"
echo "  ${CHAVE_API}"
