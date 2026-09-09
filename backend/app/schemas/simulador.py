import uuid
from decimal import Decimal
from enum import Enum

from pydantic import BaseModel, Field


class PatronSimulacion(str, Enum):
    """
    Cómo se genera la serie de valores entre el valor inicial y el final.
    - lineal: todos los pasos intermedios son equidistantes entre sí.
    - zigzag: los pasos intermedios alternan entre un valor más alto y uno más bajo que el anterior, pero siempre dentro del rango inicial-final.
    - ruido: similar al lineal pero con un componente aleatorio para mayor realismo.
    """

    lineal = "lineal"
    zigzag = "zigzag"
    ruido = "ruido"


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
    patron: PatronSimulacion = Field(
        default=PatronSimulacion.lineal,
        description=(
            "lineal = interpolación recta entre valor_inicial y valor_final. "
            "zigzag = alterna entre valor_inicial y valor_final en cada paso, "
            "útil para probar que el motor de detección cruza el umbral varias veces. "
            "ruido = sigue la tendencia lineal pero con variación "
            "aleatoria en cada paso, simulando un signo vital real."
        ),
    )
    amplitud_ruido: Decimal = Field(
        default=Decimal("1.0"),
        gt=0,
        description="Solo se usa si patron='ruido': variación máxima (+/-) sobre la tendencia lineal en cada paso.",
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
    patron: PatronSimulacion
