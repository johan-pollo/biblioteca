from datetime import datetime, timedelta, timezone
from uuid import uuid4

import jwt
from pwdlib import PasswordHash

from app.core.config import get_settings

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def crear_token(
    usuario_id: int,
    rol: str,
    tipo: str,
    duracion: timedelta,
) -> tuple[str, str, datetime]:
    ahora = datetime.now(timezone.utc)
    expira = ahora + duracion
    jti = str(uuid4())
    claims = {
        "sub": str(usuario_id),
        "rol": rol,
        "type": tipo,
        "iat": ahora,
        "exp": expira,
        "jti": jti,
    }
    token = jwt.encode(
        claims,
        get_settings().secret_key,
        algorithm=get_settings().algorithm,
    )
    return token, jti, expira


def decodificar_token(token: str) -> dict:
    return jwt.decode(
        token,
        get_settings().secret_key,
        algorithms=[get_settings().algorithm],
    )