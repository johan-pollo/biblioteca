from datetime import date, timedelta

from app.models.prestamo import Prestamo
from app.models.usuario import RolUsuario


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_multa_impide_prestar_hasta_pago_y_pago_habilita_prestamo(
    cliente,
    catalogo,
    crear_usuario,
    crear_token_acceso,
    sesion_pruebas,
):
    staff = crear_usuario(
        RolUsuario.BIBLIOTECARIO, "staff@example.com", con_socio=False
    )
    socio = crear_usuario(RolUsuario.SOCIO, "ana@example.com")
    token_staff = _auth(crear_token_acceso(staff))
    fecha_prestamo = date.today() - timedelta(days=30)
    creado = cliente.post(
        "/api/v1/prestamos",
        json={
            "socio_id": socio.socio_id,
            "libro_id": catalogo["libro"].id,
            "fecha_prestamo": fecha_prestamo.isoformat(),
            "dias": 14,
        },
        headers=token_staff,
    )
    assert creado.status_code == 201
    prestamo_id = creado.json()["id"]

    devuelto = cliente.post(
        f"/api/v1/prestamos/{prestamo_id}/devolucion",
        json={"fecha_devolucion": (date.today() - timedelta(days=3)).isoformat()},
        headers=token_staff,
    )
    assert devuelto.status_code == 200
    assert devuelto.json()["multa"] == 6.5
    assert devuelto.json()["multa_pagada"] is False

    bloqueado = cliente.post(
        "/api/v1/prestamos",
        json={
            "socio_id": socio.socio_id,
            "libro_id": catalogo["libro"].id,
            "dias": 14,
        },
        headers=token_staff,
    )
    assert bloqueado.status_code == 422
    assert bloqueado.json()["detail"] == "El socio tiene multas pendientes"

    pagado = cliente.post(
        f"/api/v1/prestamos/{prestamo_id}/pago-multa",
        headers=token_staff,
    )
    assert pagado.status_code == 200
    assert pagado.json()["multa_pagada"] is True
    habilitado = cliente.post(
        "/api/v1/prestamos",
        json={
            "socio_id": socio.socio_id,
            "libro_id": catalogo["libro"].id,
            "dias": 14,
        },
        headers=token_staff,
    )
    assert habilitado.status_code == 201


def test_pago_multa_sin_multa_devuelve_conflicto(
    cliente, catalogo, crear_usuario, crear_token_acceso, sesion_pruebas
):
    staff = crear_usuario(
        RolUsuario.BIBLIOTECARIO, "staff@example.com", con_socio=False
    )
    socio = crear_usuario(RolUsuario.SOCIO)
    hoy = date.today()
    prestamo = Prestamo(
        libro_id=catalogo["libro"].id,
        socio_id=socio.socio_id,
        fecha_prestamo=hoy,
        fecha_limite=hoy + timedelta(days=14),
        multa=0,
    )
    sesion_pruebas.add(prestamo)
    sesion_pruebas.commit()

    respuesta = cliente.post(
        f"/api/v1/prestamos/{prestamo.id}/pago-multa",
        headers=_auth(crear_token_acceso(staff)),
    )
    assert respuesta.status_code == 409
