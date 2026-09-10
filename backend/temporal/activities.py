import asyncio 
import uuid
from datetime import datetime, timezone
from decimal import Decimal

from temporalio import activity

from app.config.database import AsyncSessionLocal
from app.models.clinico import Alerta, Evento, TipoSignoVital
from app.models.enums import EstadoAlerta, TipoEvento
from app.websockets.eventos import publicar_evento


# Cuántos pasos y cuánto tiempo tarda la estabilización automática que se
# dispara tras resolver una alerta. Se mantiene corta a propósito: debe
# entrar cómoda dentro de VENTANA_SUPRESION_SEG (deteccion.py, 110s por
# defecto) para que ningún paso intermedio dispare una alerta nueva.
# 6 pasos x 15s = ~90s de margen real.
PASOS_ESTABILIZACION = 6
INTERVALO_ESTABILIZACION_SEG = 15

# Referencias a las Task de estabilización en curso.
_tareas_estabilizacion: set[asyncio.Task] = set()


async def _publicar_evento_seguro(paciente_id: str, tipo: str, data: dict) -> None:
    """
    Mismo wrapper que en signos_vitales_service.py, aísla los fallos de
    Redis para que NUNCA hagan fallar la Activity que los llama.
    """
    try:
        await publicar_evento(paciente_id=paciente_id, tipo=tipo, data=data)
    except Exception as error:
        print(
            f"No se pudo publicar el evento '{tipo}' en Redis (¿está caído?): {error}"
        )


async def _estabilizar_signo_vital(
    alerta_id: str,
    paciente_id: uuid.UUID,
    tipo_signo_id: uuid.UUID,
    valor_inicial: Decimal,
) -> None:
    """
    Simula el retorno gradual del signo vital a su rango normal tras una
    intervención, reutilizando el simulador existente (mismo motor de
    detección que cualquier medición real, vía ejecutar_simulacion).

    Corre desacoplada como su propia Task en vez de ser "esperada (await)" por notificar_resolucion, para no extender
    el tiempo de ejecución de esa Activity ni depender de su timeout
    configurado. Por eso mismo abre su propia sesión (indirectamente, a
    través de ejecutar_simulacion) y atrapa cualquier error acá.
    """
    try:
        # Import diferido para evitar dependencias circulares con simulador_service.py
        from app.services.simulador_service import (
            ejecutar_simulacion,
            generar_serie_lineal,
        )

        async with AsyncSessionLocal() as db:
            tipo_signo = await db.get(TipoSignoVital, tipo_signo_id)

        if tipo_signo is None:
            print(
                f"Estabilización omitida: no existe el tipo de signo {tipo_signo_id}."
            )
            return

        valor_final = (
            tipo_signo.rango_normal_min + tipo_signo.rango_normal_max
        ) / Decimal("2")

        valores = generar_serie_lineal(valor_inicial, valor_final, PASOS_ESTABILIZACION)

        await ejecutar_simulacion(
            paciente_id=paciente_id,
            tipo_signo_id=tipo_signo_id,
            valores=valores,
            intervalo_segundos=INTERVALO_ESTABILIZACION_SEG,
        )
    except Exception as error:
        print(
            f"No se pudo estabilizar el signo vital tras la alerta {alerta_id}: {error}"
        )


@activity.defn
async def generar_saludo(nombre: str) -> str:
    """Activity de prueba del hello world inicial. Se deja como referencia."""
    activity.logger.info(f"Generando saludo para: {nombre}")
    return f"¡Hola, {nombre}! Este mensaje pasó por Temporal."


@activity.defn
async def notificar_resolucion(alerta_id: str, accion: str, observaciones: str | None) -> str:
    """Marca la alerta como resuelta en Postgres."""
    async with AsyncSessionLocal() as db:
        alerta = await db.get(Alerta, uuid.UUID(alerta_id))
        if alerta is None:
            raise ValueError(f"No existe una alerta con id '{alerta_id}'.")

        alerta.estado = EstadoAlerta.resuelta
        alerta.resuelta_en = datetime.now(timezone.utc)
        await db.commit()

        # Publicamos DESPUÉS del commit, con los datos ya confirmados.
        # Este es el evento que hace visible en vivo que el sistema se
        # recuperó tras la intervención, incluso si el Worker se había
        # caído y recién ahora retomó el Workflow.
        await _publicar_evento_seguro(
            paciente_id=str(alerta.paciente_id),
            tipo="alerta_resuelta",
            data={
                "alerta_id": alerta_id,
                "accion": accion,
                "observaciones": observaciones,
            },
        )

        # Estabilización automática con mejor esfuerzo, no bloqueante. 
        if alerta.tipo_signo_id is not None and alerta.valor_detectado is not None:
            tarea = asyncio.create_task(
                _estabilizar_signo_vital(
                    alerta_id=alerta_id,
                    paciente_id=alerta.paciente_id,
                    tipo_signo_id=alerta.tipo_signo_id,
                    valor_inicial=alerta.valor_detectado,
                )
            )
            _tareas_estabilizacion.add(tarea)
            tarea.add_done_callback(_tareas_estabilizacion.discard)

    activity.logger.info(f"Alerta {alerta_id} resuelta en Postgres.")
    return f"Alerta {alerta_id} marcada como resuelta."


@activity.defn
async def registrar_escalacion(alerta_id: str) -> str:
    """
    Se ejecuta cuando pasa el tiempo límite sin que nadie intervenga.
    Deja un registro en 'eventos' -- así queda visible en el historial
    del paciente/dashboard que esta alerta lleva tiempo sin atenderse.

    Reutilizamos TipoEvento.alerta_actualizada en vez de crear un tipo
    nuevo (como 'alerta_escalada'), porque agregar un valor a un ENUM
    de Postgres requiere una migración de Alembic con ALTER TYPE.
    """
    async with AsyncSessionLocal() as db:
        alerta = await db.get(Alerta, uuid.UUID(alerta_id))
        if alerta is None:
            raise ValueError(f"No existe una alerta con id '{alerta_id}'.")

        evento = Evento(
            paciente_id=alerta.paciente_id,
            tipo=TipoEvento.alerta_actualizada,
            descripcion="Alerta sin atender: se escala la notificación al personal.",
            severidad=alerta.severidad,
        )
        db.add(evento)
        await db.commit()
        
        await _publicar_evento_seguro(
            paciente_id=str(alerta.paciente_id),
            tipo="alerta_escalada",
            data={"alerta_id": alerta_id, "severidad": alerta.severidad.value},
        )

    activity.logger.warning(f"Alerta {alerta_id} sin atender, escalando.")
    return f"Escalación registrada para alerta {alerta_id}."
