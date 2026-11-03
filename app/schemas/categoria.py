from pydantic import BaseModel, Field, field_validator
from typing import Optional

class CategoriaCreate(BaseModel):
    nombre: str = Field(..., min_length=3, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=200)

    @field_validator("nombre")
    def format_nombre(cls, v: str):
        return " ".join(v.strip().split()).lower()

class CategoriaUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=3, max_length=50)
    descripcion: Optional[str] = Field(None, max_length=200)

    @field_validator("nombre")
    def format_nombre(cls, v: Optional[str]):
        if v is not None:
            return " ".join(v.strip().split()).lower()
        return v


class CategoriaResponse(CategoriaCreate):
    id: int
    class Config:
        from_attributes = True