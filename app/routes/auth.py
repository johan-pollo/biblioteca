from typing import Annotated

from fastapi import APIRouter, Depends, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from app.controllers import auth as auth_controller
from app.core.dependencies import CurrentUser, SessionDep
from app.schemas.auth import CambioContrasena, RefreshSolicitud, TokenRespuesta
from app.schemas.usuario import UsuarioRegistro, UsuarioRespuesta
from app.core.limiter import limiter

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post(
    "/registro",
    response_model=UsuarioRespuesta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario socio",
    responses={409: {"description": "El email ya está registrado"}},
)
@limiter.limit("5/minute")
def registrar(request: Request, datos: UsuarioRegistro, db: SessionDep) -> UsuarioRespuesta:
    usuario = auth_controller.registrar_usuario(db, datos)
    return UsuarioRespuesta.model_validate(usuario)


@router.post(
    "/login",
    response_model=TokenRespuesta,
    summary="Iniciar sesión y obtener tokens",
    responses={401: {"description": "Credenciales inválidas"}, 423: {"description": "Cuenta bloqueada"}},
)
@limiter.limit("10/minute")
def login(
    request: Request,
    formulario: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: SessionDep,
) -> TokenRespuesta:
    return auth_controller.iniciar_sesion(
        db, formulario.username, formulario.password
    )


@router.post(
    "/refresh",
    response_model=TokenRespuesta,
    summary="Rotar los tokens de acceso y renovación",
    responses={401: {"description": "Refresh inválido, vencido o reutilizado"}},
)
def refresh(datos: RefreshSolicitud, db: SessionDep) -> TokenRespuesta:
    return auth_controller.refrescar_tokens(db, datos.refresh_token)


@router.post(
    "/logout",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cerrar sesión y revocar los refresh tokens",
    responses={401: {"description": "No autenticado"}},
)
def logout(db: SessionDep, usuario: CurrentUser) -> Response:
    auth_controller.cerrar_sesion(db, usuario)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/me",
    response_model=UsuarioRespuesta,
    summary="Consultar el usuario autenticado",
    responses={401: {"description": "No autenticado"}, 403: {"description": "Usuario inactivo"}},
)
def me(usuario: CurrentUser) -> UsuarioRespuesta:
    return UsuarioRespuesta.model_validate(usuario)


@router.patch(
    "/me/password",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cambiar contraseña y revocar refresh tokens",
    responses={401: {"description": "No autenticado"}},
)
def cambiar_contrasena(
    datos: CambioContrasena,
    db: SessionDep,
    usuario: CurrentUser,
) -> Response:
    auth_controller.cambiar_contrasena(db, usuario, datos)
    return Response(status_code=status.HTTP_204_NO_CONTENT)