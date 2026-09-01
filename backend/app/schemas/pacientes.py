import uuid
from datetime import date, datetime

from pydantic import BaseModel, ConfigDict


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
    se actualiza solo lo que venga en el body."""

    sala: str | None = None
    cama: str | None = None
    genero: str | None = None


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

    # Permite construir este schema directo desde un objeto SQLAlchemy
    # (paciente.nombre en vez de paciente["nombre"])
    model_config = ConfigDict(from_attributes=True)
