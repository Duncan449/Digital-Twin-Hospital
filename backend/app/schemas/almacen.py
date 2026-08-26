from pydantic import BaseModel
from datetime import datetime


class AlmacenIn(BaseModel):
    nombre: str
    ubicacion: str
    activo: bool = True

class AlmacenOut(BaseModel):
    id: int
    nombre: str
    ubicacion: str
    activo: bool = True
    fecha_creacion: datetime | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }