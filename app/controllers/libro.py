from typing import Optional
from sqlalchemy import select, func
from sqlalchemy.orm import Session, selectinload
from app.controllers.paginacion import paginar
from app.models.libro import Libro
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.prestamo import Prestamo
from app.schemas.libro import LibroCreate, LibroUpdate, OrdenLibros
from app.core.exceptions import NoEncontrado, Conflicto, ReglaNegocio

def calcular_disponibles(db: Session, libro_id: int, ejemplares_totales: int) -> int:
    prestamos_activos = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.libro_id == libro_id,
            Prestamo.fecha_devolucion.is_(None)
        )
    ) or 0
    return ejemplares_totales - prestamos_activos

def _formatear_libro_response(db: Session, libro: Libro) -> dict:
    disponibles = calcular_disponibles(db, libro.id, libro.ejemplares)
    return {
        "id": libro.id,
        "titulo": libro.titulo,
        "isbn": libro.isbn,
        "anio_publicacion": libro.anio_publicacion,
        "ejemplares": libro.ejemplares,
        "disponibles": disponibles,
        "autor": libro.autor,
        "categorias": libro.categorias
    }

def listar_libros(
    db: Session,
    skip: int,
    limit: int,
    buscar: Optional[str] = None,
    autor: Optional[str] = None,
    categoria_id: Optional[int] = None,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    orden: Optional[OrdenLibros] = None
):
    stmt = select(Libro).options(selectinload(Libro.autor), selectinload(Libro.categorias))

    if buscar:
        stmt = stmt.where(Libro.titulo.ilike(f"%{buscar}%"))
    if autor:
        stmt = stmt.join(Libro.autor).where(Autor.nombre.ilike(f"%{autor}%"))
    if categoria_id:
        stmt = stmt.join(Libro.categorias).where(Categoria.id == categoria_id)
    if desde:
        stmt = stmt.where(Libro.anio_publicacion >= desde)
    if hasta:
        stmt = stmt.where(Libro.anio_publicacion <= hasta)

    if orden == OrdenLibros.titulo:
        stmt = stmt.order_by(Libro.titulo.asc())
    elif orden == OrdenLibros.anio:
        stmt = stmt.order_by(Libro.anio_publicacion.asc())
    elif orden == OrdenLibros.anio_desc:
        stmt = stmt.order_by(Libro.anio_publicacion.desc())

    pagina = paginar(db, stmt, skip, limit, columna_unica=Libro.id)
    pagina["items"] = [_formatear_libro_response(db, libro) for libro in pagina["items"]]
    return pagina

def obtener_libro(db: Session, libro_id: int):
    stmt = select(Libro).options(selectinload(Libro.autor), selectinload(Libro.categorias)).where(Libro.id == libro_id)
    libro = db.scalar(stmt)
    if not libro:
        raise NoEncontrado("Libro no encontrado")
    return _formatear_libro_response(db, libro)

def crear_libro(db: Session, datos: LibroCreate):
    if db.query(Libro).filter(Libro.isbn == datos.isbn).first():
        raise Conflicto("Ya existe un libro con ese ISBN")

    autor = db.get(Autor, datos.autor_id)
    if not autor:
        raise NoEncontrado("El autor especificado no existe")

    categorias = db.query(Categoria).filter(Categoria.id.in_(datos.categoria_ids)).all()
    if len(categorias) != len(datos.categoria_ids):
        raise NoEncontrado("Una o más categorías especificadas no existen")

    libro = Libro(
        titulo=datos.titulo,
        isbn=datos.isbn,
        anio_publicacion=datos.anio_publicacion,
        ejemplares=datos.ejemplares,
        autor_id=datos.autor_id,
        categorias=categorias
    )
    db.add(libro)
    db.commit()
    db.refresh(libro)
    return obtener_libro(db, libro.id)

def actualizar_libro(db: Session, libro_id: int, datos: LibroUpdate):
    stmt = select(Libro).options(selectinload(Libro.autor), selectinload(Libro.categorias)).where(Libro.id == libro_id)
    libro = db.scalar(stmt)
    if not libro:
        raise NoEncontrado("Libro no encontrado")

    datos_dict = datos.model_dump(exclude_unset=True)

    if "isbn" in datos_dict and datos_dict["isbn"] != libro.isbn:
        if db.query(Libro).filter(Libro.isbn == datos_dict["isbn"]).first():
            raise Conflicto("Ya existe un libro con ese ISBN")

    if "autor_id" in datos_dict:
        autor = db.get(Autor, datos_dict["autor_id"])
        if not autor:
            raise NoEncontrado("El autor especificado no existe")
        libro.autor_id = datos_dict["autor_id"]

    if "categoria_ids" in datos_dict:
        cat_ids = datos_dict["categoria_ids"]
        categorias = db.query(Categoria).filter(Categoria.id.in_(cat_ids)).all()
        if len(categorias) != len(cat_ids):
            raise NoEncontrado("Una o más categorías especificadas no existen")
        libro.categorias = categorias

    if "ejemplares" in datos_dict:
        nuevos_ejemplares = datos_dict["ejemplares"]
        prestamos_activos = db.scalar(
            select(func.count(Prestamo.id)).where(
                Prestamo.libro_id == libro_id,
                Prestamo.fecha_devolucion.is_(None)
            )
        ) or 0
        if nuevos_ejemplares < prestamos_activos:
            raise ReglaNegocio("El número de ejemplares no puede ser menor a los préstamos activos")
        libro.ejemplares = nuevos_ejemplares

    for campo in ["titulo", "anio_publicacion"]:
        if campo in datos_dict:
            setattr(libro, campo, datos_dict[campo])

    db.commit()
    db.refresh(libro)
    return obtener_libro(db, libro.id)

def eliminar_libro(db: Session, libro_id: int) -> None:
    stmt = select(Libro).where(Libro.id == libro_id)
    libro = db.scalar(stmt)
    if not libro:
        raise NoEncontrado("Libro no encontrado")

    prestamos_activos = db.scalar(
        select(func.count(Prestamo.id)).where(
            Prestamo.libro_id == libro_id,
            Prestamo.fecha_devolucion.is_(None)
        )
    ) or 0
    if prestamos_activos > 0:
        raise Conflicto("No se puede eliminar el libro porque tiene préstamos sin devolver")

    db.delete(libro)
    db.commit()

def listar_libros_por_autor(db: Session, autor_id: int, skip: int, limit: int):
    autor = db.get(Autor, autor_id)
    if not autor:
        raise NoEncontrado("Autor no encontrado")

    stmt = (
        select(Libro)
        .options(selectinload(Libro.autor), selectinload(Libro.categorias))
        .where(Libro.autor_id == autor_id)
    )
    pagina = paginar(db, stmt, skip, limit, columna_unica=Libro.id)
    pagina["items"] = [_formatear_libro_response(db, libro) for libro in pagina["items"]]
    return pagina