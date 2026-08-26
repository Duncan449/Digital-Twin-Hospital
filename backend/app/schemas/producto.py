from pydantic import BaseModel
from datetime import datetime


class ProductoIn(BaseModel):
    codigo: str
    nombre: str
    descripcion: str | None = None
    precio_compra: float
    precio_venta: float
    fk_categoria: int
    fk_proveedor: int
    stock_minimo: int | None = None
    activo: bool = True


class ProductoOut(BaseModel):
    id: int
    codigo: str
    nombre: str
    descripcion: str | None = None
    precio_compra: float
    precio_venta: float
    fk_categoria: int
    fk_proveedor: int
    stock_minimo: int | None = None
    activo: bool
    fecha_creacion: datetime | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }
