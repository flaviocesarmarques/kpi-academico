"""Acesso ao banco de dados (SQLAlchemy 2.x).

Boas práticas:
  • O schema NÃO é criado pela aplicação em produção: quem cria/altera tabelas
    são as migrações Alembic (pasta migrations/), executadas como etapa
    separada do deploy (Job/initContainer no Kubernetes, serviço "migrate" no
    docker-compose). Isso torna mudanças de schema revisáveis e reversíveis.
  • `pool_pre_ping` evita erros com conexões derrubadas pelo banco.
  • A sessão é fornecida por injeção de dependência (`get_session`), o que
    permite trocá-la nos testes sem tocar no código de produção.
"""

from collections.abc import Iterator
from functools import lru_cache

from sqlalchemy import Engine, create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from kpi_academico.config import get_settings


class Base(DeclarativeBase):
    """Classe base de todos os modelos (usada também pelo Alembic)."""


@lru_cache
def get_engine() -> Engine:
    url = get_settings().database_url
    kwargs: dict[str, object] = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def get_session() -> Iterator[Session]:
    """Dependência FastAPI: abre uma sessão por requisição e sempre a fecha."""
    fabrica = sessionmaker(bind=get_engine(), expire_on_commit=False)
    with fabrica() as sessao:
        yield sessao
