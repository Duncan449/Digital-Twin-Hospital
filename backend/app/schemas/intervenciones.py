import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoAlerta, NivelSeveridad


class IntervencionCrear(BaseModel):
    """Lo que manda el personal médico para registrar la intervención que cierra una alerta."""

    accion: str = Field(
        min_length=1,
        max_length=150,
        description="Acción tomada por el personal (ej: 'Ajuste de medicación', 'Visita a la cama').",
    )
    observaciones: str | None = Field(
        default=None, description="Notas u observaciones adicionales, opcional."
    )


class IntervencionRespuesta(BaseModel):
    """Lo que devuelve la API al registrar (o consultar) una intervención."""

    id: uuid.UUID
    alerta_id: uuid.UUID
    usuario_id: uuid.UUID | None
    accion: str
    observaciones: str | None
    iniciada_en: datetime
    finalizada_en: datetime | None

    model_config = ConfigDict(from_attributes=True)


class AlertaDetalle(BaseModel):
    """Detalle completo de una alerta, incluyendo sus intervenciones."""

    id: uuid.UUID
    paciente_id: uuid.UUID
    tipo_signo_id: uuid.UUID | None
    severidad: NivelSeveridad
    valor_detectado: float | None
    estado: EstadoAlerta
    creada_en: datetime
    normalizada_en: datetime | None
    resuelta_en: datetime | None
    intervenciones: list[IntervencionRespuesta] = []

    model_config = ConfigDict(from_attributes=True)
