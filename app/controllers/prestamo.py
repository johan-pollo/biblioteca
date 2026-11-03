from datetime import date, timedelta
from typing import Optional
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload
from app.models.prestamo import Prestamo
from app.models.socio import Socio
from app.models.libro import Libro
from app.schemas.prestamo import PrestamoCreate, DevolucionCreate
from app.controllers.libro import calcular_disponibles, _formatear_libro_response
from app.core.exceptions import NoEncontrado, Conflicto, ReglaNegocio
from app.controllers.paginacion import paginar

def calcular_estado(p: Prestamo) -> str:
    if p.fecha_devolucion is not None:
        return "devuelto"
    if p.fecha_limite < date.today():
        return "vencido"
    return "activo"

def _formatear_prestamo_response(db: Session, p: Prestamo) -> dict:
    libro_data = None
    if p.libro:
        libro_data = _formatear_libro_response(db, p.libro)

    return {
        "id": p.id,
        "libro_id": p.libro_id,
        "socio_id": p.socio_id,
        "registrado_por_id": p.registrado_por_id,
        "fecha_prestamo": p.fecha_prestamo,
        "fecha_limite": p.fecha_limite,
        "fecha_devolucion": p.fecha_devolucion,
        "multa": float(p.multa),
        "multa_pagada": p.multa_pagada,
        "estado": calcular_estado(p),
        "libro": libro_data,
        "socio": p.socio
    }

def listar_prestamos(
    db: Session,
    skip: int,
    limit: int,
    estado: Optional[str] = None,
    socio_id: Optional[int] = None,
    libro_id: Optional[int] = None,
    socio_id_forzado: Optional[int] = None,
):
    stmt = select(Prestamo).options(
        selectinload(Prestamo.libro).selectinload(Libro.autor),
        selectinload(Prestamo.libro).selectinload(Libro.categorias),
        selectinload(Prestamo.socio)
    )

    hoy = date.today()
    if estado == "activo":
        stmt = stmt.where(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite >= hoy)
    elif estado == "vencido":
        stmt = stmt.where(Prestamo.fecha_devolucion.is_(None), Prestamo.fecha_limite < hoy)
    elif estado == "devuelto":
        stmt = stmt.where(Prestamo.fecha_devolucion.is_not(None))

    if socio_id:
        stmt = stmt.where(Prestamo.socio_id == socio_id)
    if socio_id_forzado is not None:
        stmt = stmt.where(Prestamo.socio_id == socio_id_forzado)
    if libro_id:
        stmt = stmt.where(Prestamo.libro_id == libro_id)

    pagina = paginar(db, stmt, skip, limit)
    pagina["items"] = [
        _formatear_prestamo_response(db, prestamo) for prestamo in pagina["items"]
    ]
    return pagina

def obtener_prestamo(
    db: Session, prestamo_id: int, socio_id_forzado: int | None = None
):
    stmt = select(Prestamo).options(
        selectinload(Prestamo.libro).selectinload(Libro.autor),
        selectinload(Prestamo.libro).selectinload(Libro.categorias),
        selectinload(Prestamo.socio)
    ).where(Prestamo.id == prestamo_id)
    if socio_id_forzado is not None:
        stmt = stmt.where(Prestamo.socio_id == socio_id_forzado)

    p = db.scalar(stmt)
    if not p:
        raise NoEncontrado("Préstamo no encontrado")
    return _formatear_prestamo_response(db, p)

def registrar_prestamo(
    db: Session, datos: PrestamoCreate, registrado_por_id: int
):
    # R1: El socio existe
    socio = db.get(Socio, datos.socio_id)
    if not socio:
        raise NoEncontrado("Socio no encontrado")

    # R2: El libro existe
    libro = db.get(Libro, datos.libro_id)
    if not libro:
        raise NoEncontrado("Libro no encontrado")

    # R3: El socio está activo
    if not socio.activo:
        raise ReglaNegocio("El socio no está activo")

    multas_pendientes = db.query(Prestamo).filter(
        Prestamo.socio_id == socio.id,
        Prestamo.multa > 0,
        Prestamo.multa_pagada.is_(False)
    ).count()
    if multas_pendientes > 0:
        raise ReglaNegocio("El socio tiene multas pendientes")

    # R4: El socio no tiene préstamos vencidos
    hoy = date.today()
    vencidos = db.query(Prestamo).filter(
        Prestamo.socio_id == socio.id,
        Prestamo.fecha_devolucion.is_(None),
        Prestamo.fecha_limite < hoy
    ).count()
    if vencidos > 0:
        raise ReglaNegocio("El socio tiene préstamos vencidos")

    # R5: El socio tiene menos de 3 préstamos sin devolver
    activos = db.query(Prestamo).filter(
        Prestamo.socio_id == socio.id,
        Prestamo.fecha_devolucion.is_(None)
    ).count()
    if activos >= 3:
        raise ReglaNegocio("Máximo de 3 préstamos")

    # R6: El socio no tiene ya ese mismo libro sin devolver
    mismo = db.query(Prestamo).filter(
        Prestamo.socio_id == socio.id,
        Prestamo.libro_id == libro.id,
        Prestamo.fecha_devolucion.is_(None)
    ).first()
    if mismo:
        raise Conflicto("El socio ya tiene este libro en préstamo")

    # R7: El libro tiene ejemplares disponibles
    disponibles = calcular_disponibles(db, libro.id, libro.ejemplares)
    if disponibles <= 0:
        raise ReglaNegocio("No hay ejemplares disponibles")

    # R8: fecha_limite = fecha_prestamo + dias
    fecha_p = datos.fecha_prestamo or date.today()
    fecha_l = fecha_p + timedelta(days=datos.dias)

    prestamo = Prestamo(
        socio_id=socio.id,
        libro_id=libro.id,
        registrado_por_id=registrado_por_id,
        fecha_prestamo=fecha_p,
        fecha_limite=fecha_l,
        multa=0.00
    )
    db.add(prestamo)
    db.commit()
    db.refresh(prestamo)
    return obtener_prestamo(db, prestamo.id)

def registrar_devolucion(db: Session, prestamo_id: int, datos: DevolucionCreate):
    p = db.get(Prestamo, prestamo_id)
    if not p:
        raise NoEncontrado("Préstamo no encontrado")

    # R9: Al devolver: el préstamo existe, no fue devuelto antes y la fecha no es anterior al préstamo
    if p.fecha_devolucion is not None:
        raise Conflicto("El préstamo ya fue devuelto")

    fecha_dev = datos.fecha_devolucion or date.today()
    if fecha_dev < p.fecha_prestamo:
        raise ReglaNegocio("La fecha de devolución no puede ser anterior a la fecha de préstamo")

    p.fecha_devolucion = fecha_dev

    # R10: Si se devuelve tarde: multa = días de retraso * 0.50
    if fecha_dev > p.fecha_limite:
        retraso = (fecha_dev - p.fecha_limite).days
        p.multa = round(retraso * 0.50, 2)

    db.commit()
    db.refresh(p)
    return obtener_prestamo(db, p.id)


def pagar_multa(db: Session, prestamo_id: int):
    prestamo = db.get(Prestamo, prestamo_id)
    if not prestamo:
        raise NoEncontrado("Préstamo no encontrado")
    if prestamo.multa <= 0 or prestamo.multa_pagada:
        raise Conflicto("El préstamo no tiene una multa pendiente")

    prestamo.multa_pagada = True
    db.commit()
    db.refresh(prestamo)
    return obtener_prestamo(db, prestamo.id)


def listar_multas_pendientes(
    db: Session, socio_id: int, skip: int = 0, limit: int = 10
) -> dict:
    consulta = (
        select(Prestamo)
        .options(
            selectinload(Prestamo.libro).selectinload(Libro.autor),
            selectinload(Prestamo.libro).selectinload(Libro.categorias),
            selectinload(Prestamo.socio),
        )
        .where(
            Prestamo.socio_id == socio_id,
            Prestamo.multa > 0,
            Prestamo.multa_pagada.is_(False),
        )
    )
    total_adeudado = db.scalar(
        select(func.coalesce(func.sum(Prestamo.multa), 0)).where(
            Prestamo.socio_id == socio_id,
            Prestamo.multa > 0,
            Prestamo.multa_pagada.is_(False),
        )
    ) or 0
    pagina = paginar(db, consulta, skip, limit)
    pagina["items"] = [
        _formatear_prestamo_response(db, prestamo) for prestamo in pagina["items"]
    ]
    pagina["total_adeudado"] = round(float(total_adeudado), 2)
    return pagina