import json
from typing import Optional
from fastapi import APIRouter, Depends, Form, File, UploadFile, status
from app.core.dependencies import SessionDep, PaginacionDep
from app.core.dependencies import requiere_rol
from app.models.usuario import RolUsuario
from app.schemas.libro import LibroCreate, LibroUpdate, LibroResponse, OrdenLibros
from app.controllers import libro as libro_controller
from app.schemas.pagina import Pagina
from app.core.cloudinary import subir_imagen_libro
from app.core.exceptions import ReglaNegocio

router = APIRouter(prefix="/libros", tags=["Libros"])

@router.get("", response_model=Pagina[LibroResponse], summary="Listar libros", responses={404: {"description": "Recurso no encontrado"}})
def listar(
    db: SessionDep,
    paginacion: PaginacionDep,
    buscar: Optional[str] = None,
    autor: Optional[str] = None,
    categoria_id: Optional[int] = None,
    desde: Optional[int] = None,
    hasta: Optional[int] = None,
    orden: Optional[OrdenLibros] = None
):
    return libro_controller.listar_libros(
        db,
        skip=paginacion.skip,
        limit=paginacion.limit,
        buscar=buscar,
        autor=autor,
        categoria_id=categoria_id,
        desde=desde,
        hasta=hasta,
        orden=orden
    )

@router.get("/{libro_id}", response_model=LibroResponse, summary="Consultar un libro", responses={404: {"description": "Libro no encontrado"}})
def obtener(libro_id: int, db: SessionDep):
    return libro_controller.obtener_libro(db, libro_id)

@router.post(
    "",
    response_model=LibroResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))],
    summary="Crear libro (soporta JSON o Form con imagen a Cloudinary)"
)
async def crear(
    db: SessionDep,
    datos: Optional[LibroCreate] = None,
    # Soporte para subida directa de imagen multipart/form-data:
    titulo: Optional[str] = Form(None),
    isbn: Optional[str] = Form(None),
    anio_publicacion: Optional[int] = Form(None),
    ejemplares: Optional[int] = Form(None),
    autor_id: Optional[int] = Form(None),
    categoria_ids: Optional[str] = Form(None, description="Lista de IDs de categorías, ej: [1, 2] o 1,2"),
    imagen: Optional[UploadFile] = File(None, description="Archivo de imagen de portada para subir a Cloudinary")
):
    imagen_url = None
    if imagen and imagen.filename:
        imagen_bytes = await imagen.read()
        if imagen_bytes:
            imagen_url = subir_imagen_libro(imagen_bytes)

    if datos is not None:
        return libro_controller.crear_libro(db, datos, imagen_url=imagen_url)

    if not all([titulo, isbn, anio_publicacion, ejemplares, autor_id, categoria_ids]):
        raise ReglaNegocio("Debe enviar los datos del libro ya sea en el cuerpo JSON o mediante formulario multipart")

    try:
        if categoria_ids.strip().startswith("["):
            cat_list = json.loads(categoria_ids)
        else:
            cat_list = [int(c.strip()) for c in categoria_ids.split(",") if c.strip()]
    except Exception:
        raise ReglaNegocio("Formato inválido en categoria_ids; use formato JSON [1, 2] o números separados por comas")

    libro_data = LibroCreate(
        titulo=titulo,
        isbn=isbn,
        anio_publicacion=anio_publicacion,
        ejemplares=ejemplares,
        autor_id=autor_id,
        categoria_ids=cat_list
    )
    return libro_controller.crear_libro(db, libro_data, imagen_url=imagen_url)

@router.post(
    "/{libro_id}/portada",
    response_model=LibroResponse,
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))],
    summary="Subir o actualizar la portada de un libro en Cloudinary"
)
async def subir_portada(
    libro_id: int,
    db: SessionDep,
    imagen: UploadFile = File(..., description="Archivo de imagen de portada")
):
    libro = libro_controller.obtener_libro(db, libro_id)
    imagen_bytes = await imagen.read()
    if not imagen_bytes:
        raise ReglaNegocio("El archivo de imagen está vacío")

    public_id = f"libro_{libro_id}_{libro['isbn']}"
    imagen_url = subir_imagen_libro(imagen_bytes, public_id=public_id)

    return libro_controller.actualizar_libro(db, libro_id, LibroUpdate(), imagen_url=imagen_url)

@router.patch("/{libro_id}", response_model=LibroResponse, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def actualizar(libro_id: int, datos: LibroUpdate, db: SessionDep):
    return libro_controller.actualizar_libro(db, libro_id, datos)

@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))])
def eliminar(libro_id: int, db: SessionDep):
    libro_controller.eliminar_libro(db, libro_id)
