from pydantic import BaseModel
from datetime import datetime


class MovimientoInventarioIn(BaseModel):
    fk_producto: int
    fk_almacen: int
    tipo_movimiento: str
    cantidad: int
    motivo: str | None = None
    fk_usuario: int
    fk_proveedor: int | None = None


class MovimientoInventarioOut(BaseModel):
    id: int
    fk_producto: int
    fk_almacen: int
    tipo_movimiento: str
    cantidad: int
    cantidad_anterior: int
    cantidad_nueva: int
    motivo: str | None = None
    fk_usuario: int
    fk_proveedor: int | None = None
    fecha_movimiento: datetime | None = None
    nombre_usuario: str| None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
        