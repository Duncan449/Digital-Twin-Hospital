import uuid
from datetime import datetime, timezone

from temporalio import activity


@activity.defn
async def generar_saludo(nombre: str) -> str:
    """
    Una Activity es el lugar donde pasan cosas "reales" con efectos
    secundarios: llamadas a APIs, escrituras en la base, envío de
    notificaciones, etc. Temporal la reintenta automáticamente si falla.

    Por ahora, solo simula un trabajo simple para probar la conexión.
    """
    activity.logger.info(f"Generando saludo para: {nombre}")
    return f"¡Hola, {nombre}! Este mensaje pasó por Temporal."


@activity.defn
async def marcar_alerta_normalizada(alerta_id: str) -> None:
    """
    Persiste en la base que el signo vital de esta alerta se sostuvo en
    "normal" el tiempo suficiente (ver AlertaWorkflow). Marca
    Alerta.severidad = normal y Alerta.normalizada_en = ahora.

    A propósito NO toca Alerta.estado: la alerta sigue "activa" (o
    "en_atencion" si el personal ya la estaba atendiendo) hasta que se
    registre una Intervencion -- normalizarse solo baja la urgencia
    clínica, no cierra el caso.

    Las Activities corren fuera del sandbox determinista del workflow,
    así que acá sí podemos hacer imports con efectos secundarios y abrir
    nuestra propia sesión de base (no compartimos la sesión de ningún
    request de FastAPI, que ya terminó hace rato).
    """
    # Imports acá adentro (no al tope del módulo) para no acoplar el
    # arranque del Worker de Temporal a que el resto de la app FastAPI
    # esté configurada exactamente igual; además evita imports circulares
    # entre `app` y `temporal`.
    from app.config.database import AsyncSessionLocal
    from app.models.clinico import Alerta
    from app.models.enums import NivelSeveridad

    async with AsyncSessionLocal() as db:
        alerta = await db.get(Alerta, uuid.UUID(alerta_id))
        if alerta is None:
            activity.logger.warning(
                f"marcar_alerta_normalizada: no existe la alerta {alerta_id} "
                "(¿se borró?). No hago nada."
            )
            return

        alerta.severidad = NivelSeveridad.normal
        alerta.normalizada_en = datetime.now(timezone.utc)
        await db.commit()

        activity.logger.info(f"Alerta {alerta_id} marcada como normalizada.")
