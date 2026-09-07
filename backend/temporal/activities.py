import uuid
from datetime import datetime, timezone

from temporalio import activity

from app.config.database import AsyncSessionLocal
from app.models.clinico import Alerta, Evento
from app.models.enums import EstadoAlerta, TipoEvento


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
    de Postgres requiere una migración de Alembic con ALTER TYPE. Si
    más adelante quisieran distinguir esto de forma más prolija en el
    dashboard, ahí es donde convendría sumar ese tipo nuevo.
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

    activity.logger.warning(f"Alerta {alerta_id} sin atender, escalando.")
    return f"Escalación registrada para alerta {alerta_id}."