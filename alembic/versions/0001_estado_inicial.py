"""Estado inicial de la biblioteca.

Revision ID: 0001_estado_inicial
Revises:
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "0001_estado_inicial"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "autores",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("nacionalidad", sa.String(length=60), nullable=True),
        sa.Column("anio_nacimiento", sa.Integer(), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_autores")),
        sa.UniqueConstraint("nombre", name=op.f("uq_autores_nombre")),
    )
    op.create_index(op.f("ix_autores_id"), "autores", ["id"], unique=False)

    op.create_table(
        "categorias",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=50), nullable=False),
        sa.Column("descripcion", sa.String(length=200), nullable=True),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_categorias")),
        sa.UniqueConstraint("nombre", name=op.f("uq_categorias_nombre")),
    )
    op.create_index(op.f("ix_categorias_id"), "categorias", ["id"], unique=False)

    op.create_table(
        "socios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("nombre", sa.String(length=100), nullable=False),
        sa.Column("email", sa.String(length=150), nullable=False),
        sa.Column("telefono", sa.String(length=15), nullable=True),
        sa.Column("activo", sa.Boolean(), nullable=False),
        sa.Column(
            "fecha_alta",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_socios")),
        sa.UniqueConstraint("email", name=op.f("uq_socios_email")),
    )
    op.create_index(op.f("ix_socios_id"), "socios", ["id"], unique=False)

    op.create_table(
        "libros",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("titulo", sa.String(length=150), nullable=False),
        sa.Column("isbn", sa.String(length=13), nullable=False),
        sa.Column("anio_publicacion", sa.Integer(), nullable=False),
        sa.Column("ejemplares", sa.Integer(), nullable=False),
        sa.Column("autor_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["autor_id"],
            ["autores.id"],
            name=op.f("fk_libros_autor_id_autores"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_libros")),
        sa.UniqueConstraint("isbn", name=op.f("uq_libros_isbn")),
    )
    op.create_index(op.f("ix_libros_id"), "libros", ["id"], unique=False)

    op.create_table(
        "libro_categoria",
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("categoria_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(
            ["categoria_id"],
            ["categorias.id"],
            name=op.f("fk_libro_categoria_categoria_id_categorias"),
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["libro_id"],
            ["libros.id"],
            name=op.f("fk_libro_categoria_libro_id_libros"),
            ondelete="CASCADE",
        ),
        sa.PrimaryKeyConstraint(
            "libro_id", "categoria_id", name=op.f("pk_libro_categoria")
        ),
    )

    op.create_table(
        "prestamos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("libro_id", sa.Integer(), nullable=False),
        sa.Column("socio_id", sa.Integer(), nullable=False),
        sa.Column("fecha_prestamo", sa.Date(), nullable=False),
        sa.Column("fecha_limite", sa.Date(), nullable=False),
        sa.Column("fecha_devolucion", sa.Date(), nullable=True),
        sa.Column("multa", sa.Numeric(precision=10, scale=2), nullable=False),
        sa.ForeignKeyConstraint(
            ["libro_id"],
            ["libros.id"],
            name=op.f("fk_prestamos_libro_id_libros"),
        ),
        sa.ForeignKeyConstraint(
            ["socio_id"],
            ["socios.id"],
            name=op.f("fk_prestamos_socio_id_socios"),
        ),
        sa.PrimaryKeyConstraint("id", name=op.f("pk_prestamos")),
    )
    op.create_index(op.f("ix_prestamos_id"), "prestamos", ["id"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_prestamos_id"), table_name="prestamos")
    op.drop_table("prestamos")
    op.drop_table("libro_categoria")
    op.drop_index(op.f("ix_libros_id"), table_name="libros")
    op.drop_table("libros")
    op.drop_index(op.f("ix_socios_id"), table_name="socios")
    op.drop_table("socios")
    op.drop_index(op.f("ix_categorias_id"), table_name="categorias")
    op.drop_table("categorias")
    op.drop_index(op.f("ix_autores_id"), table_name="autores")
    op.drop_table("autores")
