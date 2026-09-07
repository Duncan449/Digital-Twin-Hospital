import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class IntervencionCrear(BaseModel):
    """Lo que manda el personal al registrar que atendió una alerta."""

    accion: str
    observaciones: str | None = None


class IntervencionRespuesta(BaseModel):
    id: uuid.UUID
    alerta_id: uuid.UUID
    usuario_id: uuid.UUID | None
    accion: str
    observaciones: str | None
    iniciada_en: datetime
    finalizada_en: datetime | None

    model_config = ConfigDict(from_attributes=True)