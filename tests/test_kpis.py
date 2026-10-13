"""Testes UNITÁRIOS das regras de negócio (rápidos, sem banco e sem rede).

A base da pirâmide de testes: muitos testes pequenos e baratos.
`parametrize` documenta os casos de negócio de forma legível como tabela.
"""

import pytest

from kpi_academico.kpis import (
    Status,
    atingimento,
    classificar,
    periodo_anterior,
    validar_periodo,
    variacao,
)
from kpi_academico.models import Polaridade


@pytest.mark.parametrize(
    ("valor", "meta", "polaridade", "esperado"),
    [
        (85, 85, Polaridade.MAIOR_MELHOR, 100.0),
        (42.5, 85, Polaridade.MAIOR_MELHOR, 50.0),
        (8, 10, Polaridade.MENOR_MELHOR, 125.0),  # evasão abaixo da meta é bom
        (20, 10, Polaridade.MENOR_MELHOR, 50.0),
        (0, 10, Polaridade.MENOR_MELHOR, 200.0),  # evasão zero: teto
        (5, 0, Polaridade.MAIOR_MELHOR, 200.0),  # meta zero: teto
        (1000, 10, Polaridade.MAIOR_MELHOR, 200.0),
    ],
)
def test_atingimento(valor: float, meta: float, polaridade: Polaridade, esperado: float) -> None:
    assert atingimento(valor, meta, polaridade) == esperado


@pytest.mark.parametrize(
    ("percentual", "esperado"),
    [
        (None, Status.SEM_DADO),
        (100, Status.VERDE),
        (99.9, Status.AMARELO),
        (85, Status.AMARELO),
        (84.9, Status.VERMELHO),
    ],
)
def test_classificar(percentual: float | None, esperado: Status) -> None:
    assert classificar(percentual, limite_verde=100, limite_amarelo=85) is esperado


@pytest.mark.parametrize(("atual", "anterior"), [("2026.1", "2025.2"), ("2026.2", "2026.1")])
def test_periodo_anterior(atual: str, anterior: str) -> None:
    assert periodo_anterior(atual) == anterior


@pytest.mark.parametrize("invalido", ["2026", "2026.3", "26.1", "2026-1", ""])
def test_periodo_invalido(invalido: str) -> None:
    with pytest.raises(ValueError, match="Período inválido"):
        validar_periodo(invalido)


def test_variacao() -> None:
    assert variacao(10.5, 8.25) == 2.25
    assert variacao(10, None) is None
