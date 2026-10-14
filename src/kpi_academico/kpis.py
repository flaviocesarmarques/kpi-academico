"""Regras de negócio PURAS do cálculo de indicadores.

Boa prática: separar a lógica de domínio (este módulo, sem banco nem HTTP)
da infraestrutura. Funções puras são triviais de testar (tests/test_kpis.py),
rápidas no CI e fáceis de auditar — importante quando o número vai para um
relatório da CPA ou para uma visita de avaliação do MEC.
"""

import re
from enum import StrEnum

from kpi_academico.models import Polaridade

PADRAO_PERIODO = re.compile(r"^\d{4}\.[12]$")
ATINGIMENTO_MAXIMO = 200.0  # evita distorções quando a meta é muito baixa


class Status(StrEnum):
    VERDE = "verde"  # meta atingida
    AMARELO = "amarelo"  # atenção: perto da meta
    VERMELHO = "vermelho"  # abaixo do aceitável
    SEM_DADO = "sem_dado"


def validar_periodo(periodo: str) -> str:
    """Valida o formato AAAA.S (semestre 1 ou 2)."""
    if not PADRAO_PERIODO.match(periodo):
        raise ValueError(f"Período inválido: {periodo!r}. Use AAAA.S, ex.: 2026.1")
    return periodo


def periodo_anterior(periodo: str) -> str:
    """2026.1 -> 2025.2 ; 2026.2 -> 2026.1"""
    ano, semestre = (int(p) for p in validar_periodo(periodo).split("."))
    return f"{ano - 1}.2" if semestre == 1 else f"{ano}.1"


def atingimento(valor: float, meta: float, polaridade: Polaridade) -> float:
    """Percentual de atingimento da meta (0 a 200).

    - Maior é melhor: valor / meta.
    - Menor é melhor: meta / valor (evasão de 8% com meta de 10% = 125%).
    """
    if polaridade is Polaridade.MAIOR_MELHOR:
        bruto = ATINGIMENTO_MAXIMO if meta == 0 else valor / meta * 10
    else:
        bruto = ATINGIMENTO_MAXIMO if valor == 0 else meta / valor * 100
    return round(min(max(bruto, 0.0), ATINGIMENTO_MAXIMO), 1)


def classificar(percentual: float | None, limite_verde: float, limite_amarelo: float) -> Status:
    """Converte o atingimento em semáforo, segundo os limiares configurados."""
    if percentual is None:
        return Status.SEM_DADO
    if percentual >= limite_verde:
        return Status.VERDE
    if percentual >= limite_amarelo:
        return Status.AMARELO
    return Status.VERMELHO


def variacao(atual: float, anterior: float | None) -> float | None:
    """Diferença absoluta em relação ao período anterior (mesma unidade do KPI)."""
    if anterior is None:
        return None
    return round(atual - anterior, 2)
