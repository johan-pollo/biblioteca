from typing import Optional
from datetime import date
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import select
from app.controllers.paginacion import paginar
from app.models.socio import Socio
from app.models.prestamo import Prestamo
from app.models.libro import Libro
from app.models.usuario import Usuario
from app.schemas.socio import SocioCreate, SocioUpdate
from app.core.exceptions import NoEncontrado, Conflicto
from app.controllers.prestamo import _formatear_prestamo_response

def listar_socios(db: Session, skip: int, limit: int, activo: Optional[bool] = None):
    query = select(Socio)
    if activo is not None:
        query = query.where(Socio.activo == activo)
    return paginar(db, query, skip, limit)

def obtener_socio(db: Session, socio_id: int) -> Socio:
    socio = db.get(Socio, socio_id)
    if not socio:
        raise NoEncontrado("Socio no encontrado")
    return socio

def crear_socio(db: Session, datos: SocioCreate) -> Socio:
    if db.query(Socio).filter(Socio.email == datos.email).first():
        raise Conflicto("El email ya está registrado")
    socio = Socio(**datos.model_dump())
    db.add(socio)
    db.commit()
    db.refresh(socio)
    return socio

def actualizar_socio(db: Session, socio_id: int, datos: SocioUpdate) -> Socio:
    socio = obtener_socio(db, socio_id)
    datos_dict = datos.model_dump(exclude_unset=True)

    if "email" in datos_dict and datos_dict["email"] != socio.email:
        if db.query(Socio).filter(Socio.email == datos_dict["email"]).first():
            raise Conflicto("El email ya está registrado por otro socio")

    for campo, valor in datos_dict.items():
        setattr(socio, campo, valor)

    db.commit()
    db.refresh(socio)
    return socio

def eliminar_socio(db: Session, socio_id: int) -> None:
    socio = obtener_socio(db, socio_id)

    prestamos_activos = db.query(Prestamo).filter(
        Prestamo.socio_id == socio_id,
        Prestamo.fecha_devolucion.is_(None)
    ).count()
    if prestamos_activos > 0:
        raise Conflicto("No se puede eliminar el socio porque tiene préstamos sin devolver")

    total_prestamos = db.query(Prestamo).filter(Prestamo.socio_id == socio_id).count()
    if total_prestamos > 0:
        socio.activo = False
        db.commit()
    else:
        db.delete(socio)
        db.commit()

def obtener_prestamos_socio(
    db: Session,
    socio_id: int,
    estado: Optional[str] = None,
    skip: int = 0,
    limit: int = 10,
):
    obtener_socio(db, socio_id)
    query = select(Prestamo).options(
        selectinload(Prestamo.libro).selectinload(Libro.autor),
        selectinload(Prestamo.libro).selectinload(Libro.categorias),
        selectinload(Prestamo.socio),
    ).where(Prestamo.socio_id == socio_id)

    hoy = date.today()
    if estado == "activo":
        query = query.where(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite >= hoy)
    elif estado == "vencido":
        query = query.where(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy)
    elif estado == "devuelto":
        query = query.where(Prestamo.fecha_devolucion.is_not(None))

    pagina = paginar(db, query, skip, limit)
    pagina["items"] = [
        _formatear_prestamo_response(db, prestamo) for prestamo in pagina["items"]
    ]
    return pagina


def obtener_socio_del_usuario(db: Session, usuario: Usuario) -> Socio:
    if usuario.socio_id is None:
        raise NoEncontrado("El usuario no tiene un socio vinculado")
    return obtener_socio(db, usuario.socio_id)


def actualizar_socio_propio(db: Session, usuario: Usuario, datos) -> Socio:
    socio = obtener_socio_del_usuario(db, usuario)
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(socio, campo, valor)
    db.commit()
    db.refresh(socio)
    return socio