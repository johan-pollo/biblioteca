from datetime import date
from sqlalchemy import Integer, Date, Numeric, ForeignKey, Boolean, false
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Prestamo(Base):
    __tablename__ = "prestamos"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    libro_id: Mapped[int] = mapped_column(ForeignKey("libros.id"), nullable=False)
    socio_id: Mapped[int] = mapped_column(ForeignKey("socios.id"), nullable=False)
    registrado_por_id: Mapped[int | None] = mapped_column(
        ForeignKey("usuarios.id"), nullable=True
    )
    fecha_prestamo: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_limite: Mapped[date] = mapped_column(Date, nullable=False)
    fecha_devolucion: Mapped[date | None] = mapped_column(Date, nullable=True)
    multa: Mapped[float] = mapped_column(Numeric(10, 2), default=0.00, nullable=False)
    multa_pagada: Mapped[bool] = mapped_column(
        Boolean, default=False, server_default=false(), nullable=False
    )

    libro = relationship("Libro", back_populates="prestamos")
    socio = relationship("Socio", back_populates="prestamos")
    registrado_por = relationship("Usuario")