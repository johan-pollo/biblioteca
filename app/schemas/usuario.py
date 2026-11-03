from datetime import datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

from app.models.usuario import RolUsuario


class UsuarioRegistro(BaseModel):
    email: EmailStr = Field(max_length=150)
    nombre: str = Field(min_length=3, max_length=100)
    telefono: str | None = Field(default=None, pattern=r"^[\d\s\+]{7,15}$")
    password: str = Field(min_length=8, max_length=64)
    confirmar_password: str = Field(min_length=8, max_length=64)

    @field_validator("nombre")
    @classmethod
    def formatear_nombre(cls, valor: str) -> str:
        nombre = " ".join(valor.strip().split()).title()
        if len(nombre) < 3:
            raise ValueError("El nombre debe tener entre 3 y 100 caracteres")
        return nombre

    @model_validator(mode="before")
    @classmethod
    def validar_credenciales(cls, valores: object) -> object:
        if not isinstance(valores, dict):
            return valores

        password = valores.get("password")
        if isinstance(password, str) and (
            not any(caracter.isupper() for caracter in password)
            or not any(caracter.islower() for caracter in password)
            or not any(caracter.isdigit() for caracter in password)
        ):
            raise ValueError("La contraseña debe incluir mayúscula, minúscula y número")
        return valores

    @model_validator(mode="after")
    def validar_confirmacion(self) -> "UsuarioRegistro":
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden")
        return self


class UsuarioRespuesta(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    email: EmailStr
    nombre: str
    rol: RolUsuario
    activo: bool
    socio_id: int | None
    creado_en: datetime


class UsuarioCrear(BaseModel):
    email: EmailStr = Field(max_length=150)
    nombre: str = Field(min_length=3, max_length=100)
    password: str = Field(min_length=8, max_length=64)
    confirmar_password: str = Field(min_length=8, max_length=64)
    rol: RolUsuario

    @field_validator("nombre")
    @classmethod
    def formatear_nombre(cls, valor: str) -> str:
        return " ".join(valor.strip().split()).title()

    @model_validator(mode="after")
    def validar_clave(self) -> "UsuarioCrear":
        if self.password != self.confirmar_password:
            raise ValueError("Las contraseñas no coinciden")
        if (
            not any(caracter.isupper() for caracter in self.password)
            or not any(caracter.islower() for caracter in self.password)
            or not any(caracter.isdigit() for caracter in self.password)
        ):
            raise ValueError("La contraseña debe incluir mayúscula, minúscula y número")
        return self


class UsuarioRolActualizar(BaseModel):
    rol: RolUsuario


class UsuarioActivoActualizar(BaseModel):
    activo: bool