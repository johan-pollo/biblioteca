from sqlalchemy import func, select
from sqlalchemy.orm import Session


def paginar(
    db: Session,
    consulta,
    skip: int,
    limit: int,
    *,
    columna_unica=None,
    mappings: bool = False,
) -> dict:
    if columna_unica is None:
        consulta_conteo = consulta.order_by(None).subquery()
    else:
        consulta_conteo = (
            consulta.with_only_columns(
                columna_unica, maintain_column_froms=True
            )
            .order_by(None)
            .distinct()
            .subquery()
        )
    total = db.scalar(select(func.count()).select_from(consulta_conteo)) or 0
    resultado = db.execute(consulta.offset(skip).limit(limit))
    items = resultado.mappings().all() if mappings else resultado.scalars().unique().all()
    return {"items": items, "total": total, "skip": skip, "limit": limit}
