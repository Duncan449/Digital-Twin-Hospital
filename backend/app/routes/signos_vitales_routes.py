import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.signos_vitales import SignoVitalCrear, SignoVitalRespuesta
from app.services.signos_vitales_service import (
    listar_signos_vitales_paciente,
    registrar_signo_vital,
)

router = APIRouter(
    prefix="/pacientes/{paciente_id}/signos-vitales", tags=["Signos Vitales"]
)


@router.post(
    "", response_model=SignoVitalRespuesta, status_code=status.HTTP_201_CREATED
)
async def registrar_signo_vital_endpoint(
    paciente_id: uuid.UUID,
    datos: SignoVitalCrear,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra una medición de signo vital para un paciente.

    Todavía no se integró el motor de detección de anomalías.
    """
    return await registrar_signo_vital(db, paciente_id, datos)


@router.get("", response_model=list[SignoVitalRespuesta])
async def listar_signos_vitales_endpoint(
    paciente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve el historial de mediciones de un paciente, más reciente primero."""
    return await listar_signos_vitales_paciente(db, paciente_id)
