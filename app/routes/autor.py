from typing import Optional
from fastapi import APIRouter, Depends, status
from app.core.dependencies import SessionDep, PaginacionDep, requiere_rol
from app.models.usuario import RolUsuario
from app.schemas.autor import AutorCreate, AutorUpdate, AutorResponse
from app.controllers import autor as autor_controller
from app.schemas.libro import LibroResponse
from app.schemas.pagina import Pagina
from app.controllers import libro as libro_controller

router = APIRouter(prefix="/autores", tags=["Autores"])

@router.get("", response_model=Pagina[AutorResponse], summary="Listar autores", responses={404: {"description": "Recurso no encontrado"}})
def listar(db: SessionDep, paginacion: PaginacionDep, nacionalidad: Optional[str] = None):
    return autor_controller.listar_autores(
        db, skip=paginacion.skip, limit=paginacion.limit, nacionalidad=nacionalidad
    )

@router.get("/{autor_id}", response_model=AutorResponse, summary="Consultar un autor", responses={404: {"description": "Autor no encontrado"}})
def obtener(autor_id: int, db: SessionDep):
    return autor_controller.obtener_autor(db, autor_id)

@router.post("", response_model=AutorResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def crear(datos: AutorCreate, db: SessionDep):
    return autor_controller.crear_autor(db, datos)

@router.patch("/{autor_id}", response_model=AutorResponse, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def actualizar(autor_id: int, datos: AutorUpdate, db: SessionDep):
    return autor_controller.actualizar_autor(db, autor_id, datos)

@router.delete("/{autor_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))])
def eliminar(autor_id: int, db: SessionDep):
    autor_controller.eliminar_autor(db, autor_id)

@router.get("/{autor_id}/libros", response_model=Pagina[LibroResponse], summary="Listar libros de un autor", responses={404: {"description": "Autor no encontrado"}})
def libros_por_autor(autor_id: int, db: SessionDep, paginacion: PaginacionDep):
    return libro_controller.listar_libros_por_autor(db, autor_id, skip=paginacion.skip, limit=paginacion.limit)