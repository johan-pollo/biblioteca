from enum import Enum
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator
from app.schemas.autor import AutorResponse
from app.schemas.categoria import CategoriaResponse

class OrdenLibros(str, Enum):
    titulo = "titulo"
    anio = "anio"
    anio_desc = "-anio"

class LibroCreate(BaseModel):
    titulo: str = Field(..., min_length=1, max_length=150)
    isbn: str = Field(..., pattern=r"^\d{13}$")
    anio_publicacion: int = Field(..., ge=1450, le=datetime.now().year)
    ejemplares: int = Field(..., ge=1, le=50)
    autor_id: int
    categoria_ids: list[int] = Field(..., min_length=1, max_length=5)
    imagen_url: Optional[str] = Field(None, max_length=500)

    @field_validator("titulo")
    def format_titulo(cls, v: str):
        return " ".join(v.strip().split()).title()

    @field_validator("categoria_ids")
    def validate_unique_categorias(cls, v: list[int]):
        if len(v) != len(set(v)):
            raise ValueError("Las categorías no pueden contener duplicados")
        return v

class LibroUpdate(BaseModel):
    titulo: Optional[str] = Field(None, min_length=1, max_length=150)
    isbn: Optional[str] = Field(None, pattern=r"^\d{13}$")
    anio_publicacion: Optional[int] = Field(None, ge=1450, le=datetime.now().year)
    ejemplares: Optional[int] = Field(None, ge=1, le=50)
    autor_id: Optional[int] = None
    categoria_ids: Optional[list[int]] = Field(None, min_length=1, max_length=5)
    imagen_url: Optional[str] = Field(None, max_length=500)

    @field_validator("titulo")
    def format_titulo(cls, v: Optional[str]):
        if v is not None:
            return " ".join(v.strip().split()).title()
        return v

    @field_validator("categoria_ids")
    def validate_unique_categorias(cls, v: Optional[list[int]]):
        if v is not None and len(v) != len(set(v)):
            raise ValueError("Las categorías no pueden contener duplicados")
        return v

class LibroResponse(BaseModel):
    id: int
    titulo: str
    isbn: str
    anio_publicacion: int
    ejemplares: int
    disponibles: int
    imagen_url: Optional[str] = None
    autor: AutorResponse
    categorias: list[CategoriaResponse]

    class Config:
        from_attributes = True