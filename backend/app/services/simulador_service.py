import asyncio
import random
import uuid
from decimal import Decimal

from fastapi import BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import AsyncSessionLocal
from app.models.enums import OrigenMedicion
from app.schemas.signos_vitales import SignoVitalCrear
from app.schemas.simulador import PatronSimulacion, SimulacionCrear
from app.services.pacientes_service import obtener_paciente
from app.services.signos_vitales_service import registrar_signo_vital
from app.services.tipos_signos_vitales_service import obtener_tipo_signo_vital

# Piso de seguridad: SignoVitalCrear valida valor > 0 (Field(gt=0)). Sin
# este piso, el ruido aleatorio del patrón "ruido" podría alguna vez
# restar de más y generar un valor <= 0, que el schema rechazaría a
# mitad de la simulación.
VALOR_MINIMO_ABSOLUTO = Decimal("0.01")


def generar_serie_lineal(
    valor_inicial: Decimal, valor_final: Decimal, cantidad_pasos: int
) -> list[Decimal]:
    """
    Usamos interpolación lineal simple para repartir 'cantidad_pasos' valores
    equidistantes entre valor_inicial y valor_final (ambos incluidos).
    Ej: generar_serie(37.0, 40.0, 4) -> [37.0, 38.0, 39.0, 40.0]
    """
    paso = (valor_final - valor_inicial) / (cantidad_pasos - 1)
    return [valor_inicial + paso * i for i in range(cantidad_pasos)]


def generar_serie_zigzag(
    valor_inicial: Decimal, valor_final: Decimal, cantidad_pasos: int
) -> list[Decimal]:
    """
    Alterna entre valor_inicial y valor_final en cada paso (onda
    cuadrada, no una rampa gradual). Sirve para poner a prueba la
    deduplicación de alertas: el mismo tipo_signo+paciente puede cruzar
    el umbral de "normal" a "crítico" y volver, varias veces, en una
    sola simulación.
    """
    return [valor_inicial if i % 2 == 0 else valor_final for i in range(cantidad_pasos)]


def generar_serie_ruido(
    valor_inicial: Decimal,
    valor_final: Decimal,
    cantidad_pasos: int,
    amplitud: Decimal,
) -> list[Decimal]:
    """
    Toma la tendencia lineal como base y le suma un jitter aleatorio en
    cada paso (+/- amplitud), redondeado a 2 decimales para no romper
    la precisión de la columna Numeric(8,2). Simula un signo vital real,
    que nunca es una línea perfectamente recta.
    """
    tendencia = generar_serie_lineal(valor_inicial, valor_final, cantidad_pasos)

    serie_con_ruido = []
    for valor_base in tendencia:
        # random.uniform trabaja con float; lo pasamos por str() antes
        # de Decimal() para no arrastrar el error de precisión binaria
        # típico de convertir un float directo a Decimal.
        jitter = Decimal(str(random.uniform(-float(amplitud), float(amplitud))))
        valor_con_ruido = (valor_base + jitter).quantize(Decimal("0.01"))
        serie_con_ruido.append(max(valor_con_ruido, VALOR_MINIMO_ABSOLUTO))

    return serie_con_ruido


def generar_serie(
    valor_inicial: Decimal,
    valor_final: Decimal,
    cantidad_pasos: int,
    patron: PatronSimulacion,
    amplitud_ruido: Decimal,
) -> list[Decimal]:
    """
    Elige la función generadora según el patrón pedido. Se
    mantiene como un solo punto de entrada para no tener que tocar
    ejecutar_simulacion() cada vez que se agregue un patrón nuevo.
    """
    if patron == PatronSimulacion.zigzag:
        return generar_serie_zigzag(valor_inicial, valor_final, cantidad_pasos)

    if patron == PatronSimulacion.ruido:
        return generar_serie_ruido(
            valor_inicial, valor_final, cantidad_pasos, amplitud_ruido
        )

    return generar_serie_lineal(valor_inicial, valor_final, cantidad_pasos)


async def ejecutar_simulacion(
    paciente_id: uuid.UUID,
    tipo_signo_id: uuid.UUID,
    valores: list[Decimal],
    intervalo_segundos: int,
) -> None:
    """
    Esta función corre en segundo plano siendo disparada por BackgroundTasks.
    Por eso abre su PROPIA sesión con AsyncSessionLocal y no recibe la sesión del REQUEST.

    Reutiliza registrar_signo_vital() para cada valor, así cada medición
    simulada pasa por el mismo motor de detección y dispara los mismos
    workflows de Temporal que una medición real.
    """
    async with AsyncSessionLocal() as db:
        for valor in valores:
            datos = SignoVitalCrear(
                tipo_signo_id=tipo_signo_id,
                valor=valor,
                origen=OrigenMedicion.simulado,
            )
            try:
                await registrar_signo_vital(db, paciente_id, datos)
            except Exception as error:
                # Una BackgroundTask ya no tiene a quién devolverle un error HTTP (la respuesta ya se mandó).
                # Lo dejamos en consola y seguimos con el próximo valor.
                print(f"Error simulando medición para paciente {paciente_id}: {error}")

            if intervalo_segundos > 0:
                await asyncio.sleep(intervalo_segundos) # espera entre mediciones si es modo tiempo real


async def iniciar_simulacion(
    db: AsyncSession,
    background_tasks: BackgroundTasks,
    paciente_id: uuid.UUID,
    datos: SimulacionCrear,
) -> dict:
    """
    Valida que el paciente y el tipo de signo vital existan usando la
    sesión del request, genera la serie por interpolación, y
    programa la simulación como BackgroundTask.
    """
    await obtener_paciente(db, paciente_id)  # 404 si no existe
    await obtener_tipo_signo_vital(db, datos.tipo_signo_id)  # 404 si no existe

    valores = generar_serie(
        datos.valor_inicial,
        datos.valor_final,
        datos.cantidad_pasos,
        datos.patron,
        datos.amplitud_ruido,
    )

    background_tasks.add_task(
        ejecutar_simulacion,
        paciente_id,
        datos.tipo_signo_id,
        valores,
        datos.intervalo_segundos,
    )

    return {
        "mensaje": "Simulación iniciada en segundo plano.",
        "cantidad_mediciones": len(valores),
        "paciente_id": paciente_id,
        "tipo_signo_id": datos.tipo_signo_id,
        "intervalo_segundos": datos.intervalo_segundos,
        "patron": datos.patron,
    }
