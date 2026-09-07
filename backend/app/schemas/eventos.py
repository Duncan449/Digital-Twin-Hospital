import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NivelSeveridad, TipoEvento


class EventoRespuesta(BaseModel):
    id: uuid.UUID
    paciente_id: uuid.UUID
    tipo: TipoEvento
    descripcion: str | None
    severidad: NivelSeveridad
    ocurrido_en: datetime

    model_config = ConfigDict(from_attributes=True)