from fastapi import Query, Depends
from typing import Annotated
from fastapi.security import OAuth2PasswordBearer
from jwt import InvalidTokenError
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import NoAutenticado, Prohibido
from app.core.security import decodificar_token
from app.models.usuario import RolUsuario, Usuario

class Paginacion:
    def __init__(
        self,
        skip: int = Query(0, ge=0),
        limit: int = Query(10, ge=1, le=100)
    ):
        self.skip = skip
        self.limit = limit

SessionDep = Annotated[Session, Depends(get_db)]
PaginacionDep = Annotated[Paginacion, Depends()]

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")


def get_current_user(token: Annotated[str, Depends(oauth2_scheme)], db: SessionDep) -> Usuario:
    try:
        claims = decodificar_token(token)
    except InvalidTokenError as error:
        raise NoAutenticado() from error

    if claims.get("type") != "access":
        raise NoAutenticado()

    subject = claims.get("sub")
    if not isinstance(subject, str) or not subject.isdigit():
        raise NoAutenticado()

    usuario = db.scalar(select(Usuario).where(Usuario.id == int(subject)))
    if usuario is None:
        raise NoAutenticado()
    if not usuario.activo:
        raise Prohibido("Usuario inactivo")
    return usuario


CurrentUser = Annotated[Usuario, Depends(get_current_user)]


def requiere_rol(*roles: RolUsuario):
    def verificar_rol(usuario: CurrentUser) -> Usuario:
        if usuario.rol not in roles:
            raise Prohibido("No tiene permiso para esta operación")
        return usuario

    return verificar_rol


Staff = Annotated[
    Usuario,
    Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO)),
]