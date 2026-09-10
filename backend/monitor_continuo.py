"""
Script standalone que mantiene "vivo"
el Dashboard durante la demo: genera mediciones continuas para todos los
pacientes activos y todos los tipos de signos vitales del catálogo,
alternando entre dos estados por cada par (paciente, tipo_signo):

  - "normal": ruido chico alrededor del punto medio del rango normal.
  - "deteriorando" -> "esperando": camina hacia (y más allá) del límite
    crítico, se queda ahí esperando una intervención, y vuelve a
    "normal" cuando la alerta correspondiente se resuelve.

El deterioro se dispara de dos formas:
  - Espontánea: cada par tiene una probabilidad chica de arrancar un
    deterioro en cada tick, mientras está en "normal".
  - Manual: un POST a /pacientes/{id}/signos-vitales/{tipo_signo_id}/deteriorar
    (el botón del frontend) publica un comando por Redis que este script
    escucha en tiempo real.

El catálogo de tipos de signos y la lista de pacientes se piden
dinámicamente a la API al arrancar 

Corre como un proceso aparte, en paralelo a uvicorn y al Worker de
Temporal. Se lanza a mano: `python monitor_continuo.py` desde backend/.
"""

import asyncio
import json
import random
import time
import uuid
from dataclasses import dataclass

import httpx

from app.config.redis_client import get_redis_client
from app.websockets.eventos import CANAL_EVENTOS

BASE_URL = "http://localhost:8000"

# --- Parámetros ajustables de la simulación ---
INTERVALO_TICK_SEG = 15  # cada cuánto se postea una medición nueva, por par
FRACCION_RUIDO_NORMAL = 0.12  # +/- sobre el ancho del rango normal, en estado "normal"
FRACCION_AVANCE_DETERIORO = (
    0.35  # qué tan rápido camina hacia el objetivo (proporcional)
)
PROBABILIDAD_DETERIORO_ESPONTANEO = 0.003  # por tick, solo en estado "normal"
PAUSA_POST_RESOLUCION_SEG = (
    95  # margen para no pisar la estabilización automática de Temporal
)


@dataclass
class EstadoPar:
    paciente_id: str
    paciente_nombre: str
    tipo_signo_id: str
    tipo_signo_nombre: str
    rango_normal_min: float
    rango_normal_max: float
    rango_critico_min: float
    rango_critico_max: float
    valor_actual: float
    estado: str = "normal"  # normal | deteriorando | esperando | pausado
    objetivo: float = 0.0
    reanudar_en: float = 0.0  # timestamp (time.monotonic()) hasta el que queda pausado


def _arrancar_deterioro(par: EstadoPar) -> None:
    '''
    Cambia el estado a "deteriorando" y define un objetivo fuera del rango normal, hacia arriba o hacia abajo. Se llama desde el loop de cada par
    (espontáneo) o desde el listener de comandos (manual).'''
    direccion_arriba = random.choice([True, False])
    if direccion_arriba:
        margen = max(par.rango_critico_max - par.rango_normal_max, 0.1)
        par.objetivo = par.rango_critico_max + margen * 0.5
    else:
        margen = max(par.rango_normal_min - par.rango_critico_min, 0.1)
        par.objetivo = par.rango_critico_min - margen * 0.5

    par.estado = "deteriorando"
    print(
        f"[{par.paciente_nombre} / {par.tipo_signo_nombre}] arranca deterioro "
        f"hacia {'arriba' if direccion_arriba else 'abajo'}."
    )


def _tick_normal(par: EstadoPar) -> float:
    amplitud = (par.rango_normal_max - par.rango_normal_min) * FRACCION_RUIDO_NORMAL
    nuevo = par.valor_actual + random.uniform(-amplitud, amplitud)
    return min(max(nuevo, par.rango_normal_min), par.rango_normal_max)


def _tick_deteriorando(par: EstadoPar) -> float:
    return (
        par.valor_actual + (par.objetivo - par.valor_actual) * FRACCION_AVANCE_DETERIORO
    )


def _tick_esperando(par: EstadoPar) -> float:
    # jitter chico alrededor del valor crítico actual, sin seguir alejándose
    amplitud = abs(par.rango_critico_max - par.rango_critico_min) * 0.02
    return par.valor_actual + random.uniform(-amplitud, amplitud)


async def _postear_medicion(
    cliente: httpx.AsyncClient, par: EstadoPar, valor: float
) -> str | None:
    try:
        respuesta = await cliente.post(
            f"{BASE_URL}/pacientes/{par.paciente_id}/signos-vitales",
            json={
                "tipo_signo_id": par.tipo_signo_id,
                "valor": round(valor, 2),
                "origen": "simulado",
            },
        )
        respuesta.raise_for_status()
        return respuesta.json()["severidad_calculada"]
    except Exception as error:
        print(
            f"Error posteando medición [{par.paciente_nombre}/{par.tipo_signo_nombre}]: {error}"
        )
        return None


async def _loop_par(cliente: httpx.AsyncClient, par: EstadoPar) -> None:
    """Un loop infinito e independiente por cada (paciente, tipo_signo)."""
    while True:
        await asyncio.sleep(INTERVALO_TICK_SEG)
        ahora = time.monotonic()

        if par.estado == "pausado":
            if ahora < par.reanudar_en:
                continue
            par.estado = "normal"

        if par.estado == "normal":
            if random.random() < PROBABILIDAD_DETERIORO_ESPONTANEO:
                _arrancar_deterioro(par)
            nuevo_valor = _tick_normal(par)
        elif par.estado == "deteriorando":
            nuevo_valor = _tick_deteriorando(par)
        else:  # "esperando"
            nuevo_valor = _tick_esperando(par)

        severidad = await _postear_medicion(cliente, par, nuevo_valor)
        if severidad is None:
            continue  # el POST falló, no actualizamos valor_actual con un dato no confirmado

        par.valor_actual = nuevo_valor

        if par.estado == "deteriorando" and severidad == "critica":
            par.estado = "esperando"
            print(
                f"[{par.paciente_nombre} / {par.tipo_signo_nombre}] llegó a crítico, esperando intervención."
            )


async def _resolver_par_por_alerta(
    cliente: httpx.AsyncClient,
    pares: dict[tuple[str, str], EstadoPar],
    paciente_id: str,
    alerta_id: str,
) -> None:
    """
    El evento 'alerta_resuelta' solo trae el alerta_id para saber a
    qué tipo_signo corresponde (y así encontrar el par en nuestro dict),
    consultamos GET /alertas/{id}.
    """
    try:
        respuesta = await cliente.get(f"{BASE_URL}/alertas/{alerta_id}")
        respuesta.raise_for_status()
        tipo_signo_id = respuesta.json()["tipo_signo_id"]
    except Exception as error:
        print(
            f"No se pudo resolver a qué signo corresponde la alerta {alerta_id}: {error}"
        )
        return

    par = pares.get((paciente_id, tipo_signo_id))
    if par is None:
        return

    par.estado = "pausado"
    par.reanudar_en = time.monotonic() + PAUSA_POST_RESOLUCION_SEG
    par.valor_actual = (par.rango_normal_min + par.rango_normal_max) / 2
    print(
        f"[{par.paciente_nombre} / {par.tipo_signo_nombre}] alerta resuelta, "
        f"pausado {PAUSA_POST_RESOLUCION_SEG}s antes de volver a 'normal'."
    )


async def _escuchar_comandos(
    cliente: httpx.AsyncClient, pares: dict[tuple[str, str], EstadoPar]
) -> None:
    """
    Una sola suscripción a Redis cubre los dos casos: el comando de
    deterioro manual (botón del frontend) y la detección de que una
    alerta se resolvió (para saber cuándo volver a 'normal'). Ambos
    viajan por el mismo canal que ya usa publicar_evento().
    """
    cliente_redis = await get_redis_client()
    pubsub = cliente_redis.pubsub()
    await pubsub.subscribe(CANAL_EVENTOS)

    async for mensaje in pubsub.listen():
        if mensaje["type"] != "message":
            continue
        try:
            evento = json.loads(mensaje["data"])
        except (TypeError, ValueError):
            continue

        paciente_id = evento.get("paciente_id")
        tipo = evento.get("tipo")
        data = evento.get("data", {})

        if tipo == "comando_deterioro":
            par = pares.get((paciente_id, data.get("tipo_signo_id")))
            if par is not None and par.estado in ("normal", "pausado"):
                _arrancar_deterioro(par)

        elif tipo == "alerta_resuelta":
            await _resolver_par_por_alerta(
                cliente, pares, paciente_id, data.get("alerta_id")
            )


async def _cargar_pares(cliente: httpx.AsyncClient) -> dict[tuple[str, str], EstadoPar]:
    pacientes = (await cliente.get(f"{BASE_URL}/pacientes")).json()
    tipos = (await cliente.get(f"{BASE_URL}/tipos-signos-vitales")).json()

    pares: dict[tuple[str, str], EstadoPar] = {}
    for paciente in pacientes:  
        for tipo in tipos:
            rango_normal_min = float(tipo["rango_normal_min"])
            rango_normal_max = float(tipo["rango_normal_max"])
            pares[(paciente["id"], tipo["id"])] = EstadoPar(
                paciente_id=paciente["id"],
                paciente_nombre=f"{paciente['nombre']} {paciente['apellido']}",
                tipo_signo_id=tipo["id"],
                tipo_signo_nombre=tipo["nombre"],
                rango_normal_min=rango_normal_min,
                rango_normal_max=rango_normal_max,
                rango_critico_min=float(tipo["rango_critico_min"]),
                rango_critico_max=float(tipo["rango_critico_max"]),
                valor_actual=(rango_normal_min + rango_normal_max) / 2,
            )
    return pares


async def main() -> None:
    async with httpx.AsyncClient(timeout=10.0) as cliente:
        pares = await _cargar_pares(cliente)
        print(
            f"Monitoreando {len(pares)} pares (paciente, tipo_signo). Ctrl+C para salir."
        )

        tareas = [
            asyncio.create_task(_loop_par(cliente, par)) for par in pares.values()
        ]
        tareas.append(asyncio.create_task(_escuchar_comandos(cliente, pares)))

        await asyncio.gather(*tareas)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nMonitor detenido.")
