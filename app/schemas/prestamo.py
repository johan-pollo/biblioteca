from datetime import date
from typing import Optional
from pydantic import BaseModel, Field, field_validator
from app.schemas.libro import LibroResponse
from app.schemas.socio import SocioResponse

class PrestamoCreate(BaseModel):
    socio_id: int
    libro_id: int
    fecha_prestamo: Optional[date] = Field(default_factory=date.today)
    dias: int = Field(default=14, ge=1, le=30)

    @field_validator("fecha_prestamo")
    def validate_fecha_prestamo(cls, v: date):
        if v > date.today():
            raise ValueError("La fecha de préstamo no puede ser futura")
        return v

class DevolucionCreate(BaseModel):
    fecha_devolucion: Optional[date] = Field(default_factory=date.today)

class PrestamoResponse(BaseModel):
    id: int
    libro_id: int
    socio_id: int
    fecha_prestamo: date
    fecha_limite: date
    fecha_devolucion: Optional[date]
    multa: float
    multa_pagada: bool
    registrado_por_id: Optional[int] = None
    estado: str
    libro: Optional[LibroResponse] = None
    socio: Optional[SocioResponse] = None

    class Config:
        from_attributes = True


class MultasPendientesRespuesta(BaseModel):
    items: list[PrestamoResponse]
    total: int
    skip: int
    limit: int
    total_adeudado: float