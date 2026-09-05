import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.enums import EstadoPaciente
from app.config.database import get_db
from app.schemas.pacientes import PacienteActualizar, PacienteCrear, PacienteRespuesta
from app.services.pacientes_service import (
    actualizar_paciente,
    crear_paciente,
    listar_pacientes,
    obtener_paciente,
    dar_de_alta_paciente,
)

router = APIRouter(prefix="/pacientes", tags=["Pacientes"])


@router.post("", response_model=PacienteRespuesta, status_code=status.HTTP_201_CREATED)
async def crear_paciente_endpoint(
    datos: PacienteCrear,
    db: AsyncSession = Depends(get_db),
):
    """Crea un nuevo paciente. Automáticamente se genera su Digital Twin asociado."""
    return await crear_paciente(db, datos)


@router.get("", response_model=list[PacienteRespuesta])
async def listar_pacientes_endpoint(
    estado: EstadoPaciente = EstadoPaciente.internado,
    db: AsyncSession = Depends(get_db),
):
    """Lista pacientes por estado. Por default, solo internados."""
    return await listar_pacientes(db, estado)


@router.get("/{paciente_id}", response_model=PacienteRespuesta)
async def obtener_paciente_endpoint(
    paciente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve un paciente puntual por su id."""
    return await obtener_paciente(db, paciente_id)


@router.patch("/{paciente_id}", response_model=PacienteRespuesta)
async def actualizar_paciente_endpoint(
    paciente_id: uuid.UUID,
    datos: PacienteActualizar,
    db: AsyncSession = Depends(get_db),
):
    """Actualiza datos administrativos del paciente (sala, cama, género)."""
    return await actualizar_paciente(db, paciente_id, datos)


@router.patch("/{paciente_id}/dar-de-alta", response_model=PacienteRespuesta)
async def dar_de_alta_paciente_endpoint(
    paciente_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Da de alta a un paciente (soft delete)"""
    return await dar_de_alta_paciente(db, paciente_id)
