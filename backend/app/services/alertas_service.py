import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import Alerta
from app.models.enums import EstadoAlerta
from app.services.pacientes_service import obtener_paciente


async def listar_alertas(
    db: AsyncSession, estado: EstadoAlerta = EstadoAlerta.activa
) -> list[Alerta]:
    """
    Lista alertas filtradas por estado. Por default trae solo las activas, pero se puede pedir explícitamente
      'en_atencion' o 'resuelta' para vistas de historial. Más recientes primero.
    """
    resultado = await db.execute(
        select(Alerta).where(Alerta.estado == estado).order_by(Alerta.creada_en.desc())
    )
    return list(resultado.scalars().all())


async def obtener_alerta(db: AsyncSession, alerta_id: uuid.UUID) -> Alerta:
    """Busca una alerta puntual por id. Lanza 404 si no existe."""
    alerta = await db.get(Alerta, alerta_id)
    if alerta is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No existe una alerta con id '{alerta_id}'.",
        )
    return alerta

async def listar_alertas_paciente(
    db: AsyncSession, paciente_id: uuid.UUID
) -> list[Alerta]:
    """
    Historial completo de alertas de un paciente puntual pensado para el registro de eventos
    del Digital Twin, no para el dashboard general.
    """
    await obtener_paciente(db, paciente_id)  # 404 si no existe

    resultado = await db.execute(
        select(Alerta)
        .where(Alerta.paciente_id == paciente_id)
        .order_by(Alerta.creada_en.desc())
    )
    return list(resultado.scalars().all())
