from datetime import datetime
from sqlalchemy import String, Integer, Boolean, DateTime, Index, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from app.core.database import Base

class Socio(Base):
    __tablename__ = "socios"
    __table_args__ = (
        Index("uq_socios_email_lower", func.lower(text("email")), unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(150), unique=True, nullable=False)
    telefono: Mapped[str | None] = mapped_column(String(15), nullable=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    fecha_alta: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    prestamos = relationship("Prestamo", back_populates="socio")