from datetime import date, timedelta

from app.models.prestamo import Prestamo
from app.models.usuario import RolUsuario


def _auth(token: str) -> dict[str, str]:
    return {"Authorization": f"Bearer {token}"}


def test_listado_publico_libros_devuelve_paginacion(cliente, catalogo):
    respuesta = cliente.get("/api/v1/libros?skip=0&limit=5")
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1
    assert len(respuesta.json()["items"]) == 1
    assert respuesta.json()["skip"] == 0
    assert respuesta.json()["limit"] == 5


def test_crear_libro_prohibe_socio_y_permite_bibliotecario(
    cliente, crear_usuario, crear_token_acceso, catalogo
):
    socio = crear_usuario(RolUsuario.SOCIO)
    bibliotecario = crear_usuario(
        RolUsuario.BIBLIOTECARIO, "bibliotecario@example.com", con_socio=False
    )
    datos = {
        "titulo": "El amor en los tiempos del colera",
        "isbn": "9780307389732",
        "anio_publicacion": 1985,
        "ejemplares": 2,
        "autor_id": catalogo["autor"].id,
        "categoria_ids": [catalogo["categoria"].id],
    }
    prohibido = cliente.post(
        "/api/v1/libros",
        json=datos,
        headers=_auth(crear_token_acceso(socio)),
    )
    creado = cliente.post(
        "/api/v1/libros",
        json=datos,
        headers=_auth(crear_token_acceso(bibliotecario)),
    )
    assert prohibido.status_code == 403
    assert creado.status_code == 201


def test_bibliotecario_no_puede_eliminar_libro(
    cliente, crear_usuario, crear_token_acceso, catalogo
):
    bibliotecario = crear_usuario(
        RolUsuario.BIBLIOTECARIO, "biblio@example.com", con_socio=False
    )
    respuesta = cliente.delete(
        f"/api/v1/libros/{catalogo['libro'].id}",
        headers=_auth(crear_token_acceso(bibliotecario)),
    )
    assert respuesta.status_code == 403


def test_listado_filtra_socio_y_no_permite_consultar_prestamo_ajeno(
    cliente,
    sesion_pruebas,
    catalogo,
    crear_usuario,
    crear_token_acceso,
):
    socio_ana = crear_usuario(RolUsuario.SOCIO, "ana@example.com")
    socio_luis = crear_usuario(RolUsuario.SOCIO, "luis@example.com")
    bibliotecario = crear_usuario(
        RolUsuario.BIBLIOTECARIO, "staff@example.com", con_socio=False
    )
    fecha = date.today()
    prestamo_ana = Prestamo(
        libro_id=catalogo["libro"].id,
        socio_id=socio_ana.socio_id,
        registrado_por_id=bibliotecario.id,
        fecha_prestamo=fecha,
        fecha_limite=fecha + timedelta(days=14),
        multa=0,
    )
    prestamo_luis = Prestamo(
        libro_id=catalogo["libro"].id,
        socio_id=socio_luis.socio_id,
        registrado_por_id=bibliotecario.id,
        fecha_prestamo=fecha,
        fecha_limite=fecha + timedelta(days=14),
        multa=0,
    )
    sesion_pruebas.add_all([prestamo_ana, prestamo_luis])
    sesion_pruebas.commit()
    sesion_pruebas.refresh(prestamo_ana)
    sesion_pruebas.refresh(prestamo_luis)
    token_ana = crear_token_acceso(socio_ana)

    listado = cliente.get(
        f"/api/v1/prestamos?socio_id={socio_luis.socio_id}",
        headers=_auth(token_ana),
    )
    ajeno = cliente.get(
        f"/api/v1/prestamos/{prestamo_luis.id}",
        headers=_auth(token_ana),
    )
    assert listado.status_code == 200
    assert [item["socio_id"] for item in listado.json()["items"]] == [
        socio_ana.socio_id
    ]
    assert ajeno.status_code == 404


def test_prestamo_guarda_el_usuario_que_lo_registro(
    cliente, catalogo, crear_usuario, crear_token_acceso, sesion_pruebas
):
    staff = crear_usuario(
        RolUsuario.BIBLIOTECARIO, "biblio@example.com", con_socio=False
    )
    socio = crear_usuario(RolUsuario.SOCIO, "socio@example.com")
    respuesta = cliente.post(
        "/api/v1/prestamos",
        json={
            "socio_id": socio.socio_id,
            "libro_id": catalogo["libro"].id,
            "dias": 14,
        },
        headers=_auth(crear_token_acceso(staff)),
    )
    assert respuesta.status_code == 201
    assert respuesta.json()["registrado_por_id"] == staff.id
    prestamo = sesion_pruebas.get(Prestamo, respuesta.json()["id"])
    assert prestamo.registrado_por_id == staff.id


def test_patch_socio_propio_no_admite_campos_extra(
    cliente, crear_usuario, crear_token_acceso
):
    socio = crear_usuario(RolUsuario.SOCIO)
    respuesta = cliente.patch(
        "/api/v1/socios/me",
        json={"activo": False},
        headers=_auth(crear_token_acceso(socio)),
    )
    assert respuesta.status_code == 422


def test_reportes_son_staff(cliente, crear_usuario, crear_token_acceso):
    socio = crear_usuario(RolUsuario.SOCIO)
    bibliotecario = crear_usuario(
        RolUsuario.BIBLIOTECARIO, "biblio@example.com", con_socio=False
    )
    url = "/api/v1/reportes/resumen"
    prohibido = cliente.get(url, headers=_auth(crear_token_acceso(socio)))
    permitido = cliente.get(
        url, headers=_auth(crear_token_acceso(bibliotecario))
    )
    assert prohibido.status_code == 403
    assert permitido.status_code == 200


def test_admin_no_puede_quitarse_el_rol(
    cliente, crear_usuario, crear_token_acceso
):
    admin = crear_usuario(RolUsuario.ADMIN, con_socio=False)
    respuesta = cliente.patch(
        f"/api/v1/usuarios/{admin.id}/rol",
        json={"rol": "bibliotecario"},
        headers=_auth(crear_token_acceso(admin)),
    )
    assert respuesta.status_code == 422


def test_socio_no_puede_acceder_a_recursos_de_usuarios(cliente, crear_usuario, crear_token_acceso):
    socio = crear_usuario(RolUsuario.SOCIO)
    token = _auth(crear_token_acceso(socio))
    assert cliente.get("/api/v1/usuarios", headers=token).status_code == 403
    assert cliente.get("/api/v1/socios", headers=token).status_code == 403


def test_socio_me_es_propietario_y_devuelve_sus_prestamos(
    cliente,
    catalogo,
    crear_usuario,
    crear_token_acceso,
    sesion_pruebas,
):
    socio = crear_usuario(RolUsuario.SOCIO)
    fecha = date.today()
    sesion_pruebas.add(
        Prestamo(
            libro_id=catalogo["libro"].id,
            socio_id=socio.socio_id,
            fecha_prestamo=fecha,
            fecha_limite=fecha + timedelta(days=14),
            multa=0,
        )
    )
    sesion_pruebas.commit()
    token = _auth(crear_token_acceso(socio))
    assert cliente.get("/api/v1/socios/me", headers=token).status_code == 200
    prestamos = cliente.get("/api/v1/socios/me/prestamos", headers=token)
    assert prestamos.status_code == 200
    assert prestamos.json()["total"] == 1


def test_socio_puede_ver_multa_pendiente_y_deuda_total(
    cliente,
    catalogo,
    crear_usuario,
    crear_token_acceso,
    sesion_pruebas,
):
    socio = crear_usuario(RolUsuario.SOCIO)
    fecha = date.today()
    sesion_pruebas.add(
        Prestamo(
            libro_id=catalogo["libro"].id,
            socio_id=socio.socio_id,
            fecha_prestamo=fecha - timedelta(days=20),
            fecha_limite=fecha - timedelta(days=6),
            fecha_devolucion=fecha,
            multa=3.0,
            multa_pagada=False,
        )
    )
    sesion_pruebas.commit()
    respuesta = cliente.get(
        "/api/v1/socios/me/multas",
        headers=_auth(crear_token_acceso(socio)),
    )
    assert respuesta.status_code == 200
    assert respuesta.json()["total"] == 1
    assert respuesta.json()["total_adeudado"] == 3.0
