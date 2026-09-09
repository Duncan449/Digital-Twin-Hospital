import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict

from app.models.enums import EstadoAlerta, NivelSeveridad


class AlertaRespuesta(BaseModel):
    """Lo que la API devuelve al listar o consultar alertas."""

    id: uuid.UUID
    paciente_id: uuid.UUID
    tipo_signo_id: uuid.UUID | None
    severidad: NivelSeveridad
    valor_detectado: Decimal | None
    estado: EstadoAlerta
    workflow_id_temporal: str | None
    creada_en: datetime
    resuelta_en: datetime | None

    model_config = ConfigDict(from_attributes=True)
