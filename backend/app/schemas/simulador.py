import uuid
from decimal import Decimal

from pydantic import BaseModel, Field


class SimulacionCrear(BaseModel):
    """
    Lo que pide el cliente para simular la evolución de UN signo vital de
    UN paciente.
    """

    tipo_signo_id: uuid.UUID
    valor_inicial: Decimal = Field(gt=0)
    valor_final: Decimal = Field(gt=0)
    cantidad_pasos: int = Field(
        ge=2,
        le=200,
        description="Cantidad de mediciones a generar, incluyendo el valor inicial y el final.",
    )
    intervalo_segundos: int = Field(
        ge=0,
        default=0,
        description=(
            "0 = inserta todas las mediciones al instante (modo histórico). "
            ">0 = espera esa cantidad de segundos entre medición y medición (modo tiempo real)."
        ),
    )


class SimulacionRespuesta(BaseModel):
    """
    Respuesta INMEDIATA al disparar la simulación. NO incluye
    las mediciones generadas, como corren en segundo plano, todavía no
    existen en el momento en que se arma esta respuesta.
    """

    mensaje: str
    cantidad_mediciones: int
    paciente_id: uuid.UUID
    tipo_signo_id: uuid.UUID
    intervalo_segundos: int
