from fastapi import APIRouter
from fastapi.responses import JSONResponse
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.dependencies import SessionDep

router = APIRouter(tags=["Salud"])


@router.get("/health", summary="Comprobar el estado de la API y la base de datos", responses={503: {"description": "Base de datos no disponible"}})
def comprobar_salud(db: SessionDep):
    try:
        db.execute(text("SELECT 1"))
    except SQLAlchemyError:
        return JSONResponse(
            status_code=503,
            content={"status": "error", "database": "error"},
        )

    return {"status": "ok", "database": "ok"}