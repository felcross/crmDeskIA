"""add lead_id to tickets

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-08-27 02:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = 'd4e5f6a7b8c9'
down_revision: str | None = 'c3d4e5f6a7b8'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column('tickets', sa.Column('lead_id', sa.Integer(), nullable=True))
    op.create_index('ix_tickets_lead_id', 'tickets', ['lead_id'])
    op.create_foreign_key('fk_tickets_lead', 'tickets', 'leads', ['lead_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_tickets_lead', 'tickets', type_='foreignkey')
    op.drop_index('ix_tickets_lead_id', table_name='tickets')
    op.drop_column('tickets', 'lead_id')
