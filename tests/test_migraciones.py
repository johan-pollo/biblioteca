from alembic import command
from alembic.config import Config

from app.core.config import get_settings


def test_upgrade_downgrade_upgrade_en_base_temporal(tmp_path, monkeypatch):
    base_temporal = tmp_path / "migraciones.db"
    url_sqlite = f"sqlite:///{base_temporal.as_posix()}"
    monkeypatch.setenv("DATABASE_URL", url_sqlite)
    monkeypatch.setenv("SECRET_KEY", "clave-de-pruebas-de-32-caracteres")
    get_settings.cache_clear()

    try:
        configuracion = Config("alembic.ini")
        command.upgrade(configuracion, "head")
        command.downgrade(configuracion, "base")
        command.upgrade(configuracion, "head")
    finally:
        get_settings.cache_clear()
