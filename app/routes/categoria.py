from fastapi import APIRouter, Depends, status
from app.core.dependencies import SessionDep, PaginacionDep
from app.core.dependencies import requiere_rol
from app.models.usuario import RolUsuario
from app.schemas.categoria import CategoriaCreate, CategoriaUpdate, CategoriaResponse
from app.controllers import categoria as categoria_controller
from app.schemas.pagina import Pagina

router = APIRouter(prefix="/categorias", tags=["Categorías"])

@router.get("", response_model=Pagina[CategoriaResponse], summary="Listar categorías", responses={404: {"description": "Recurso no encontrado"}})
def listar(db: SessionDep, paginacion: PaginacionDep):
    return categoria_controller.listar_categorias(db, skip=paginacion.skip, limit=paginacion.limit)

@router.post("", response_model=CategoriaResponse, status_code=status.HTTP_201_CREATED, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def crear(datos: CategoriaCreate, db: SessionDep):
    return categoria_controller.crear_categoria(db, datos)

@router.patch("/{categoria_id}", response_model=CategoriaResponse, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))])
def actualizar(categoria_id: int, datos: CategoriaUpdate, db: SessionDep):
    return categoria_controller.actualizar_categoria(db, categoria_id, datos)

@router.delete("/{categoria_id}", status_code=status.HTTP_204_NO_CONTENT, dependencies=[Depends(requiere_rol(RolUsuario.ADMIN))])
def eliminar(categoria_id: int, db: SessionDep):
    categoria_controller.eliminar_categoria(db, categoria_id)