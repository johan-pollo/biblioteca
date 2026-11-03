from datetime import datetime
from enum import Enum

from sqlalchemy import Boolean, DateTime, Enum as SqlEnum, ForeignKey, Index
from sqlalchemy import Integer, String, UniqueConstraint, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship, validates

from app.core.database import Base


class RolUsuario(str, Enum):
    ADMIN = "admin"
    BIBLIOTECARIO = "bibliotecario"
    SOCIO = "socio"


class Usuario(Base):
    __tablename__ = "usuarios"
    __table_args__ = (
        UniqueConstraint("email", name="uq_usuarios_email"),
        UniqueConstraint("socio_id", name="uq_usuarios_socio_id"),
        Index("uq_usuarios_email_lower", func.lower(text("email")), unique=True),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(150), nullable=False)
    nombre: Mapped[str] = mapped_column(String(100), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    rol: Mapped[RolUsuario] = mapped_column(
        SqlEnum(
            RolUsuario,
            name="rolusuario",
            values_callable=lambda roles: [rol.value for rol in roles],
        ),
        default=RolUsuario.SOCIO,
        server_default=RolUsuario.SOCIO.value,
        nullable=False,
    )
    activo: Mapped[bool] = mapped_column(
        Boolean, default=True, server_default=text("true"), nullable=False
    )
    intentos_fallidos: Mapped[int] = mapped_column(
        Integer, default=0, server_default=text("0"), nullable=False
    )
    bloqueado_hasta: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    socio_id: Mapped[int | None] = mapped_column(
        ForeignKey("socios.id"), nullable=True
    )
    creado_en: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    socio = relationship("Socio")
    refresh_tokens = relationship(
        "RefreshToken", back_populates="usuario", cascade="all, delete-orphan"
    )

    @validates("nombre")
    def formatear_nombre(self, clave: str, valor: str) -> str:
        return " ".join(valor.strip().split()).title()

    @validates("email")
    def normalizar_email(self, clave: str, valor: str) -> str:
        return valor.strip().lower()