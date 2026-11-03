from typing import Optional
from fastapi import APIRouter, Depends, status
from app.core.dependencies import CurrentUser, SessionDep, PaginacionDep, requiere_rol
from app.core.exceptions import Prohibido
from app.models.usuario import RolUsuario
from app.schemas.socio import (
    SocioActualizarPropio,
    SocioCreate,
    SocioUpdate,
    SocioResponse,
)
from app.schemas.prestamo import MultasPendientesRespuesta, PrestamoResponse
from app.schemas.pagina import Pagina
from app.controllers import socio as socio_controller
from app.controllers import prestamo as prestamo_controller

router = APIRouter(prefix="/socios", tags=["Socios"])

@router.get("/me", response_model=SocioResponse)
def obtener_propio(usuario: CurrentUser, db: SessionDep):
    if usuario.rol != RolUsuario.SOCIO:
        raise Prohibido("Esta ruta es exclusiva para socios")
    return socio_controller.obtener_socio_del_usuario(db, usuario)


@router.patch("/me", response_model=SocioResponse)
def actualizar_propio(
    datos: SocioActualizarPropio, usuario: CurrentUser, db: SessionDep
):
    if usuario.rol != RolUsuario.SOCIO:
        raise Prohibido("Esta ruta es exclusiva para socios")
    return socio_controller.actualizar_socio_propio(db, usuario, datos)


@router.get("/me/prestamos", response_model=Pagina[PrestamoResponse])
def prestamos_propios(
    usuario: CurrentUser,
    db: SessionDep,
    paginacion: PaginacionDep,
    estado: Optional[str] = None,
):
    if usuario.rol != RolUsuario.SOCIO:
        raise Prohibido("Esta ruta es exclusiva para socios")
    socio = socio_controller.obtener_socio_del_usuario(db, usuario)
    return socio_controller.obtener_prestamos_socio(
        db, socio.id, estado=estado, skip=paginacion.skip, limit=paginacion.limit
    )


@router.get("/me/multas", response_model=MultasPendientesRespuesta)
def multas_propias(usuario: CurrentUser, db: SessionDep, paginacion: PaginacionDep):
    if usuario.rol != RolUsuario.SOCIO:
        raise Prohibido("Esta ruta es exclusiva para socios")
    socio = socio_controller.obtener_socio_del_usuario(db, usuario)
    return prestamo_controller.listar_multas_pendientes(
        db, socio.id, paginacion.skip, paginacion.limit
    )


@router.get("", response_model=Pagina[SocioResponse], dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def listar(db: SessionDep, paginacion: PaginacionDep, activo: Optional[bool] = None):
    return socio_controller.listar_socios(db, skip=paginacion.skip, limit=paginacion.limit, activo=activo)

@router.get("/{socio_id}", response_model=SocioResponse, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def obtener(socio_id: int, db: SessionDep):
    return socio_controller.obtener_socio(db, socio_id)

@router.post("", response_model=SocioResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def crear(datos: SocioCreate, db: SessionDep):
    return socio_controller.crear_socio(db, datos)

@router.patch("/{socio_id}", response_model=SocioResponse, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def actualizar(socio_id: int, datos: SocioUpdate, db: SessionDep):
    return socio_controller.actualizar_socio(db, socio_id, datos)

@router.delete("/{socio_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))])
def eliminar(socio_id: int, db: SessionDep):
    socio_controller.eliminar_socio(db, socio_id)

@router.get("/{socio_id}/prestamos", response_model=Pagina[PrestamoResponse], dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def prestamos_socio(
    socio_id: int,
    db: SessionDep,
    paginacion: PaginacionDep,
    estado: Optional[str] = None,
):
    return socio_controller.obtener_prestamos_socio(
        db, socio_id, estado=estado, skip=paginacion.skip, limit=paginacion.limit
    )