import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.models.enums import EstadoAlerta, NivelSeveridad, OrigenMedicion


class SignoVitalCrear(BaseModel):
    """Lo que manda el cliente (o el simulador) para registrar una medición."""

    tipo_signo_id: uuid.UUID
    valor: Decimal = Field(gt=0, description="El valor del signo vital debe ser mayor que cero.")
    origen: OrigenMedicion = OrigenMedicion.simulado


class SignoVitalRespuesta(BaseModel):
    """Lo que la API devuelve al listar mediciones (GET)."""

    id: uuid.UUID
    paciente_id: uuid.UUID
    tipo_signo_id: uuid.UUID
    valor: Decimal
    origen: OrigenMedicion
    medido_en: datetime

    model_config = ConfigDict(from_attributes=True)


class AlertaResumen(BaseModel):
    """Resumen de la alerta generada o actualizada por esta medición (si aplica)."""

    id: uuid.UUID
    severidad: NivelSeveridad
    estado: EstadoAlerta
    valor_detectado: Decimal

    model_config = ConfigDict(from_attributes=True)


class SignoVitalRegistradoRespuesta(BaseModel):
    """
    Lo que devuelve POST /signos-vitales: la medición guardada + el
    resultado del motor de detección. Enriquecida a propósito para poder
    validar el motor completo desde Swagger/Postman, sin depender
    todavía del websocket.
    """

    signo_vital: SignoVitalRespuesta
    severidad_calculada: NivelSeveridad
    alerta: AlertaResumen | None = None
