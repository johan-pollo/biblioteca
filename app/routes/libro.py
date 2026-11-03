from typing import Optional
from fastapi import APIRouter, Depends, status
from app.core.dependencies import SessionDep, PaginacionDep
from app.core.dependencies import requiere_rol
from app.models.usuario import RolUsuario
from app.schemas.libro import LibroCreate, LibroUpdate, LibroResponse, OrdenLibros
from app.controllers import libro as libro_controller
from app.schemas.pagina import Pagina

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

@router.post("", response_model=LibroResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def crear(datos: LibroCreate, db: SessionDep):
    return libro_controller.crear_libro(db, datos)

@router.patch("/{libro_id}", response_model=LibroResponse, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def actualizar(libro_id: int, datos: LibroUpdate, db: SessionDep):
    return libro_controller.actualizar_libro(db, libro_id, datos)

@router.delete("/{libro_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))])
def eliminar(libro_id: int, db: SessionDep):
    libro_controller.eliminar_libro(db, libro_id)