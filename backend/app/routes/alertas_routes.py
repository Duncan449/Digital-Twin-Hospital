import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.models.enums import EstadoAlerta
from app.schemas.alertas import AlertaRespuesta
from app.services.alertas_service import listar_alertas, listar_alertas_paciente, obtener_alerta

router = APIRouter(prefix="/alertas", tags=["Alertas"])
router_paciente = APIRouter(prefix="/pacientes/{paciente_id}/alertas", tags=["Alertas"])


@router.get("", response_model=list[AlertaRespuesta])
async def listar_alertas_endpoint(
    estado: EstadoAlerta = EstadoAlerta.activa,
    db: AsyncSession = Depends(get_db),
):
    """Lista alertas por estado. Por default, solo las activas."""
    return await listar_alertas(db, estado)


@router.get("/{alerta_id}", response_model=AlertaRespuesta)
async def obtener_alerta_endpoint(
    alerta_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve una alerta puntual por su id."""
    return await obtener_alerta(db, alerta_id)

@router_paciente.get("", response_model=list[AlertaRespuesta])
async def listar_alertas_paciente_endpoint(
    paciente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Historial completo de alertas de un paciente puntual, más reciente primero."""
    return await listar_alertas_paciente(db, paciente_id)
