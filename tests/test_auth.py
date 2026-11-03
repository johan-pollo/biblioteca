from datetime import datetime, timezone

import jwt
from fastapi import APIRouter

from app.core.config import get_settings
from app.main import app
from app.models.usuario import RolUsuario


def _datos_registro(email: str = "ana@example.com") -> dict:
    return {
        "email": email,
        "nombre": "ana ejemplo",
        "telefono": "3001234567",
        "password": "ClaveSegura123",
        "confirmar_password": "ClaveSegura123",
    }


def _iniciar_sesion(cliente, email: str, password: str = "ClaveSegura123"):
    return cliente.post(
        "/api/v1/auth/login",
        data={"username": email, "password": password},
    )


def test_registro_rechaza_clave_debil_y_confirmacion_distinta(cliente):
    debil = _datos_registro()
    debil["password"] = "solamenteletras"
    debil["confirmar_password"] = "solamenteletras"
    assert cliente.post("/api/v1/auth/registro", json=debil).status_code == 422

    distinta = _datos_registro()
    distinta["confirmar_password"] = "OtraClave123"
    assert cliente.post("/api/v1/auth/registro", json=distinta).status_code == 422


def test_registro_no_expone_hash_y_email_duplicado_no_distingue_mayusculas(cliente):
    respuesta = cliente.post(
        "/api/v1/auth/registro", json=_datos_registro("ana@example.com")
    )
    assert respuesta.status_code == 201
    assert "password_hash" not in respuesta.json()
    assert "password" not in respuesta.json()

    duplicado = cliente.post(
        "/api/v1/auth/registro", json=_datos_registro("ANA@EXAMPLE.COM")
    )
    assert duplicado.status_code == 409


def test_login_usa_el_mismo_mensaje_para_email_inexistente_y_clave_incorrecta(
    cliente, crear_usuario
):
    crear_usuario(RolUsuario.SOCIO)
    desconocido = _iniciar_sesion(cliente, "nadie@example.com")
    clave_mala = _iniciar_sesion(cliente, "socio@example.com", "Incorrecta123")
    assert desconocido.status_code == clave_mala.status_code == 401
    assert desconocido.json()["detail"] == clave_mala.json()["detail"]
    assert desconocido.json()["detail"] == "Credenciales inválidas"


def test_login_correcto_entrega_tokens_y_me_requiere_bearer(
    cliente, crear_usuario
):
    crear_usuario(RolUsuario.SOCIO)
    login = _iniciar_sesion(cliente, "socio@example.com")
    assert login.status_code == 200
    assert login.json()["token_type"] == "bearer"
    assert login.json()["access_token"]
    assert login.json()["refresh_token"]

    sin_token = cliente.get("/api/v1/auth/me")
    assert sin_token.status_code == 401
    assert sin_token.headers["www-authenticate"] == "Bearer"

    me = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {login.json()['access_token']}"},
    )
    assert me.status_code == 200
    assert "password_hash" not in me.json()


def test_token_alterado_y_refresh_usado_como_bearer_son_rechazados(
    cliente, crear_usuario
):
    crear_usuario(RolUsuario.SOCIO)
    par = _iniciar_sesion(cliente, "socio@example.com").json()
    token_alterado = par["access_token"][:-1] + (
        "a" if par["access_token"][-1] != "a" else "b"
    )
    alterado = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token_alterado}"},
    )
    refresh_como_access = cliente.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {par['refresh_token']}"},
    )
    assert alterado.status_code == 401
    assert alterado.headers["www-authenticate"] == "Bearer"
    assert refresh_como_access.status_code == 401


def test_refresh_rota_token_y_reutilizarlo_revoca_la_familia(
    cliente, crear_usuario
):
    crear_usuario(RolUsuario.SOCIO)
    original = _iniciar_sesion(cliente, "socio@example.com").json()["refresh_token"]
    rotado = cliente.post(
        "/api/v1/auth/refresh", json={"refresh_token": original}
    )
    assert rotado.status_code == 200

    reutilizado = cliente.post(
        "/api/v1/auth/refresh", json={"refresh_token": original}
    )
    token_familiar = cliente.post(
        "/api/v1/auth/refresh",
        json={"refresh_token": rotado.json()["refresh_token"]},
    )
    assert reutilizado.status_code == 401
    assert token_familiar.status_code == 401


def test_logout_invalida_refresh(cliente, crear_usuario):
    crear_usuario(RolUsuario.SOCIO)
    par = _iniciar_sesion(cliente, "socio@example.com").json()
    cerrar = cliente.post(
        "/api/v1/auth/logout",
        headers={"Authorization": f"Bearer {par['access_token']}"},
    )
    refresh = cliente.post(
        "/api/v1/auth/refresh", json={"refresh_token": par["refresh_token"]}
    )
    assert cerrar.status_code == 204
    assert refresh.status_code == 401


def test_cinco_fallos_bloquean_la_cuenta(cliente, crear_usuario):
    crear_usuario(RolUsuario.SOCIO)
    respuestas = [
        _iniciar_sesion(cliente, "socio@example.com", "Incorrecta123")
        for _ in range(5)
    ]
    assert [respuesta.status_code for respuesta in respuestas] == [
        401,
        401,
        401,
        401,
        423,
    ]
    assert respuestas[-1].json()["detail"] == "Cuenta bloqueada temporalmente"


def test_usuario_inactivo_no_puede_usar_token_vigente(
    cliente, crear_usuario, crear_token_acceso, encabezados_autorizacion
):
    usuario = crear_usuario(RolUsuario.SOCIO, activo=False)
    respuesta = cliente.get(
        "/api/v1/auth/me",
        headers=encabezados_autorizacion(crear_token_acceso(usuario)),
    )
    assert respuesta.status_code == 403
    assert respuesta.json()["detail"] == "Usuario inactivo"


def test_login_limita_a_diez_solicitudes_por_minuto(cliente, crear_usuario):
    crear_usuario(RolUsuario.SOCIO)
    respuestas = [
        _iniciar_sesion(cliente, "socio@example.com", "Incorrecta123")
        for _ in range(11)
    ]
    assert respuestas[-1].status_code == 429


def test_registro_limita_a_cinco_solicitudes_por_minuto(cliente):
    respuestas = [
        cliente.post(
            "/api/v1/auth/registro",
            json=_datos_registro(f"persona{numero}@example.com"),
        )
        for numero in range(6)
    ]
    assert [respuesta.status_code for respuesta in respuestas] == [
        201,
        201,
        201,
        201,
        201,
        429,
    ]


def test_health_y_cabecera_request_id(cliente):
    respuesta = cliente.get("/api/v1/health")
    assert respuesta.status_code == 200
    assert respuesta.json() == {"status": "ok", "database": "ok"}
    assert len(respuesta.headers["x-request-id"]) == 36


def test_respuesta_interna_es_generica_y_no_filtra_excepcion(cliente):
    router = APIRouter()

    @router.get("/_prueba-error-interno")
    def provocar_error():
        raise RuntimeError("dato secreto que no debe filtrarse")

    cantidad_rutas = len(app.routes)
    app.include_router(router)
    try:
        respuesta = cliente.get("/_prueba-error-interno")
        assert respuesta.status_code == 500
        assert respuesta.json() == {"detail": "Error interno del servidor"}
        assert "secreto" not in respuesta.text
        assert respuesta.headers.get("x-request-id")
    finally:
        del app.router.routes[cantidad_rutas:]
        app.openapi_schema = None


def test_algoritmo_configurado_acepta_el_token_de_login(cliente, crear_usuario):
    crear_usuario(RolUsuario.SOCIO)
    access = _iniciar_sesion(cliente, "socio@example.com").json()["access_token"]
    claims = jwt.decode(
        access,
        get_settings().secret_key,
        algorithms=[get_settings().algorithm],
    )
    assert claims["type"] == "access"
    assert claims["exp"] > datetime.now(timezone.utc).timestamp()
