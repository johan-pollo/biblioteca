from datetime import datetime
from typing import Optional
from pydantic import BaseModel, ConfigDict, Field, EmailStr, field_validator

class SocioCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    email: EmailStr = Field(..., max_length=150)
    telefono: Optional[str] = Field(None, pattern=r"^[\d\s\+]{7,15}$")

    @field_validator("nombre")
    def format_nombre(cls, v: str):
        return " ".join(v.strip().split()).title()

    @field_validator("email")
    def format_email(cls, v: str):
        return v.strip().lower()

class SocioUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    email: Optional[EmailStr] = Field(None, max_length=150)
    telefono: Optional[str] = Field(None, pattern=r"^[\d\s\+]{7,15}$")

    @field_validator("nombre")
    def format_nombre(cls, v: Optional[str]):
        if v is not None:
            return " ".join(v.strip().split()).title()
        return v

    @field_validator("email")
    def format_email(cls, v: Optional[str]):
        if v is not None:
            return v.strip().lower()
        return v


class SocioActualizarPropio(BaseModel):
    model_config = ConfigDict(extra="forbid")

    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    telefono: Optional[str] = Field(None, pattern=r"^[\d\s\+]{7,15}$")

    @field_validator("nombre")
    @classmethod
    def format_nombre(cls, valor: Optional[str]):
        if valor is not None:
            return " ".join(valor.strip().split()).title()
        return valor

class SocioResponse(BaseModel):
    id: int
    nombre: str
    email: str
    telefono: Optional[str]
    activo: bool
    fecha_alta: datetime

    class Config:
        from_attributes = True