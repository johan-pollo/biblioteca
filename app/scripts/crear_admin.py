from getpass import getpass

from sqlalchemy import func, select

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.usuario import RolUsuario, Usuario


def main() -> None:
    email = input("Correo del administrador: ").strip().lower()
    with SessionLocal() as db:
        usuario_existente = db.scalar(
            select(Usuario.id).where(func.lower(Usuario.email) == email)
        )
        if usuario_existente is not None:
            print("Ya existe un usuario con ese correo; no se realizaron cambios.")
            return

        password = getpass(
            "Contraseña (8-64 caracteres, mayúscula, minúscula y número): "
        )
        confirmar = getpass("Confirma la contraseña: ")
        if password != confirmar:
            raise ValueError("Las contraseñas no coinciden")
        if (
            len(password) < 8
            or len(password) > 64
            or not any(caracter.isupper() for caracter in password)
            or not any(caracter.islower() for caracter in password)
            or not any(caracter.isdigit() for caracter in password)
        ):
            raise ValueError(
                "La contraseña debe tener entre 8 y 64 caracteres e incluir "
                "mayúscula, minúscula y número"
            )

        nombre = " ".join(input("Nombre del administrador: ").strip().split()).title()
        usuario = Usuario(
            email=email,
            nombre=nombre,
            password_hash=hash_password(password),
            rol=RolUsuario.ADMIN,
            activo=True,
        )
        db.add(usuario)
        db.commit()
        print("Administrador creado correctamente.")


if __name__ == "__main__":
    main()