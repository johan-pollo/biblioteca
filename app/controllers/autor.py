from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import select
from app.controllers.paginacion import paginar
from app.models.autor import Autor
from app.schemas.autor import AutorCreate, AutorUpdate
from app.core.exceptions import NoEncontrado, Conflicto

def listar_autores(db: Session, skip: int, limit: int, nacionalidad: Optional[str] = None):
    query = select(Autor)
    if nacionalidad:
        query = query.where(Autor.nacionalidad.ilike(f"%{nacionalidad}%"))
    return paginar(db, query, skip, limit)

def obtener_autor(db: Session, autor_id: int) -> Autor:
    autor = db.get(Autor, autor_id)
    if not autor:
        raise NoEncontrado("Autor no encontrado")
    return autor

def crear_autor(db: Session, datos: AutorCreate) -> Autor:
    if db.query(Autor).filter(Autor.nombre == datos.nombre).first():
        raise Conflicto("El autor ya existe")
    autor = Autor(**datos.model_dump())
    db.add(autor)
    db.commit()
    db.refresh(autor)
    return autor

def actualizar_autor(db: Session, autor_id: int, datos: AutorUpdate) -> Autor:
    autor = obtener_autor(db, autor_id)
    datos_dict = datos.model_dump(exclude_unset=True)

    if "nombre" in datos_dict and datos_dict["nombre"] != autor.nombre:
        if db.query(Autor).filter(Autor.nombre == datos_dict["nombre"]).first():
            raise Conflicto("Ya existe un autor con ese nombre")

    for campo, valor in datos_dict.items():
        setattr(autor, campo, valor)

    db.commit()
    db.refresh(autor)
    return autor

def eliminar_autor(db: Session, autor_id: int) -> None:
    autor = obtener_autor(db, autor_id)
    if autor.libros:
        raise Conflicto("No se puede eliminar un autor que tiene libros registrados")
    db.delete(autor)
    db.commit()