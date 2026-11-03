from typing import Optional
from fastapi import APIRouter, Depends, status
from app.core.dependencies import CurrentUser, SessionDep, PaginacionDep, requiere_rol
from app.models.usuario import RolUsuario
from app.schemas.prestamo import PrestamoCreate, DevolucionCreate, PrestamoResponse
from app.schemas.pagina import Pagina
from app.controllers import prestamo as prestamo_controller

router = APIRouter(prefix="/prestamos", tags=["Préstamos"])

@router.get("", response_model=Pagina[PrestamoResponse], summary="Listar préstamos", responses={401: {"description": "No autenticado"}, 403: {"description": "No autorizado"}})
def listar(
    usuario: CurrentUser,
    db: SessionDep,
    paginacion: PaginacionDep,
    estado: Optional[str] = None,
    socio_id: Optional[int] = None,
    libro_id: Optional[int] = None
):
    socio_id_forzado = (
        usuario.socio_id if usuario.socio_id is not None else -1
    ) if usuario.rol == RolUsuario.SOCIO else None
    return prestamo_controller.listar_prestamos(
        db,
        skip=paginacion.skip,
        limit=paginacion.limit,
        estado=estado,
        socio_id=(
            None if usuario.rol == RolUsuario.SOCIO else socio_id
        ),
        libro_id=libro_id,
        socio_id_forzado=socio_id_forzado,
    )

@router.get("/{prestamo_id}", response_model=PrestamoResponse, summary="Consultar un préstamo", responses={401: {"description": "No autenticado"}, 403: {"description": "No autorizado"}, 404: {"description": "Préstamo no encontrado"}})
def obtener(prestamo_id: int, usuario: CurrentUser, db: SessionDep):
    socio_id_forzado = (
        usuario.socio_id if usuario.socio_id is not None else -1
    ) if usuario.rol == RolUsuario.SOCIO else None
    return prestamo_controller.obtener_prestamo(
        db, prestamo_id, socio_id_forzado=socio_id_forzado
    )

@router.post("", response_model=PrestamoResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))], summary="Registrar un préstamo")
def crear(datos: PrestamoCreate, usuario: CurrentUser, db: SessionDep):
    return prestamo_controller.registrar_prestamo(db, datos, registrado_por_id=usuario.id)

@router.post("/{prestamo_id}/devolucion", response_model=PrestamoResponse, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))], summary="Registrar devolución")
def devolucion(prestamo_id: int, datos: DevolucionCreate, db: SessionDep):
    return prestamo_controller.registrar_devolucion(db, prestamo_id, datos)

@router.post("/{prestamo_id}/pago-multa", response_model=PrestamoResponse, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))], summary="Registrar pago de multa")
def pagar_multa(prestamo_id: int, db: SessionDep):
    return prestamo_controller.pagar_multa(db, prestamo_id)