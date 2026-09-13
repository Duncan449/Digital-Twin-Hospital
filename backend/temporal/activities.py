import uuid
from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from temporalio import activity

from app.config.database import AsyncSessionLocal
from app.models.clinico import Alerta, Evento, TipoSignoVital
from app.models.enums import EstadoAlerta, OrigenMedicion, TipoEvento
from app.models.pacientes import DigitalTwin
from app.schemas.signos_vitales import SignoVitalCrear
from app.services.deteccion import _calcular_severidad_actual_paciente
from app.websockets.eventos import publicar_evento


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

@activity.defn
async def generar_saludo(nombre: str) -> str:
    """Activity de prueba del hello world inicial. Se deja como referencia."""
    activity.logger.info(f"Generando saludo para: {nombre}")
    return f"¡Hola, {nombre}! Este mensaje pasó por Temporal."


@activity.defn
async def registrar_escalacion(alerta_id: str, nivel: int) -> str:
    """
    Se ejecuta cuando pasa el tiempo límite sin que nadie intervenga.
    Deja un registro en 'eventos' así queda visible en el historial
    del paciente/dashboard que esta alerta lleva tiempo sin atenderse.

    Reutilizamos TipoEvento.alerta_actualizada en vez de crear un tipo
    nuevo (como 'alerta_escalada'), porque agregar un valor a un ENUM
    de Postgres requiere una migración de Alembic con ALTER TYPE.
    """
    async with AsyncSessionLocal() as db:
        alerta = await db.get(Alerta, uuid.UUID(alerta_id))
        if alerta is None:
            raise ValueError(f"No existe una alerta con id '{alerta_id}'.")

        db.add(
            Evento(
                paciente_id=alerta.paciente_id,
                tipo=TipoEvento.alerta_actualizada,
                descripcion=f"Alerta sin atender (escalación nivel {nivel}): se notifica de nuevo al personal.",
                severidad=alerta.severidad,
            )
        )
        await db.commit()

        await _publicar_evento_seguro(
            paciente_id=str(alerta.paciente_id),
            tipo="alerta_escalada",
            data={"alerta_id": alerta_id, "nivel": nivel, "severidad": alerta.severidad.value},
        )

    activity.logger.warning(f"Alerta {alerta_id} escalada a nivel {nivel}.")
    return f"Escalación nivel {nivel} registrada para alerta {alerta_id}."


@activity.defn
async def marcar_alerta_resuelta(
    alerta_id: str, accion: str, observaciones: str | None
) -> dict:
    """
    Persiste la resolución en Postgres y recalcula el Digital Twin.
    """
    async with AsyncSessionLocal() as db:
        alerta = await db.get(Alerta, uuid.UUID(alerta_id))
        if alerta is None:
            raise ValueError(f"No existe una alerta con id '{alerta_id}'.")

        alerta.estado = EstadoAlerta.resuelta
        alerta.resuelta_en = datetime.now(timezone.utc)

        # El twin no salta a "normal" de golpe: se queda en la
        # severidad real hasta que la estabilización lo baje paso a paso.
        digital_twin = await db.scalar(
            select(DigitalTwin)
            .where(DigitalTwin.paciente_id == alerta.paciente_id)
            .with_for_update()
        )
        if digital_twin is not None:
            nueva_severidad_twin = await _calcular_severidad_actual_paciente(
                db, alerta.paciente_id
            )
            if digital_twin.severidad_actual != nueva_severidad_twin:
                digital_twin.severidad_actual = nueva_severidad_twin

        tipo_signo = None
        if alerta.tipo_signo_id is not None:
            tipo_signo = await db.get(TipoSignoVital, alerta.tipo_signo_id)

        paciente_id = alerta.paciente_id
        tipo_signo_id = alerta.tipo_signo_id
        valor_inicial = alerta.valor_detectado

        await db.commit()

        await _publicar_evento_seguro(
            paciente_id=str(paciente_id),
            tipo="alerta_resuelta",
            data={
                "alerta_id": alerta_id,
                "accion": accion,
                "observaciones": observaciones,
            },
        )

    activity.logger.info(f"Alerta {alerta_id} resuelta en Postgres.")

    if tipo_signo is None or valor_inicial is None:
        return {"paciente_id": str(paciente_id), "tipo_signo_id": None}

    valor_objetivo = (
        tipo_signo.rango_normal_min + tipo_signo.rango_normal_max
    ) / Decimal("2")
    return {
        "paciente_id": str(paciente_id),
        "tipo_signo_id": str(tipo_signo_id),
        "valor_inicial": str(valor_inicial),
        "valor_objetivo": str(valor_objetivo),
    }


@activity.defn
async def aplicar_paso_estabilizacion(
    paciente_id: str, tipo_signo_id: str, valor: str
) -> None:
    """
    UN paso de la rampa de estabilización. Reutiliza registrar_signo_vital,
    el mismo motor de detección que cualquier medición real, así el
    paso queda en el historial (Evento). 
    Cada paso es su propia Activity: si el Worker se cae a mitad de la rampa,
    Temporal retoma exactamente en el paso que faltaba.
    """

    from app.services.signos_vitales_service import registrar_signo_vital

    datos = SignoVitalCrear(
        tipo_signo_id=uuid.UUID(tipo_signo_id),
        valor=Decimal(valor),
        origen=OrigenMedicion.simulado,
    )
    async with AsyncSessionLocal() as db:
        await registrar_signo_vital(db, uuid.UUID(paciente_id), datos)
