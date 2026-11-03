import cloudinary
import cloudinary.uploader
from app.core.config import get_settings
from app.core.exceptions import ReglaNegocio

_configurado = False

def configurar_cloudinary():
    global _configurado
    if not _configurado:
        settings = get_settings()
        if settings.cloudinary_url:
            cloudinary.config(cloudinary_url=settings.cloudinary_url)
        cloudinary.config(secure=True)
        _configurado = True

def subir_imagen_libro(file_bytes_or_buffer, public_id: str | None = None) -> str:
    """
    Sube un archivo de imagen a Cloudinary en la carpeta 'biblioteca/libros' y retorna su URL segura HTTPS.
    """
    configurar_cloudinary()
    try:
        upload_params = {
            "folder": "biblioteca/libros",
            "resource_type": "image",
            "overwrite": True
        }
        if public_id:
            upload_params["public_id"] = public_id

        resultado = cloudinary.uploader.upload(
            file_bytes_or_buffer,
            **upload_params
        )
        return resultado.get("secure_url") or resultado.get("url")
    except Exception as e:
        raise ReglaNegocio(f"Error al subir imagen a Cloudinary: {str(e)}")

