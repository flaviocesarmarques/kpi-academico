"""Configuração da aplicação seguindo o princípio 12-Factor App (fator III).

Boas práticas:
  • Toda configuração vem de VARIÁVEIS DE AMBIENTE — o mesmo artefato (imagem
    Docker) roda em dev, homologação e produção mudando só o ambiente.
  • Segredos usam `SecretStr`: não aparecem em logs, repr() ou tracebacks.
  • Nenhum segredo real tem valor padrão. Em produção, a aplicação recusa
    iniciar com a chave de API de exemplo (falha rápida = "fail fast").

Customização: todas as variáveis usam o prefixo KPI_ (ex.: KPI_DATABASE_URL).
Veja o arquivo .env.example na raiz do repositório.
"""

from enum import StrEnum
from functools import lru_cache

from pydantic import SecretStr, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

CHAVE_DE_EXEMPLO = "troque-esta-chave"  # valor público, só para desenvolvimento


class Ambiente(StrEnum):
    DESENVOLVIMENTO = "dev"
    HOMOLOGACAO = "hml"
    PRODUCAO = "prod"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="KPI_", env_file=".env", extra="ignore")

    ambiente: Ambiente = Ambiente.DESENVOLVIMENTO
    # SQLite por padrão facilita o primeiro contato; em contêiner/cluster use PostgreSQL:
    # postgresql+psycopg://usuario:senha@host:5432/kpi
    database_url: str = "sqlite:///./kpi.db"
    api_key: SecretStr = SecretStr(CHAVE_DE_EXEMPLO)
    log_level: str = "INFO"

    # Limiares do "semáforo" de atingimento de meta (em % da meta).
    # Ajuste conforme a política da instituição (ex.: PDI, CPA).
    limite_verde: float = 100.0
    limite_amarelo: float = 85.0

    # Feature flags (etapa 8). Sem Unleash configurado, usa os valores locais abaixo.
    unleash_url: str | None = None
    unleash_token: SecretStr | None = None
    flag_painel_tendencia: bool = False

    @model_validator(mode="after")
    def _validar_producao(self) -> "Settings":
        if self.ambiente is Ambiente.PRODUCAO and (
            self.api_key.get_secret_value() == CHAVE_DE_EXEMPLO
        ):
            raise ValueError("KPI_API_KEY de exemplo não pode ser usada em produção.")
        if self.limite_amarelo > self.limite_verde:
            raise ValueError("limite_amarelo deve ser menor ou igual a limite_verde.")
        return self


@lru_cache
def get_settings() -> Settings:
    """Instância única (cacheada) — leia o ambiente uma vez por processo."""
    return Settings()
