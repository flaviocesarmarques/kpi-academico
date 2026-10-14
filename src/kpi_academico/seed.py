"""Popula o banco com indicadores e medições de EXEMPLO.

Uso:  uv run kpi-seed            (depois de `uv run alembic upgrade head`)

Os indicadores abaixo ilustram as 4 dimensões. Os valores são fictícios.
Substitua pela lista oficial de KPIs da sua coordenação (ex.: exportando
da planilha de OKRs/KPIs para CSV e adaptando a função `carregar`).
O script é IDEMPOTENTE: pode ser executado várias vezes sem duplicar dados.
"""

import random

from sqlalchemy import select
from sqlalchemy.orm import Session

from kpi_academico.db import get_engine
from kpi_academico.models import Dimensao as D  # noqa: N817 - tabela mais legível
from kpi_academico.models import Indicador, Medicao
from kpi_academico.models import Polaridade as P  # noqa: N817

INDICADORES = [
    # codigo, nome, dimensao, unidade, meta, polaridade, eixo_inep
    (
        "CUR-01",
        "Cobertura de ACE na matriz",
        D.FORMACAO_CURRICULO,
        "%",
        10,
        P.MAIOR_MELHOR,
        "Organização didático-pedagógica",
    ),
    (
        "CUR-02",
        "Aprovação nas disciplinas",
        D.FORMACAO_CURRICULO,
        "%",
        85,
        P.MAIOR_MELHOR,
        "Organização didático-pedagógica",
    ),
    (
        "EST-01",
        "Taxa de evasão",
        D.TRAJETORIA_ESTUDANTE,
        "%",
        12,
        P.MENOR_MELHOR,
        "Políticas acadêmicas",
    ),
    (
        "EST-02",
        "Taxa de conclusão no prazo",
        D.TRAJETORIA_ESTUDANTE,
        "%",
        55,
        P.MAIOR_MELHOR,
        "Políticas acadêmicas",
    ),
    (
        "EST-03",
        "Taxa de evasão no 1º ano",
        D.TRAJETORIA_ESTUDANTE,
        "%",
        15,
        P.MENOR_MELHOR,
        "Políticas acadêmicas",
    ),
    (
        "DOC-01",
        "Docentes com doutorado",
        D.DOCENTES_INOVACAO,
        "%",
        40,
        P.MAIOR_MELHOR,
        "Corpo docente e tutorial",
    ),
    (
        "DOC-02",
        "Projetos de inovação com empresas",
        D.DOCENTES_INOVACAO,
        "qtd",
        6,
        P.MAIOR_MELHOR,
        "Corpo docente e tutorial",
    ),
    (
        "QUA-01",
        "Conceito ENADE",
        D.QUALIDADE_GESTAO,
        "conceito",
        4,
        P.MAIOR_MELHOR,
        "Avaliação externa",
    ),
    (
        "QUA-02",
        "Satisfação discente (CPA)",
        D.QUALIDADE_GESTAO,
        "%",
        85,
        P.MAIOR_MELHOR,
        "Planejamento e avaliação institucional",
    ),
]
CURSOS = ["CC", "EC", "ES", "CD", "IA", "ADS"]
PERIODOS = ["2025.2", "2026.1"]


def carregar(sessao: Session) -> int:
    rng = random.Random(42)  # semente fixa: dados de exemplo reproduzíveis  # noqa: S311
    novos = 0
    for codigo, nome, dim, unidade, meta, pol, eixo in INDICADORES:
        ind = sessao.scalar(select(Indicador).where(Indicador.codigo == codigo))
        if ind is None:
            ind = Indicador(
                codigo=codigo,
                nome=nome,
                dimensao=dim,
                unidade=unidade,
                meta=meta,
                polaridade=pol,
                eixo_inep=eixo,
            )
            sessao.add(ind)
            sessao.flush()
        for curso in CURSOS:
            for periodo in PERIODOS:
                existe = sessao.scalar(
                    select(Medicao.id).where(
                        Medicao.indicador_id == ind.id,
                        Medicao.curso == curso,
                        Medicao.periodo == periodo,
                    )
                )
                if existe:
                    continue
                valor = round(meta * rng.uniform(0.7, 1.25), 1)
                sessao.add(
                    Medicao(
                        indicador_id=ind.id,
                        curso=curso,
                        periodo=periodo,
                        valor=valor,
                        fonte="seed de exemplo",
                    )
                )
                novos += 1
    sessao.commit()
    return novos


def main() -> None:
    with Session(get_engine()) as sessao:
        print(f"Medições inseridas: {carregar(sessao)}")


if __name__ == "__main__":
    main()
