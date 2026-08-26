# backend/app/schemas/proveedor.py
from pydantic import BaseModel, EmailStr
from datetime import datetime


class ProveedorIn(BaseModel):
    nombre: str
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = None
    activo: bool = True


class ProveedorOut(BaseModel):
    id: int
    nombre: str
    telefono: str | None = None
    email: EmailStr | None = None
    direccion: str | None = None
    ciudad: str | None = None
    activo: bool = True
    fecha_creacion: datetime | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
