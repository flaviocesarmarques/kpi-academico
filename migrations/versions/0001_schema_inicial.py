"""schema inicial: indicador e medicao

Revision ID: 0001
Revises:
Create Date: 2026-10-12
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "0001"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "indicador",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("codigo", sa.String(20), nullable=False),
        sa.Column("nome", sa.String(200), nullable=False),
        sa.Column("descricao", sa.Text(), nullable=True),
        sa.Column("formula", sa.Text(), nullable=True),
        sa.Column(
            "dimensao",
            sa.Enum(
                "formacao_curriculo",
                "trajetoria_estudante",
                "docentes_inovacao",
                "qualidade_gestao",
                name="dimensao",
                native_enum=False,
                length=40,
            ),
            nullable=False,
        ),
        sa.Column("unidade", sa.String(20), nullable=False),
        sa.Column("meta", sa.Float(), nullable=False),
        sa.Column(
            "polaridade",
            sa.Enum(
                "maior_melhor", "menor_melhor", name="polaridade", native_enum=False, length=20
            ),
            nullable=False,
        ),
        sa.Column("eixo_inep", sa.String(100), nullable=True),
    )
    op.create_index("ix_indicador_codigo", "indicador", ["codigo"], unique=True)

    op.create_table(
        "medicao",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column(
            "indicador_id",
            sa.Integer(),
            sa.ForeignKey("indicador.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("curso", sa.String(10), nullable=False),
        sa.Column("periodo", sa.String(6), nullable=False),
        sa.Column("valor", sa.Float(), nullable=False),
        sa.Column("fonte", sa.String(200), nullable=True),
        sa.Column("registrado_em", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint(
            "indicador_id", "curso", "periodo", name="uq_medicao_indicador_curso_periodo"
        ),
    )
    op.create_index("ix_medicao_curso", "medicao", ["curso"])
    op.create_index("ix_medicao_periodo", "medicao", ["periodo"])


def downgrade() -> None:
    op.drop_index("ix_medicao_periodo", table_name="medicao")
    op.drop_index("ix_medicao_curso", table_name="medicao")
    op.drop_table("medicao")
    op.drop_index("ix_indicador_codigo", table_name="indicador")
    op.drop_table("indicador")
