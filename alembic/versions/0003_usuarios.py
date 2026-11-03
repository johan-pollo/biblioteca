"""Añade usuarios y roles.

Revision ID: 0003_usuarios
Revises: 0002_multa_pagada
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0003_usuarios"
down_revision: Union[str, None] = "0002_multa_pagada"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "rol",
            sa.Enum("admin", "bibliotecario", "socio", name="rolusuario"),
            server_default="socio",
            nullable=False,
        ),
        sa.Column("activo", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column(
            "intentos_fallidos",
            sa.Integer(),
            server_default=sa.text("0"),
            nullable=False,
        ),
        sa.Column("bloqueado_hasta", sa.DateTime(timezone=True), nullable=True),
        sa.Column("socio_id", sa.Integer(), nullable=True),
        sa.Column(
            "creado_en",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(
            ["socio_id"],
            ["socios.id"],
            name=op.f("fk_usuarios_socio_id_socios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_usuarios")),
        sa.UniqueConstraint("email", name=op.f("uq_usuarios_email")),
        sa.UniqueConstraint("socio_id", name=op.f("uq_usuarios_socio_id")),
    )
    op.create_index(
        "uq_usuarios_email_lower",
        "usuarios",
        [sa.text("lower(email)")],
        unique=True,
    )
    op.create_index(
        "uq_socios_email_lower",
        "socios",
        [sa.text("lower(email)")],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index("uq_socios_email_lower", table_name="socios")
    op.drop_index("uq_usuarios_email_lower", table_name="usuarios")
    op.drop_table("usuarios")
    sa.Enum(name="rolusuario").drop(op.get_bind())
