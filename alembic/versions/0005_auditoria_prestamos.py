"""Añade auditoría del usuario que registra cada préstamo nuevo.

Revision ID: 0005_auditoria_prestamos
Revises: 0004_refresh_tokens
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0005_auditoria_prestamos"
down_revision: Union[str, None] = "0004_refresh_tokens"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("prestamos") as batch_op:
        batch_op.add_column(
            sa.Column("registrado_por_id", sa.Integer(), nullable=True)
        )
        batch_op.create_foreign_key(
            op.f("fk_prestamos_registrado_por_id_usuarios"),
            "usuarios",
            ["registrado_por_id"],
            ["id"],
        )


def downgrade() -> None:
    with op.batch_alter_table("prestamos") as batch_op:
        batch_op.drop_constraint(
            op.f("fk_prestamos_registrado_por_id_usuarios"),
            type_="foreignkey",
        )
        batch_op.drop_column("registrado_por_id")
