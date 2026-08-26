from pydantic import BaseModel
from datetime import datetime


class CategoriaIn(BaseModel):
    nombre: str
    descripcion: str | None = None
    activa: bool = True


class CategoriaOut(BaseModel):
    id: int
    nombre: str
    descripcion: str | None = None
    activa: bool = True
    fecha_creacion: datetime | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
