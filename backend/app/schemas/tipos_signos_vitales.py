import uuid
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TipoSignoVitalRespuesta(BaseModel):
    """Se devuelven los tipos de signos vitales 
    (frecuencia cardíaca, saturación, etc.), 
    incluyendo sus rangos normal y crítico."""

    id: uuid.UUID
    nombre: str
    unidad: str
    rango_normal_min: Decimal
    rango_normal_max: Decimal
    rango_critico_min: Decimal
    rango_critico_max: Decimal

    model_config = ConfigDict(from_attributes=True)