from datetime import date
from pydantic import BaseModel

class LibroMasPrestadoReporte(BaseModel):
    libro_id: int
    titulo: str
    autor_nombre: str
    total_prestamos: int

class CategoriaReporte(BaseModel):
    categoria_id: int
    nombre: str
    total_libros: int

class PrestamoVencidoReporte(BaseModel):
    prestamo_id: int
    titulo_libro: str
    socio_nombre: str
    socio_email: str
    fecha_limite: date
    dias_retraso: int

class SocioConMultasReporte(BaseModel):
    socio_id: int
    socio_nombre: str
    total_multas: float
    prestamos_con_multa: int

class AutorReporte(BaseModel):
    autor_id: int
    nombre: str
    total_libros: int
    total_ejemplares: int
    total_prestamos: int

class ResumenReporte(BaseModel):
    total_libros: int
    total_ejemplares: int
    total_prestamos_activos: int
    total_socios_activos: int
    total_prestamos_vencidos: int
    total_multas_recabadas: float