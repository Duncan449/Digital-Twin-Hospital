"""alertas: agrega normalizada_en

Revision ID: 187f69574266
Revises: c75ef2124ff2
Create Date: 2026-09-05 00:00:00.000000

Agrega alertas.normalizada_en (timestamptz, nullable): lo completa el
AlertaWorkflow de Temporal cuando el signo vital se sostiene en "normal"
10 segundos seguidos. No reemplaza a resuelta_en -- una alerta puede
estar normalizada y seguir pendiente de que el personal registre una
Intervencion.
"""
from alembic import op
import sqlalchemy as sa


revision = '187f69574266'
down_revision = 'c75ef2124ff2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "alertas",
        sa.Column("normalizada_en", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("alertas", "normalizada_en")
