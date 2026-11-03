from sqlalchemy import String, Integer, ForeignKey, Table, Column
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

libro_categoria = Table(
    "libro_categoria",
    Base.metadata,
    Column("libro_id", Integer, ForeignKey("libros.id", ondelete="CASCADE"), primary_key=True),
    Column("categoria_id", Integer, ForeignKey("categorias.id", ondelete="CASCADE"), primary_key=True)
)

class Libro(Base):
    __tablename__ = "libros"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    titulo: Mapped[str] = mapped_column(String(150), nullable=False)
    isbn: Mapped[str] = mapped_column(String(13), unique=True, nullable=False)
    anio_publicacion: Mapped[int] = mapped_column(Integer, nullable=False)
    ejemplares: Mapped[int] = mapped_column(Integer, nullable=False)
    autor_id: Mapped[int] = mapped_column(ForeignKey("autores.id"), nullable=False)

    autor = relationship("Autor", back_populates="libros")
    categorias = relationship("Categoria", secondary=libro_categoria, back_populates="libros")
    prestamos = relationship("Prestamo", back_populates="libro")