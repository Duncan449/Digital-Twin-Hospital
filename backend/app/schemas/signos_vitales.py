import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import OrigenMedicion


class SignoVitalCrear(BaseModel):
    """Lo que manda el cliente (o el simulador) para registrar una medición."""

    tipo_signo_id: uuid.UUID
    valor: Decimal = Field(gt=0, description = "El valor del signo vital debe ser mayor que cero.")
    origen: OrigenMedicion = OrigenMedicion.simulado


class SignoVitalRespuesta(BaseModel):
    """Lo que la API devuelve tras registrar o listar una medición."""

    id: uuid.UUID
    paciente_id: uuid.UUID
    tipo_signo_id: uuid.UUID
    valor: Decimal
    origen: OrigenMedicion
    medido_en: datetime

    # Permite construir este schema directo desde el objeto SQLAlchemy.
    model_config = ConfigDict(from_attributes=True)
