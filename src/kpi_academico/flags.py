"""Feature flags (etapa 8 da trilha) — separar DEPLOY de RELEASE.

O código novo vai para produção desligado; a funcionalidade é LIBERADA depois,
no painel do Unleash, para um grupo (ex.: só a coordenação) ou um percentual
de usuários, e pode ser desligada em segundos sem novo deploy.

Funcionamento:
  • Se KPI_UNLEASH_URL estiver definida, consulta o servidor Unleash.
  • Caso contrário, usa o valor local (variável KPI_FLAG_<NOME>), o que mantém
    o desenvolvimento e os testes simples e determinísticos.

Boa prática: toda flag tem DONO e DATA PARA REMOÇÃO. Flag esquecida vira
dívida técnica. Registre-as em docs/feature-flags.md.
"""

import logging
from functools import lru_cache
from typing import Any

from kpi_academico.config import get_settings

log = logging.getLogger(__name__)

PAINEL_TENDENCIA = "painel_tendencia"


@lru_cache
def _cliente_unleash() -> Any | None:
    cfg = get_settings()
    if not cfg.unleash_url:
        return None
    # Import tardio: só carrega o cliente quando o Unleash está configurado.
    from UnleashClient import UnleashClient  # type: ignore[attr-defined]

    token = cfg.unleash_token.get_secret_value() if cfg.unleash_token else ""
    cliente = UnleashClient(
        url=cfg.unleash_url,
        app_name="kpi-academico",
        environment=cfg.ambiente.value,
        custom_headers={"Authorization": token},
    )
    cliente.initialize_client()
    log.info("Feature flags via Unleash em %s", cfg.unleash_url)
    return cliente


def ativa(nome: str) -> bool:
    """Retorna se a flag está ligada. Em caso de falha, usa o valor local (seguro)."""
    padrao = bool(getattr(get_settings(), f"flag_{nome}", False))
    cliente = _cliente_unleash()
    if cliente is None:
        return padrao
    try:
        return bool(cliente.is_enabled(nome, fallback_function=lambda *_: padrao))
    except Exception:  # pragma: no cover - indisponibilidade do servidor de flags
        log.exception("Falha ao consultar Unleash; usando valor local da flag %s", nome)
        return padrao
