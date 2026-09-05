"""tablas iniciales

Revision ID: c75ef2124ff2
Revises: 
Create Date: 2026-09-02 21:39:56.426971

Migración baseline: las tablas ya existían en Neon (creadas a mano vía
schema.sql) antes de adoptar Alembic. No ejecuta cambios reales —
se aplica con 'alembic stamp head', no con 'upgrade', solo para que
Alembic empiece a llevar el control de versiones desde acá.
"""
from alembic import op
import sqlalchemy as sa


revision = 'c75ef2124ff2'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
