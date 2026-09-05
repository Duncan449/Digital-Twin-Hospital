import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import TipoSignoVital


async def listar_tipos_signos_vitales(db: AsyncSession) -> list[TipoSignoVital]:
    """
    Devuelve el catálogo completo de tipos de signos vitales, ordenado
    alfabéticamente.
    """
    resultado = await db.execute(
        select(TipoSignoVital).order_by(TipoSignoVital.nombre)
    )
    return list(resultado.scalars().all())


async def obtener_tipo_signo_vital(
    db: AsyncSession, tipo_signo_id: uuid.UUID
) -> TipoSignoVital:
    """Busca un tipo de signo vital puntual por id. Lanza 404 si no existe."""
    tipo_signo = await db.get(TipoSignoVital, tipo_signo_id)
    if tipo_signo is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe un tipo de signo vital con id '{tipo_signo_id}'.",
        )
    return tipo_signo