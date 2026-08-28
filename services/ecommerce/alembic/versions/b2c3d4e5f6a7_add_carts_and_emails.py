"""add abandoned_carts and email_logs

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-08-28 14:00:00.000000
"""
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op

revision: str = "b2c3d4e5f6a7"
down_revision: str | None = "a1b2c3d4e5f6"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "abandoned_carts",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("cliente_email", sa.String(255), nullable=False),
        sa.Column("cliente_nome", sa.String(255), nullable=False),
        sa.Column("valor_total", sa.Float(), server_default="0"),
        sa.Column("itens_json", sa.Text(), server_default="[]"),
        sa.Column("criado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_abandoned_carts_email", "abandoned_carts", ["cliente_email"])

    op.create_table(
        "email_logs",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("para", sa.String(255), nullable=False),
        sa.Column("assunto", sa.String(500), nullable=False),
        sa.Column("tipo", sa.String(50), nullable=False),
        sa.Column("enviado_em", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_email_logs_para", "email_logs", ["para"])


def downgrade() -> None:
    op.drop_table("email_logs")
    op.drop_table("abandoned_carts")
