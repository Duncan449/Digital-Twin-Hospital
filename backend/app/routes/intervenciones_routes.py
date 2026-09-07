import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.dependencies.auth import get_current_user
from app.models.usuarios import Usuario
from app.schemas.intervenciones import IntervencionCrear, IntervencionRespuesta
from app.services.intervenciones_service import registrar_intervencion

router = APIRouter(prefix="/alertas/{alerta_id}/intervenciones", tags=["Intervenciones"])


@router.post("", response_model=IntervencionRespuesta, status_code=status.HTTP_201_CREATED)
async def registrar_intervencion_endpoint(
    alerta_id: uuid.UUID,
    datos: IntervencionCrear,
    db: AsyncSession = Depends(get_db),
    usuario_actual: Usuario = Depends(get_current_user),
):
    """Registra la intervención del personal autenticado sobre una alerta."""
    return await registrar_intervencion(db, alerta_id, datos, usuario_actual.id)