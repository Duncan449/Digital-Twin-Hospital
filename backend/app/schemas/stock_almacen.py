from pydantic import BaseModel
from datetime import datetime


class Stock_AlmacenIn(BaseModel):
    fk_producto: int
    fk_almacen: int
    cantidad_disponible: int 
    cantidad_reservada: int 

class Stock_AlmacenOut(BaseModel):
    id: int
    fk_producto: int
    fk_almacen: int
    cantidad_disponible: int 
    cantidad_reservada: int 
    fecha_ultima_actualizacion: datetime | None = None

    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }

class StockDetalladoOut(BaseModel):
    producto: str
    almacen: str
    total_disponible: int
    total_reservada: int

class StockConProductoOut(BaseModel):
    id: int
    fk_producto: int
    fk_almacen: int
    cantidad_disponible: int
    cantidad_reservada: int
    fecha_ultima_actualizacion: datetime | None = None
    nombre_producto: str
    class Config:
        json_encoders = {
            datetime: lambda v: v.strftime("%d/%m/%Y %H:%M:%S") if v else None
        }

class StockPorProductoOut(BaseModel):
    fk_producto: int
    total_disponible: int


class StockPorAlmacenOut(BaseModel):
    fk_producto: int
    codigo_producto: str
    nombre_producto: str
    cantidad_disponible: int
    cantidad_reservada: int
