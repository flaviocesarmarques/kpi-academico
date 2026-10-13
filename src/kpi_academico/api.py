"""Rotas da API v1.

Versionamento de rota (/api/v1) permite evoluir o contrato sem quebrar
clientes existentes — prática essencial em entrega contínua.
"""

from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from kpi_academico import flags
from kpi_academico.config import get_settings
from kpi_academico.db import get_session
from kpi_academico.kpis import atingimento, classificar, periodo_anterior, variacao
from kpi_academico.models import Dimensao, Indicador, Medicao
from kpi_academico.observability import MEDICOES_REGISTRADAS
from kpi_academico.schemas import (
    CURSOS_VALIDOS,
    IndicadorEntrada,
    IndicadorSaida,
    ItemPainel,
    MedicaoEntrada,
    MedicaoSaida,
    Painel,
    ResumoPainel,
)
from kpi_academico.security import exigir_api_key

router = APIRouter(prefix="/api/v1", tags=["indicadores"])
SessaoDep = Annotated[Session, Depends(get_session)]


@router.get("/dimensoes", response_model=list[str])
def listar_dimensoes() -> list[str]:
    return [d.value for d in Dimensao]


@router.get("/indicadores", response_model=list[IndicadorSaida])
def listar_indicadores(sessao: SessaoDep, dimensao: Dimensao | None = None) -> list[Indicador]:
    consulta = select(Indicador).order_by(Indicador.codigo)
    if dimensao:
        consulta = consulta.where(Indicador.dimensao == dimensao)
    return list(sessao.scalars(consulta))


@router.post(
    "/indicadores",
    response_model=IndicadorSaida,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_api_key)],
)
def criar_indicador(dados: IndicadorEntrada, sessao: SessaoDep) -> Indicador:
    indicador = Indicador(**dados.model_dump())
    sessao.add(indicador)
    try:
        sessao.commit()
    except IntegrityError:
        sessao.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "Código de indicador já existe.") from None
    return indicador


@router.post(
    "/medicoes",
    response_model=MedicaoSaida,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(exigir_api_key)],
)
def registrar_medicao(dados: MedicaoEntrada, sessao: SessaoDep) -> Medicao:
    indicador = sessao.scalar(select(Indicador).where(Indicador.codigo == dados.codigo_indicador))
    if indicador is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Indicador não encontrado.")
    medicao = Medicao(
        indicador=indicador,
        curso=dados.curso,
        periodo=dados.periodo,
        valor=dados.valor,
        fonte=dados.fonte,
    )
    sessao.add(medicao)
    try:
        sessao.commit()
    except IntegrityError:
        sessao.rollback()
        raise HTTPException(
            status.HTTP_409_CONFLICT, "Já existe medição deste indicador para o curso e período."
        ) from None
    MEDICOES_REGISTRADAS.labels(curso=dados.curso).inc()
    return medicao


@router.get("/cursos/{curso}/painel", response_model=Painel)
def painel_do_curso(
    curso: str,
    sessao: SessaoDep,
    periodo: Annotated[str, Query(pattern=r"^\d{4}\.[12]$", examples=["2026.1"])],
) -> Painel:
    curso = curso.upper()
    if curso not in CURSOS_VALIDOS:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Curso não encontrado.")
    cfg = get_settings()
    com_tendencia = flags.ativa(flags.PAINEL_TENDENCIA)

    def valores(per: str) -> dict[int, float]:
        linhas = sessao.execute(
            select(Medicao.indicador_id, Medicao.valor).where(
                Medicao.curso == curso, Medicao.periodo == per
            )
        )
        return dict(linhas.tuples().all())

    atuais = valores(periodo)
    anteriores = valores(periodo_anterior(periodo)) if com_tendencia else {}

    resumo = ResumoPainel()
    itens: list[ItemPainel] = []
    for ind in sessao.scalars(select(Indicador).order_by(Indicador.dimensao, Indicador.codigo)):
        valor = atuais.get(ind.id)
        perc = atingimento(valor, ind.meta, ind.polaridade) if valor is not None else None
        st = classificar(perc, cfg.limite_verde, cfg.limite_amarelo)
        setattr(resumo, st.value, getattr(resumo, st.value) + 1)
        itens.append(
            ItemPainel(
                codigo=ind.codigo,
                nome=ind.nome,
                dimensao=ind.dimensao,
                unidade=ind.unidade,
                meta=ind.meta,
                valor=valor,
                atingimento=perc,
                status=st,
                variacao=(
                    variacao(valor, anteriores.get(ind.id))
                    if com_tendencia and valor is not None
                    else None
                ),
            )
        )
    return Painel(curso=curso, periodo=periodo, resumo=resumo, itens=itens)
