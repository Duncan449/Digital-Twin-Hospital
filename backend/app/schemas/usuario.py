from pydantic import BaseModel, EmailStr
from datetime import datetime


class UsuarioIn(BaseModel):  # Para el registro de un usuario
    nombre: str
    email: EmailStr
    password: str
    rol: str


class UsuarioUpdate(BaseModel):  # Para la actualización de un usuario
    nombre: str
    email: EmailStr
    rol: str


class UsuarioOut(BaseModel):
    id: int
    nombre: str
    email: EmailStr
    rol: str
    activo: bool = True
    fecha_creacion: datetime | None = None
    fecha_ultima_sesion: datetime | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
