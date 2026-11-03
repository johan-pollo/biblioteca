from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.exceptions import Conflicto, NoEncontrado, Prohibido, ReglaNegocio
from app.core.security import hash_password
from app.models.refresh_token import RefreshToken
from app.models.socio import Socio
from app.models.usuario import RolUsuario, Usuario
from app.schemas.usuario import UsuarioCrear


def listar_usuarios(
    db: Session,
    skip: int,
    limit: int,
    rol: RolUsuario | None = None,
    activo: bool | None = None,
) -> dict:
    consulta = select(Usuario)
    if rol is not None:
        consulta = consulta.where(Usuario.rol == rol)
    if activo is not None:
        consulta = consulta.where(Usuario.activo.is_(activo))

    total = db.scalar(
        select(func.count()).select_from(consulta.order_by(None).subquery())
    ) or 0
    usuarios = db.scalars(
        consulta.order_by(Usuario.id).offset(skip).limit(limit)
    ).all()
    return {"items": usuarios, "total": total, "skip": skip, "limit": limit}


def crear_usuario(db: Session, datos: UsuarioCrear) -> Usuario:
    if datos.rol not in {RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO}:
        raise Prohibido("Solo se pueden crear administradores o bibliotecarios")
    email = str(datos.email).strip().lower()
    existente = db.scalar(
        select(Usuario.id).where(func.lower(Usuario.email) == email)
    )
    socio_existente = db.scalar(
        select(Socio.id).where(func.lower(Socio.email) == email)
    )
    if existente is not None or socio_existente is not None:
        raise Conflicto("El email ya está registrado")

    usuario = Usuario(
        email=email,
        nombre=datos.nombre,
        password_hash=hash_password(datos.password),
        rol=datos.rol,
        activo=True,
    )
    try:
        db.add(usuario)
        db.commit()
    except IntegrityError as error:
        db.rollback()
        raise Conflicto("El email ya está registrado") from error
    db.refresh(usuario)
    return usuario


def _obtener_usuario(db: Session, usuario_id: int) -> Usuario:
    usuario = db.get(Usuario, usuario_id)
    if usuario is None:
        raise NoEncontrado("Usuario no encontrado")
    return usuario


def _validar_admin_activo(db: Session, objetivo: Usuario, rol_nuevo, activo_nuevo: bool):
    sigue_admin_activo = rol_nuevo == RolUsuario.ADMIN and activo_nuevo
    if sigue_admin_activo:
        return

    administradores_activos = db.scalar(
            select(func.count())
            .select_from(Usuario)
            .where(
                Usuario.rol == RolUsuario.ADMIN,
                Usuario.activo.is_(True),
            )
        ) or 0
    if (
        objetivo.rol == RolUsuario.ADMIN
        and objetivo.activo
        and administradores_activos <= 1
    ):
        raise ReglaNegocio("Debe existir al menos un administrador activo")


def _revocar_refresh_tokens(db: Session, usuario_id: int) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.usuario_id == usuario_id,
        RefreshToken.revocado.is_(False),
    ).update({RefreshToken.revocado: True}, synchronize_session=False)


def actualizar_rol(
    db: Session, usuario_id: int, rol_nuevo: RolUsuario, actor: Usuario
) -> Usuario:
    objetivo = _obtener_usuario(db, usuario_id)
    if actor.id == objetivo.id and objetivo.rol == RolUsuario.ADMIN and rol_nuevo != RolUsuario.ADMIN:
        raise ReglaNegocio("Un administrador no puede quitarse su propio rol")

    _validar_admin_activo(db, objetivo, rol_nuevo, objetivo.activo)
    objetivo.rol = rol_nuevo
    _revocar_refresh_tokens(db, objetivo.id)
    db.commit()
    db.refresh(objetivo)
    return objetivo


def actualizar_estado(
    db: Session, usuario_id: int, activo_nuevo: bool, actor: Usuario
) -> Usuario:
    objetivo = _obtener_usuario(db, usuario_id)
    if actor.id == objetivo.id and objetivo.rol == RolUsuario.ADMIN and not activo_nuevo:
        raise ReglaNegocio("Un administrador no puede desactivarse")

    _validar_admin_activo(db, objetivo, objetivo.rol, activo_nuevo)
    objetivo.activo = activo_nuevo
    if not activo_nuevo:
        _revocar_refresh_tokens(db, objetivo.id)
    db.commit()
    db.refresh(objetivo)
    return objetivo