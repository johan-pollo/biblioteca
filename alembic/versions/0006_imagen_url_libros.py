"""Añade imagen_url a libros para portadas en Cloudinary.

Revision ID: 0006_imagen_url_libros
Revises: 0005_auditoria_prestamos
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0006_imagen_url_libros"
down_revision: Union[str, None] = "0005_auditoria_prestamos"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("libros") as batch_op:
        batch_op.add_column(
            sa.Column("imagen_url", sa.String(length=500), nullable=True)
        )


def downgrade() -> None:
    with op.batch_alter_table("libros") as batch_op:
        batch_op.drop_column("imagen_url")

