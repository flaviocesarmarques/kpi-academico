"""O seed deve ser idempotente: rodar duas vezes não duplica dados."""

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from kpi_academico.db import get_engine
from kpi_academico.models import Medicao
from kpi_academico.seed import CURSOS, INDICADORES, PERIODOS, carregar


def test_seed_idempotente() -> None:
    with Session(get_engine()) as sessao:
        assert carregar(sessao) == len(INDICADORES) * len(CURSOS) * len(PERIODOS)
        assert carregar(sessao) == 0
        # modificação para teste dinâmico - Passo 4
        assert sessao.scalar(select(func.count(Medicao.id))) == (
            len(INDICADORES) * len(CURSOS) * len(PERIODOS)
        )
