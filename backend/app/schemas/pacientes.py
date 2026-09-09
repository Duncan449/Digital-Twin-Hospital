import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict

from app.models.enums import NivelSeveridad


class PacienteCrear(BaseModel):
    """Lo que el cliente manda en el POST. Sin id ni estado, que se generan automáticamente."""

    nombre: str
    apellido: str
    documento: str
    fecha_nacimiento: date
    genero: str | None = None
    sala: str | None = None
    cama: str | None = None


class PacienteActualizar(BaseModel):
    """Para actualizaciones administrativas (PATCH). Todo opcional:
    se actualiza solo lo que venga en el body.

    Incluye tanto datos operativos (sala, cama, genero) como de identidad
    (nombre, apellido, documento, fecha_nacimiento) para casos de
    corrección de errores de tipeo. Todo cambio queda registrado en
    la tabla eventos para trazabilidad."""

    nombre: str | None = None
    apellido: str | None = None
    documento: str | None = None
    fecha_nacimiento: date | None = None
    sala: str | None = None
    cama: str | None = None
    genero: str | None = None


class DigitalTwinRespuesta(BaseModel):
    """
    Espeja el modelo DigitalTwin. Va anidado dentro de PacienteRespuesta
    en vez de tener su propio endpoint GET: así el Dashboard trae el
    estado de severidad de TODOS los pacientes en una sola llamada
    (GET /pacientes), en vez de tener que pedir un digital twin por
    paciente aparte (el clásico problema N+1).
    """

    id: uuid.UUID
    paciente_id: uuid.UUID
    severidad_actual: NivelSeveridad
    ultima_actualizacion: datetime
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class PacienteRespuesta(BaseModel):
    """Lo que la API devuelve al cliente."""

    id: uuid.UUID
    nombre: str
    apellido: str
    documento: str
    fecha_nacimiento: date
    estado: str
    sala: str | None
    cama: str | None
    fecha_ingreso: datetime
    # No es Optional: la creación de un paciente SIEMPRE genera su
    # digital twin en la misma transacción atómica (ver crear_paciente
    # en el service), así que todo paciente que llega hasta acá tiene uno.
    digital_twin: DigitalTwinRespuesta

    # Permite construir este schema directo desde un objeto SQLAlchemy
    # (paciente.nombre en vez de paciente["nombre"])
    model_config = ConfigDict(from_attributes=True)