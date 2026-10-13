"""Contratos da API (entrada e saída) com validação Pydantic.

Boa prática: nunca expor os modelos do banco diretamente na API. Os schemas
formam o CONTRATO público (documentado em /docs via OpenAPI); o banco pode
evoluir sem quebrar quem consome a API. Mudanças incompatíveis no contrato
exigem nova versão de rota (/api/v2) e um commit "feat!:" (major no SemVer).
"""

from pydantic import BaseModel, ConfigDict, Field, field_validator

from kpi_academico.kpis import Status, validar_periodo
from kpi_academico.models import Dimensao, Polaridade

# Siglas aceitas. Personalize com os cursos da sua instituição.
CURSOS_VALIDOS = frozenset({"CC", "EC", "ES", "CD", "IA", "ADS"})


class IndicadorEntrada(BaseModel):
    codigo: str = Field(min_length=2, max_length=20, pattern=r"^[A-Z0-9_\-]+$", examples=["EVA-01"])
    nome: str = Field(min_length=3, max_length=200)
    descricao: str | None = None
    formula: str | None = None
    dimensao: Dimensao
    unidade: str = Field(max_length=20, examples=["%"])
    meta: float = Field(ge=0)
    polaridade: Polaridade
    eixo_inep: str | None = Field(default=None, max_length=100)


class IndicadorSaida(IndicadorEntrada):
    model_config = ConfigDict(from_attributes=True)
    id: int


class MedicaoEntrada(BaseModel):
    codigo_indicador: str
    curso: str
    periodo: str = Field(examples=["2026.1"])
    valor: float = Field(ge=0)
    fonte: str | None = Field(default=None, max_length=200, examples=["Sistema acadêmico"])

    @field_validator("curso")
    @classmethod
    def _curso(cls, v: str) -> str:
        v = v.upper()
        if v not in CURSOS_VALIDOS:
            raise ValueError(f"Curso desconhecido. Válidos: {sorted(CURSOS_VALIDOS)}")
        return v

    @field_validator("periodo")
    @classmethod
    def _periodo(cls, v: str) -> str:
        return validar_periodo(v)


class MedicaoSaida(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    curso: str
    periodo: str
    valor: float
    fonte: str | None


class ItemPainel(BaseModel):
    codigo: str
    nome: str
    dimensao: Dimensao
    unidade: str
    meta: float
    valor: float | None
    atingimento: float | None
    status: Status
    variacao: float | None = None  # preenchido só com a flag "painel_tendencia" ligada


class ResumoPainel(BaseModel):
    verde: int = 0
    amarelo: int = 0
    vermelho: int = 0
    sem_dado: int = 0


class Painel(BaseModel):
    curso: str
    periodo: str
    resumo: ResumoPainel
    itens: list[ItemPainel]
