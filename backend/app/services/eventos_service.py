import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.clinico import Evento
from app.services.pacientes_service import obtener_paciente


async def listar_eventos_paciente(db: AsyncSession, paciente_id: uuid.UUID) -> list[Evento]:
    """Historial cronológico completo de un paciente, más reciente primero."""
    await obtener_paciente(db, paciente_id)  # 404 si no existe

    resultado = await db.execute(
        select(Evento)
        .where(Evento.paciente_id == paciente_id)
        .order_by(Evento.ocurrido_en.desc())
    )
    return list(resultado.scalars().all())