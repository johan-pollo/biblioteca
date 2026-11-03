from sqlalchemy.orm import Session
from sqlalchemy import select
from app.controllers.paginacion import paginar
from app.models.categoria import Categoria
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate
from app.core.exceptions import NoEncontrado, Conflicto

def listar_categorias(db: Session, skip: int, limit: int):
    return paginar(db, select(Categoria), skip, limit)

def obtener_categoria(db: Session, categoria_id: int) -> Categoria:
    categoria = db.get(Categoria, categoria_id)
    if not categoria:
        raise NoEncontrado("Categoría no encontrada")
    return categoria

def crear_categoria(db: Session, datos: CategoriaCreate) -> Categoria:
    if db.query(Categoria).filter(Categoria.nombre == datos.nombre).first():
        raise Conflicto("La categoría ya existe")
    categoria = Categoria(**datos.model_dump())
    db.add(categoria)
    db.commit()
    db.refresh(categoria)
    return categoria

def actualizar_categoria(db: Session, categoria_id: int, datos: CategoriaUpdate) -> Categoria:
    categoria = obtener_categoria(db, categoria_id)
    datos_dict = datos.model_dump(exclude_unset=True)

    if "nombre" in datos_dict and datos_dict["nombre"] != categoria.nombre:
        if db.query(Categoria).filter(Categoria.nombre == datos_dict["nombre"]).first():
            raise Conflicto("Ya existe una categoría con ese nombre")

    for campo, valor in datos_dict.items():
        setattr(categoria, campo, valor)

    db.commit()
    db.refresh(categoria)
    return categoria

def eliminar_categoria(db: Session, categoria_id: int) -> None:
    categoria = obtener_categoria(db, categoria_id)
    db.delete(categoria)
    db.commit()