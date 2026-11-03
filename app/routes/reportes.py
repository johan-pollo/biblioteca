from fastapi import APIRouter, Depends
from app.core.dependencies import SessionDep, PaginacionDep, requiere_rol
from app.models.usuario import RolUsuario
from app.schemas.pagina import Pagina
from app.schemas.reportes import (
    LibroMasPrestadoReporte,
    CategoriaReporte,
    PrestamoVencidoReporte,
    SocioConMultasReporte,
    AutorReporte,
    ResumenReporte
)
from app.controllers import reportes as reportes_controller

router = APIRouter(
    prefix="/reportes",
    tags=["Reportes"],
    dependencies=[Depends(requiere_rol(RolUsuario.ADMIN, RolUsuario.BIBLIOTECARIO))],
)

@router.get("/libros-mas-prestados", response_model=Pagina[LibroMasPrestadoReporte], summary="Consultar libros más prestados")
def libros_mas_prestados(db: SessionDep, paginacion: PaginacionDep):
    return reportes_controller.libros_mas_prestados(db, paginacion.skip, paginacion.limit)

@router.get("/categorias", response_model=Pagina[CategoriaReporte], summary="Consultar estadísticas por categoría")
def reporte_categorias(db: SessionDep, paginacion: PaginacionDep):
    return reportes_controller.reporte_categorias(db, paginacion.skip, paginacion.limit)

@router.get("/prestamos-vencidos", response_model=Pagina[PrestamoVencidoReporte], summary="Consultar préstamos vencidos")
def prestamos_vencidos(db: SessionDep, paginacion: PaginacionDep):
    return reportes_controller.prestamos_vencidos(db, paginacion.skip, paginacion.limit)

@router.get("/socios-con-multas", response_model=Pagina[SocioConMultasReporte], summary="Consultar socios con multas")
def socios_con_multas(db: SessionDep, paginacion: PaginacionDep):
    return reportes_controller.socios_con_multas(db, paginacion.skip, paginacion.limit)

@router.get("/autores", response_model=Pagina[AutorReporte], summary="Consultar estadísticas por autor")
def reporte_autores(db: SessionDep, paginacion: PaginacionDep):
    return reportes_controller.reporte_autores(db, paginacion.skip, paginacion.limit)

@router.get("/resumen", response_model=ResumenReporte, summary="Consultar resumen de la biblioteca")
def resumen_general(db: SessionDep):
    return reportes_controller.resumen_general(db)