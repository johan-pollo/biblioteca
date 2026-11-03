from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class AutorCreate(BaseModel):
    nombre: str = Field(..., min_length=2, max_length=100)
    nacionalidad: Optional[str] = Field(None, max_length=60)
    anio_nacimiento: Optional[int] = Field(None, ge=1000, le=datetime.now().year)

    @field_validator("nombre")
    def format_nombre(cls, v: str):
        return " ".join(v.strip().split()).title()

class AutorUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=2, max_length=100)
    nacionalidad: Optional[str] = Field(None, max_length=60)
    anio_nacimiento: Optional[int] = Field(None, ge=1000, le=datetime.now().year)

    @field_validator("nombre")
    def format_nombre(cls, v: Optional[str]):
        if v is not None:
            return " ".join(v.strip().split()).title()
        return v


class AutorResponse(AutorCreate):
    id: int
    class Config:
        from_attributes = True