"""Modelo de dados dos indicadores acadêmicos.

Estrutura em 4 dimensões (personalize em `Dimensao`):
  1. Formação e Currículo
  2. Trajetória do Estudante
  3. Corpo Docente e Inovação
  4. Qualidade, Avaliação e Gestão

Cada `Indicador` tem meta e polaridade (se "maior é melhor" ou "menor é
melhor", como em evasão). Cada `Medicao` registra o valor de um indicador
para um curso em um período letivo (AAAA.S, ex.: 2026.1).

Toda alteração neste arquivo exige uma NOVA migração Alembic:
    uv run alembic revision --autogenerate -m "descreva a mudança"
O CI verifica se modelos e migrações estão sincronizados (tests/test_migracoes.py).
"""

from datetime import UTC, datetime
from enum import StrEnum

from sqlalchemy import DateTime, Enum, Float, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from kpi_academico.db import Base


class Dimensao(StrEnum):
    FORMACAO_CURRICULO = "formacao_curriculo"
    TRAJETORIA_ESTUDANTE = "trajetoria_estudante"
    DOCENTES_INOVACAO = "docentes_inovacao"
    QUALIDADE_GESTAO = "qualidade_gestao"


class Polaridade(StrEnum):
    MAIOR_MELHOR = "maior_melhor"  # ex.: taxa de conclusão, conceito ENADE
    MENOR_MELHOR = "menor_melhor"  # ex.: taxa de evasão, retenção


def _agora() -> datetime:
    return datetime.now(UTC)


class Indicador(Base):
    __tablename__ = "indicador"

    id: Mapped[int] = mapped_column(primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)
    nome: Mapped[str] = mapped_column(String(200))
    descricao: Mapped[str | None] = mapped_column(Text)
    formula: Mapped[str | None] = mapped_column(Text)
    dimensao: Mapped[Dimensao] = mapped_column(
        Enum(Dimensao, native_enum=False, length=40, values_callable=lambda e: [m.value for m in e])
    )
    unidade: Mapped[str] = mapped_column(String(20))  # "%", "conceito", "nota", "qtd"
    meta: Mapped[float] = mapped_column(Float)
    polaridade: Mapped[Polaridade] = mapped_column(
        Enum(
            Polaridade, native_enum=False, length=20, values_callable=lambda e: [m.value for m in e]
        )
    )
    # Eixo/dimensão do instrumento de avaliação do Inep a que o KPI se relaciona.
    eixo_inep: Mapped[str | None] = mapped_column(String(100))

    medicoes: Mapped[list["Medicao"]] = relationship(back_populates="indicador")


class Medicao(Base):
    __tablename__ = "medicao"
    __table_args__ = (
        UniqueConstraint(
            "indicador_id", "curso", "periodo", name="uq_medicao_indicador_curso_periodo"
        ),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    indicador_id: Mapped[int] = mapped_column(ForeignKey("indicador.id", ondelete="CASCADE"))
    curso: Mapped[str] = mapped_column(String(10), index=True)  # sigla: CC, EC, ES, CD, IA, ADS
    periodo: Mapped[str] = mapped_column(String(6), index=True)  # AAAA.S
    valor: Mapped[float] = mapped_column(Float)
    fonte: Mapped[str | None] = mapped_column(String(200))  # rastreabilidade do dado
    registrado_em: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=_agora)

    indicador: Mapped[Indicador] = relationship(back_populates="medicoes")
