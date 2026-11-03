"""Añade persistencia de refresh tokens.

Revision ID: 0004_refresh_tokens
Revises: 0003_usuarios
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0004_refresh_tokens"
down_revision: Union[str, None] = "0003_usuarios"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "refresh_tokens",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("jti", sa.String(length=36), nullable=False),
        sa.Column("usuario_id", sa.Integer(), nullable=False),
        sa.Column("expira_en", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "revocado",
            sa.Boolean(),
            server_default=sa.text("false"),
            nullable=False,
        ),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["usuario_id"],
            ["usuarios.id"],
            name=op.f("fk_refresh_tokens_usuario_id_usuarios"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_refresh_tokens")),
    )
    op.create_index(
        "uq_refresh_tokens_jti",
        "refresh_tokens",
        ["jti"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_refresh_tokens_jti", table_name="refresh_tokens")
    op.drop_table("refresh_tokens")
