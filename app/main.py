import logging
import time
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.openapi.utils import get_openapi
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware
from starlette.middleware.cors import CORSMiddleware

from app.core.config import get_settings
from app.core.exceptions import ErrorAplicacion, NoAutenticado
from app.core.limiter import limiter
from app.routes import autor, auth, categoria, health, libro, socio, prestamo, reportes, usuario

settings = get_settings()
logger = logging.getLogger("app.request")
app = FastAPI(
    title="API Biblioteca REST",
    docs_url=None if settings.environment == "prod" else "/docs",
    redoc_url=None if settings.environment == "prod" else "/redoc",
)
app.state.limiter = limiter
def rate_limit_exceeded_handler(request: Request, exc: Exception):
    if not isinstance(exc, RateLimitExceeded):
        raise TypeError("El manejador recibió una excepción inesperada")
    return _rate_limit_exceeded_handler(request, exc)


app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)


@app.middleware("http")
async def request_id_y_logging(request: Request, call_next):
    request_id = str(uuid4())
    inicio = time.perf_counter()
    try:
        respuesta = await call_next(request)
    except Exception as exc:
        respuesta = await error_interno_handler(request, exc)
    duracion_ms = (time.perf_counter() - inicio) * 1000
    respuesta.headers["X-Request-ID"] = request_id
    logger.info(
        "request_id=%s método=%s ruta=%s código=%s duración_ms=%.2f",
        request_id,
        request.method,
        request.url.path,
        respuesta.status_code,
        duracion_ms,
    )
    return respuesta


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(ErrorAplicacion)
def error_aplicacion_handler(request: Request, exc: ErrorAplicacion):
    headers = {"WWW-Authenticate": "Bearer"} if isinstance(exc, NoAutenticado) else None
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail},
        headers=headers,
    )


@app.exception_handler(Exception)
async def error_interno_handler(request: Request, exc: Exception):
    logger.error(
        "error_interno método=%s ruta=%s tipo=%s",
        request.method,
        request.url.path,
        type(exc).__name__,
    )
    return JSONResponse(
        status_code=500,
        content={"detail": "Error interno del servidor"},
    )


# Registro de routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(auth.router, prefix="/api/v1")
app.include_router(autor.router, prefix="/api/v1")
app.include_router(categoria.router, prefix="/api/v1")
app.include_router(libro.router, prefix="/api/v1")
app.include_router(socio.router, prefix="/api/v1")
app.include_router(prestamo.router, prefix="/api/v1")
app.include_router(reportes.router, prefix="/api/v1")
app.include_router(usuario.router, prefix="/api/v1")


def personalizar_openapi():
    if app.openapi_schema is not None:
        return app.openapi_schema

    esquema = get_openapi(
        title=app.title,
        version="1.0.0",
        routes=app.routes,
    )
    for ruta, metodos in esquema.get("paths", {}).items():
        for metodo, operacion in metodos.items():
            if metodo not in {"get", "post", "put", "patch", "delete"}:
                continue
            operacion.setdefault("summary", f"{metodo.upper()} {ruta}")
            respuestas = operacion.setdefault("responses", {})
            respuestas.setdefault("401", {"description": "No autenticado"})
            respuestas.setdefault("403", {"description": "No autorizado"})
            respuestas.setdefault("404", {"description": "Recurso no encontrado"})

    app.openapi_schema = esquema
    return esquema


app.openapi = personalizar_openapi