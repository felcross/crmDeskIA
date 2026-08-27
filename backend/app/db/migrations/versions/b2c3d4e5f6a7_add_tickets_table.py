"""add tickets table

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-27 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('tickets',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('descricao', sa.Text(), nullable=False),
        sa.Column('prioridade', sa.String(length=50), nullable=False, server_default='normal'),
        sa.Column('status', sa.String(length=50), nullable=False, server_default='aberto'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_tickets_email'), 'tickets', ['email'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_tickets_email'), table_name='tickets')
    op.drop_table('tickets')
