"""Autenticação simples por chave de API nas rotas de ESCRITA.

Boas práticas de segurança aplicadas:
  • Leitura pública (painéis), escrita protegida — princípio do menor privilégio.
  • Comparação em tempo constante (`hmac.compare_digest`) contra timing attacks.
  • A chave vem do ambiente (Secret do Kubernetes, criptografado com SOPS no Git).

Evolução recomendada para produção: OAuth2/OIDC com o provedor de identidade
da instituição (ex.: Keycloak, Microsoft Entra ID) e perfis por papel
(coordenador, NDE, CPA). O FastAPI tem suporte nativo em fastapi.security.
"""

import hmac

from fastapi import HTTPException, Security, status
from fastapi.security import APIKeyHeader

from kpi_academico.config import get_settings

_cabecalho = APIKeyHeader(name="X-API-Key", auto_error=False)


def exigir_api_key(chave: str | None = Security(_cabecalho)) -> None:
    esperada = get_settings().api_key.get_secret_value()
    if chave is None or not hmac.compare_digest(chave.encode(), esperada.encode()):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Chave de API inválida."
        )
