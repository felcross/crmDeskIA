"""add companies table + update tickets

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-08-27 01:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create companies table
    op.create_table('companies',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('nome', sa.String(length=255), nullable=False),
        sa.Column('origem', sa.String(length=50), nullable=False),
        sa.Column('deal_id', sa.Integer(), nullable=True),
        sa.Column('criado_em', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('nome'),
        sa.ForeignKeyConstraint(['deal_id'], ['deals.id']),
    )

    # Update tickets table
    op.add_column('tickets', sa.Column('company_id', sa.Integer(), nullable=True))
    op.add_column('tickets', sa.Column('cargo', sa.String(length=100), server_default='', nullable=False))
    op.create_foreign_key('fk_tickets_company', 'tickets', 'companies', ['company_id'], ['id'])


def downgrade() -> None:
    op.drop_constraint('fk_tickets_company', 'tickets', type_='foreignkey')
    op.drop_column('tickets', 'cargo')
    op.drop_column('tickets', 'company_id')
    op.drop_table('companies')
