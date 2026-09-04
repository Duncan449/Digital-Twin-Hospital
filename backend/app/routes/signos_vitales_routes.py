import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.signos_vitales import (
    AlertaResumen,
    SignoVitalCrear,
    SignoVitalRegistradoRespuesta,
    SignoVitalRespuesta,
)
from app.services.signos_vitales_service import (
    listar_signos_vitales_paciente,
    registrar_signo_vital,
)

router = APIRouter(
    prefix="/pacientes/{paciente_id}/signos-vitales", tags=["Signos Vitales"]
)


@router.post(
    "", response_model=SignoVitalRegistradoRespuesta, status_code=status.HTTP_201_CREATED
)
async def registrar_signo_vital_endpoint(
    paciente_id: uuid.UUID,
    datos: SignoVitalCrear,
    db: AsyncSession = Depends(get_db),
):
    """
    Registra una medición y evalúa su severidad con el motor de
    detección. Genera un Evento siempre, y una Alerta si la severidad
    es "precaucion" o "critica".
    """
    resultado = await registrar_signo_vital(db, paciente_id, datos)
    return SignoVitalRegistradoRespuesta(
        signo_vital=SignoVitalRespuesta.model_validate(resultado["signo_vital"]),
        severidad_calculada=resultado["severidad_calculada"],
        alerta=(
            AlertaResumen.model_validate(resultado["alerta"])
            if resultado["alerta"] is not None
            else None
        ),
    )


@router.get("", response_model=list[SignoVitalRespuesta])
async def listar_signos_vitales_endpoint(
    paciente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve el historial de mediciones de un paciente, más reciente primero."""
    return await listar_signos_vitales_paciente(db, paciente_id)