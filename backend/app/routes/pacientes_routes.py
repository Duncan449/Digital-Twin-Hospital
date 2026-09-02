from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.pacientes import PacienteCrear, PacienteRespuesta
from app.services.pacientes_service import crear_paciente

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post(
    "",
    response_model=PacienteRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def crear_paciente_endpoint(
    datos: PacienteCrear,
    db: AsyncSession = Depends(get_db),
):
    """
    Crea un nuevo paciente. Automáticamente se genera su Digital Twin
    asociado, con severidad inicial 'normal'.
    """
    return await crear_paciente(db, datos)
