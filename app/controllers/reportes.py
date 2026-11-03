from datetime import date
from sqlalchemy import select, func
from sqlalchemy.orm import Session
from app.controllers.paginacion import paginar
from app.models.libro import Libro, libro_categoria
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.socio import Socio
from app.models.prestamo import Prestamo

def libros_mas_prestados(db: Session, skip: int = 0, limit: int = 10):
    total = func.count(Prestamo.id).label("total_prestamos")
    stmt = (
        select(
            Libro.id.label("libro_id"),
            Libro.titulo,
            Autor.nombre.label("autor_nombre"),
            total
        )
        .join(Prestamo, Prestamo.libro_id == Libro.id)
        .join(Autor, Autor.id == Libro.autor_id)
        .group_by(Libro.id, Libro.titulo, Autor.nombre)
        .order_by(total.desc())
    )
    return paginar(db, stmt, skip, limit, mappings=True)

def reporte_categorias(db: Session, skip: int = 0, limit: int = 10):
    total = func.count(libro_categoria.c.libro_id).label("total_libros")
    stmt = (
        select(
            Categoria.id.label("categoria_id"),
            Categoria.nombre,
            total
        )
        .outerjoin(libro_categoria, libro_categoria.c.categoria_id == Categoria.id)
        .group_by(Categoria.id, Categoria.nombre)
    )
    return paginar(db, stmt, skip, limit, mappings=True)

def prestamos_vencidos(db: Session, skip: int = 0, limit: int = 10):
    hoy = date.today()
    retraso = (hoy - Prestamo.fecha_limite).label("dias_retraso")
    stmt = (
        select(
            Prestamo.id.label("prestamo_id"),
            Libro.titulo.label("titulo_libro"),
            Socio.nombre.label("socio_nombre"),
            Socio.email.label("socio_email"),
            Prestamo.fecha_limite,
            retraso
        )
        .join(Libro, Libro.id == Prestamo.libro_id)
        .join(Socio, Socio.id == Prestamo.socio_id)
        .where(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy)
    )
    return paginar(db, stmt, skip, limit, mappings=True)

def socios_con_multas(db: Session, skip: int = 0, limit: int = 10):
    stmt = (
        select(
            Socio.id.label("socio_id"),
            Socio.nombre.label("socio_nombre"),
            func.sum(Prestamo.multa).label("total_multas"),
            func.count(Prestamo.id).label("prestamos_con_multa")
        )
        .join(Prestamo, Prestamo.socio_id == Socio.id)
        .where(Prestamo.multa > 0)
        .group_by(Socio.id, Socio.nombre)
        .having(func.sum(Prestamo.multa) > 0)
    )
    return paginar(db, stmt, skip, limit, mappings=True)

def reporte_autores(db: Session, skip: int = 0, limit: int = 10):
    stmt = (
        select(
            Autor.id.label("autor_id"),
            Autor.nombre,
            func.count(func.distinct(Libro.id)).label("total_libros"),
            func.coalesce(func.sum(Libro.ejemplares), 0).label("total_ejemplares"),
            func.count(Prestamo.id).label("total_prestamos")
        )
        .outerjoin(Libro, Libro.autor_id == Autor.id)
        .outerjoin(Prestamo, Prestamo.libro_id == Libro.id)
        .group_by(Autor.id, Autor.nombre)
    )
    return paginar(db, stmt, skip, limit, mappings=True)

def resumen_general(db: Session):
    hoy = date.today()
    return {
        "total_libros": db.scalar(select(func.count(Libro.id))) or 0,
        "total_ejemplares": db.scalar(select(func.coalesce(func.sum(Libro.ejemplares), 0))) or 0,
        "total_prestamos_activos": db.scalar(select(func.count(Prestamo.id)).where(Prestamo.fecha_devolucion.is_(None))) or 0,
        "total_socios_activos": db.scalar(select(func.count(Socio.id)).where(Socio.activo.is_(True))) or 0,
        "total_prestamos_vencidos": db.scalar(select(func.count(Prestamo.id)).where(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy)) or 0,
        "total_multas_recabadas": float(db.scalar(select(func.coalesce(func.sum(Prestamo.multa), 0.0))) or 0.0)
    }