import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.eventos import EventoRespuesta
from app.services.eventos_service import listar_eventos_paciente

router = APIRouter(prefix="/pacientes/{paciente_id}/eventos", tags=["Eventos"])


@router.get("", response_model=list[EventoRespuesta])
async def listar_eventos_endpoint(paciente_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Historial cronológico de eventos de un paciente: registros de signos vitales, alertas generadas/actualizadas, escalaciones e intervenciones."""
    return await listar_eventos_paciente(db, paciente_id)