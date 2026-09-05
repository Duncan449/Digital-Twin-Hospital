import uuid

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.schemas.tipos_signos_vitales import TipoSignoVitalRespuesta
from app.services.tipos_signos_vitales_service import (
    listar_tipos_signos_vitales,
    obtener_tipo_signo_vital,
)

router = APIRouter(prefix="/tipos-signos-vitales", tags=["Tipos de Signos Vitales"])


@router.get("", response_model=list[TipoSignoVitalRespuesta])
async def listar_tipos_signos_vitales_endpoint(db: AsyncSession = Depends(get_db)):
    """
    Catálogo completo de tipos de signos vitales.
    """
    return await listar_tipos_signos_vitales(db)


@router.get("/{tipo_signo_id}", response_model=TipoSignoVitalRespuesta)
async def obtener_tipo_signo_vital_endpoint(
    tipo_signo_id: uuid.UUID, db: AsyncSession = Depends(get_db)
):
    """Devuelve un tipo de signo vital puntual por su id."""
    return await obtener_tipo_signo_vital(db, tipo_signo_id)