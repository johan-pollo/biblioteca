from datetime import timedelta
from collections.abc import Callable, Generator
from pathlib import Path
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from alembic import command
from alembic.config import Config
from sqlalchemy import create_engine, delete
from sqlalchemy.engine import make_url
from sqlalchemy.orm import Session, sessionmaker

from app import models
from app.core.config import get_settings
from app.core.database import Base, get_db
from app.core.limiter import limiter
from app.core.security import crear_token, hash_password
from app.main import app
from app.models.autor import Autor
from app.models.categoria import Categoria
from app.models.libro import Libro
from app.models.socio import Socio
from app.models.usuario import RolUsuario, Usuario


@pytest.fixture(scope="session")
def motor_pruebas():
    settings = get_settings()
    url = settings.test_database_url
    if not url:
        pytest.fail(
            "Define TEST_DATABASE_URL con una base de datos exclusiva para pruebas."
        )

    url_sqlalchemy = make_url(url)
    url_principal = make_url(settings.database_url)
    if url_sqlalchemy == url_principal:
        pytest.fail("TEST_DATABASE_URL no puede apuntar a DATABASE_URL.")
    if (
        url_sqlalchemy.get_backend_name() != "sqlite"
        and url_sqlalchemy.host == url_principal.host
        and url_sqlalchemy.database == url_principal.database
    ):
        pytest.fail("TEST_DATABASE_URL debe usar una base distinta a DATABASE_URL.")
    if (
        url_sqlalchemy.get_backend_name() == "sqlite"
        and url_sqlalchemy.database in (None, "", ":memory:")
    ):
        pytest.fail(
            "Para SQLite, TEST_DATABASE_URL debe usar un archivo y no una base en memoria."
        )
    argumentos = {}
    if url_sqlalchemy.get_backend_name() == "sqlite":
        argumentos["check_same_thread"] = False

    motor = create_engine(url, connect_args=argumentos)
    configuracion = Config(str(Path(__file__).resolve().parents[1] / "alembic.ini"))
    settings_pruebas = settings.model_copy(update={"database_url": url})
    try:
        with patch("app.core.config.get_settings", return_value=settings_pruebas):
            command.upgrade(configuracion, "head")
        yield motor
    finally:
        with patch("app.core.config.get_settings", return_value=settings_pruebas):
            command.downgrade(configuracion, "base")
        motor.dispose()


@pytest.fixture
def sesion_pruebas(motor_pruebas) -> Generator[Session, None, None]:
    fabrica = sessionmaker(
        bind=motor_pruebas,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )
    with fabrica() as db:
        for tabla in reversed(Base.metadata.sorted_tables):
            db.execute(delete(tabla))
        db.commit()
        yield db


@pytest.fixture(autouse=True)
def reiniciar_rate_limit():
    limiter.reset()
    yield
    limiter.reset()


@pytest.fixture
def cliente(motor_pruebas) -> Generator[TestClient, None, None]:
    fabrica = sessionmaker(
        bind=motor_pruebas,
        autoflush=False,
        autocommit=False,
        expire_on_commit=False,
    )

    def obtener_sesion():
        with fabrica() as db:
            yield db

    app.dependency_overrides[get_db] = obtener_sesion
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.pop(get_db, None)


@pytest.fixture
def crear_usuario(sesion_pruebas: Session) -> Callable:
    def crear(
        rol: RolUsuario,
        email: str | None = None,
        *,
        activo: bool = True,
        con_socio: bool | None = None,
        password: str = "ClaveSegura123",
    ) -> Usuario:
        direccion = email or f"{rol.value}@example.com"
        necesita_socio = rol == RolUsuario.SOCIO if con_socio is None else con_socio
        socio = None
        if necesita_socio:
            socio = Socio(
                nombre=f"Socio {direccion.split('@')[0]}",
                email=direccion,
                telefono="3001234567",
                activo=activo,
            )
            sesion_pruebas.add(socio)
            sesion_pruebas.flush()

        usuario = Usuario(
            email=direccion.lower(),
            nombre=f"Usuario {direccion.split('@')[0]}",
            password_hash=hash_password(password),
            rol=rol,
            activo=activo,
            socio_id=socio.id if socio else None,
        )
        sesion_pruebas.add(usuario)
        sesion_pruebas.commit()
        sesion_pruebas.refresh(usuario)
        return usuario

    return crear


@pytest.fixture
def crear_token_acceso():
    def crear(usuario: Usuario) -> str:
        token, _, _ = crear_token(
            usuario.id,
            usuario.rol.value,
            "access",
            timedelta(minutes=15),
        )
        return token

    return crear


@pytest.fixture
def encabezados_autorizacion():
    def crear(token: str) -> dict[str, str]:
        return {"Authorization": f"Bearer {token}"}

    return crear


@pytest.fixture
def catalogo(sesion_pruebas: Session):
    autor = Autor(nombre="Gabriel Garcia Marquez", nacionalidad="Colombiana")
    categoria = Categoria(nombre="Novela", descripcion="Narrativa")
    sesion_pruebas.add_all([autor, categoria])
    sesion_pruebas.flush()
    libro = Libro(
        titulo="Cien Anos De Soledad",
        isbn="9780307474728",
        anio_publicacion=1967,
        ejemplares=3,
        autor_id=autor.id,
        categorias=[categoria],
    )
    sesion_pruebas.add(libro)
    sesion_pruebas.commit()
    return {"autor": autor, "categoria": categoria, "libro": libro}


@pytest.fixture
def crear_socio(sesion_pruebas: Session) -> Callable:
    def crear(email: str = "socio@example.com", *, activo: bool = True) -> Socio:
        socio = Socio(
            nombre="Ana Ejemplo",
            email=email,
            telefono="3001234567",
            activo=activo,
        )
        sesion_pruebas.add(socio)
        sesion_pruebas.commit()
        sesion_pruebas.refresh(socio)
        return socio

    return crear
