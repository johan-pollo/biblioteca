from datetime import datetime, timedelta, timezone

import jwt
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.exceptions import (
    CuentaBloqueada,
    Conflicto,
    NoAutenticado,
    Prohibido,
)
from app.core.security import (
    crear_token,
    decodificar_token,
    hash_password,
    verify_password,
)
from app.models.refresh_token import RefreshToken
from app.models.socio import Socio
from app.models.usuario import RolUsuario, Usuario
from app.schemas.auth import CambioContrasena, TokenRespuesta
from app.schemas.usuario import UsuarioRegistro


def registrar_usuario(db: Session, datos: UsuarioRegistro) -> Usuario:
    email = str(datos.email).strip().lower()
    email_normalizado = func.lower(email)
    email_en_uso = db.scalar(
        select(Usuario.id).where(func.lower(Usuario.email) == email_normalizado)
    )
    socio_existente = db.scalar(
        select(Socio.id).where(func.lower(Socio.email) == email_normalizado)
    )
    if email_en_uso is not None or socio_existente is not None:
        raise Conflicto("El email ya está registrado")

    socio = Socio(
        nombre=datos.nombre,
        email=email,
        telefono=datos.telefono,
        activo=True,
    )
    usuario = Usuario(
        email=email,
        nombre=datos.nombre,
        password_hash=hash_password(datos.password),
        rol=RolUsuario.SOCIO,
        activo=True,
        socio=socio,
    )

    try:
        db.add_all([socio, usuario])
        db.commit()
    except IntegrityError as error:
        db.rollback()
        restriccion = getattr(getattr(error.orig, "diag", None), "constraint_name", None)
        detalle = str(error.orig)
        restricciones_email = {
            "uq_usuarios_email",
            "uq_usuarios_email_lower",
            "uq_socios_email",
            "uq_socios_email_lower",
        }
        if restriccion in restricciones_email or any(
            nombre in detalle for nombre in restricciones_email
        ):
            raise Conflicto("El email ya está registrado") from error
        raise

    db.refresh(usuario)
    return usuario


def _fecha_utc(fecha: datetime) -> datetime:
    if fecha.tzinfo is None:
        return fecha.replace(tzinfo=timezone.utc)
    return fecha.astimezone(timezone.utc)


def _crear_par_tokens(db: Session, usuario: Usuario) -> TokenRespuesta:
    settings = get_settings()
    access_token, _, _ = crear_token(
        usuario.id,
        usuario.rol.value,
        "access",
        timedelta(minutes=settings.access_token_expire_minutes),
    )
    refresh_token, jti, expira = crear_token(
        usuario.id,
        usuario.rol.value,
        "refresh",
        timedelta(days=settings.refresh_token_expire_days),
    )
    db.add(
        RefreshToken(
            jti=jti,
            usuario_id=usuario.id,
            expira_en=expira,
            revocado=False,
        )
    )
    return TokenRespuesta(
        access_token=access_token,
        refresh_token=refresh_token,
        expires_in=settings.access_token_expire_minutes * 60,
    )


def iniciar_sesion(db: Session, email: str, contrasena: str) -> TokenRespuesta:
    usuario = db.scalar(
        select(Usuario).where(func.lower(Usuario.email) == email.strip().lower())
    )
    if usuario is None:
        raise NoAutenticado("Credenciales inválidas")
    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    ahora = datetime.now(timezone.utc)
    if usuario.bloqueado_hasta is not None:
        if _fecha_utc(usuario.bloqueado_hasta) > ahora:
            raise CuentaBloqueada()
        usuario.bloqueado_hasta = None
        usuario.intentos_fallidos = 0

    if not verify_password(contrasena, usuario.password_hash):
        usuario.intentos_fallidos += 1
        if usuario.intentos_fallidos >= 5:
            usuario.bloqueado_hasta = ahora + timedelta(minutes=15)
            db.commit()
            raise CuentaBloqueada()
        db.commit()
        raise NoAutenticado("Credenciales inválidas")

    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    respuesta = _crear_par_tokens(db, usuario)
    db.commit()
    return respuesta


def refrescar_tokens(db: Session, token_refresh: str) -> TokenRespuesta:
    try:
        claims = decodificar_token(token_refresh)
    except jwt.InvalidTokenError as error:
        raise NoAutenticado() from error

    subject = claims.get("sub")
    jti = claims.get("jti")
    if (
        claims.get("type") != "refresh"
        or not isinstance(subject, str)
        or not subject.isdigit()
        or not isinstance(jti, str)
    ):
        raise NoAutenticado()

    refresh = db.scalar(
        select(RefreshToken)
        .where(RefreshToken.jti == jti)
        .with_for_update()
    )
    if refresh is None:
        raise NoAutenticado()

    usuario = db.get(Usuario, int(subject))
    if usuario is None or refresh.usuario_id != usuario.id:
        raise NoAutenticado()

    if refresh.revocado:
        db.query(RefreshToken).filter(
            RefreshToken.usuario_id == usuario.id,
            RefreshToken.revocado.is_(False),
        ).update({RefreshToken.revocado: True}, synchronize_session=False)
        db.commit()
        raise NoAutenticado()

    if _fecha_utc(refresh.expira_en) <= datetime.now(timezone.utc):
        raise NoAutenticado()
    if not usuario.activo:
        raise Prohibido("Usuario inactivo")

    refresh.revocado = True
    respuesta = _crear_par_tokens(db, usuario)
    db.commit()
    return respuesta


def cerrar_sesion(db: Session, usuario: Usuario) -> None:
    db.query(RefreshToken).filter(
        RefreshToken.usuario_id == usuario.id,
        RefreshToken.revocado.is_(False),
    ).update({RefreshToken.revocado: True}, synchronize_session=False)
    db.commit()


def cambiar_contrasena(
    db: Session, usuario: Usuario, datos: CambioContrasena
) -> None:
    if not verify_password(datos.contrasena_actual, usuario.password_hash):
        raise NoAutenticado("La contraseña actual es incorrecta")

    usuario.password_hash = hash_password(datos.contrasena_nueva)
    db.query(RefreshToken).filter(
        RefreshToken.usuario_id == usuario.id,
        RefreshToken.revocado.is_(False),
    ).update({RefreshToken.revocado: True}, synchronize_session=False)
    db.commit()