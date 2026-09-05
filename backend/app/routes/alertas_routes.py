import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.dependencies.auth import get_current_user
from app.models.enums import EstadoAlerta
from app.models.usuarios import Usuario
from app.schemas.intervenciones import AlertaDetalle, IntervencionCrear, IntervencionRespuesta
from app.services.alertas_service import (
    listar_alertas,
    obtener_alerta,
    registrar_intervencion,
)

router = APIRouter(prefix="/alertas", tags=["Alertas"])


@router.get("", response_model=list[AlertaDetalle])
async def listar_alertas_endpoint(
    paciente_id: uuid.UUID | None = None,
    estado: EstadoAlerta | None = None,
    db: AsyncSession = Depends(get_db),
):
    """
    Lista alertas, más recientes primero. Filtros opcionales por
    paciente y/o estado (ej: ?estado=activa para ver solo las que
    siguen pendientes de intervención).
    """
    return await listar_alertas(db, paciente_id=paciente_id, estado=estado)


@router.get("/{alerta_id}", response_model=AlertaDetalle)
async def obtener_alerta_endpoint(
    alerta_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Devuelve una alerta puntual junto con sus intervenciones registradas."""
    return await obtener_alerta(db, alerta_id)


@router.post(
    "/{alerta_id}/intervenciones",
    response_model=IntervencionRespuesta,
    status_code=status.HTTP_201_CREATED,
)
async def registrar_intervencion_endpoint(
    alerta_id: uuid.UUID,
    datos: IntervencionCrear,
    db: AsyncSession = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    """
    Registra la intervención del personal médico que cierra la alerta.

    Requiere estar autenticado (Bearer token de /auth/login): el
    usuario que hizo la intervención se toma del token, no del body, así
    queda una trazabilidad real de quién la registró.
    """
    return await registrar_intervencion(db, alerta_id, usuario_actual.id, datos)
