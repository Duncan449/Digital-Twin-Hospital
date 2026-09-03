import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class UsuarioCrear(BaseModel):
    """Lo que llega en el POST. La contraseña viaja en texto plano solo en
    este paso (por HTTPS) y se hashea en el service antes de tocar la DB."""

    nombre: str
    email: EmailStr
    password: str = Field(min_length=8)
    rol_id: uuid.UUID


class UsuarioActualizar(BaseModel):
    """Para PATCH. Todo opcional: se actualiza solo lo que venga en el body.
    A propósito no incluye password ni rol_id -- cambiar la contraseña o el
    rol de alguien merece su propio endpoint, no mezclarse en un update genérico."""

    nombre: str | None = None
    activo: bool | None = None


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str


class UsuarioRespuesta(BaseModel):
    """Lo que la API devuelve. A propósito NO incluye password ni password_hash:
    es la barrera para que ese dato nunca salga por la red."""

    id: uuid.UUID
    nombre: str
    email: EmailStr
    rol_id: uuid.UUID
    activo: bool
    creado_en: datetime

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """Lo que devuelve /auth/login tras un login exitoso."""

    access_token: str
    token_type: str = "bearer"


class RolCrear(BaseModel):
    nombre: str
    descripcion: str | None = None
    permisos: dict[str, bool] = {}


class RolRespuesta(BaseModel):
    id: uuid.UUID
    nombre: str
    descripcion: str | None
    permisos: dict[str, bool]

    model_config = ConfigDict(from_attributes=True)