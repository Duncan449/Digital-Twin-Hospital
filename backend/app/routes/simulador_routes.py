import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.simulador import SimulacionCrear, SimulacionRespuesta
from app.services.simulador_service import iniciar_simulacion

router = APIRouter(prefix="/pacientes/{paciente_id}/simulacion", tags=["Simulador"])


@router.post(
    "", response_model=SimulacionRespuesta, status_code=status.HTTP_202_ACCEPTED
)
async def iniciar_simulacion_endpoint(
    paciente_id: uuid.UUID,
    datos: SimulacionCrear,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db),
):
    """
    Genera una serie de valores por interpolación lineal y los va
    registrando de a uno, con o sin pausa entre mediciones según
    intervalo_segundos. Devuelve 202 ACCEPTED ya que la
    simulación se ACEPTÓ para procesar, pero todavía no terminó de crear
    nada en el momento en que esta respuesta se manda ( se hace después en segundo plano).

    Para simular varios signos vitales a la vez ( Por ej: temperatura Y
    frecuencia cardíaca subiendo juntas), o varios pacientes a la vez, se
    llama a este mismo endpoint una vez por cada combinación de paciente y signo vital.
    """

    return await iniciar_simulacion(db, background_tasks, paciente_id, datos)
