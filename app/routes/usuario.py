from fastapi import APIRouter, Depends, status

from app.controllers import usuario as usuario_controller
from app.core.dependencies import CurrentUser, PaginacionDep, SessionDep, requiere_rol
from app.models.usuario import RolUsuario
from app.schemas.pagina import Pagina
from app.schemas.usuario import (
    UsuarioActivoActualizar,
    UsuarioCrear,
    UsuarioRespuesta,
    UsuarioRolActualizar,
)

router = APIRouter(
    prefix="/usuarios",
    tags=["Usuarios"],
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))],
)


@router.get("", response_model=Pagina[UsuarioRespuesta])
def listar(
    db: SessionDep,
    paginacion: PaginacionDep,
    rol: RolUsuario | None = None,
    activo: bool | None = None,
):
    return usuario_controller.listar_usuarios(
        db, paginacion.skip, paginacion.limit, rol, activo
    )


@router.post(
    "",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
)
def crear(datos: UsuarioCrear, db: SessionDep):
    return usuario_controller.crear_usuario(db, datos)


@router.patch("/{usuario_id}/rol", response_model=UsuarioRespuesta)
def actualizar_rol(
    usuario_id: int,
    datos: UsuarioRolActualizar,
    db: SessionDep,
    actor: CurrentUser,
):
    return usuario_controller.actualizar_rol(db, usuario_id, datos.rol, actor)


@router.patch("/{usuario_id}/activo", response_model=UsuarioRespuesta)
def actualizar_estado(
    usuario_id: int,
    datos: UsuarioActivoActualizar,
    db: SessionDep,
    actor: CurrentUser,
):
    return usuario_controller.actualizar_estado(db, usuario_id, datos.activo, actor)