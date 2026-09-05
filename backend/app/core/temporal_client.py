"""
Puente entre la app FastAPI y Temporal para el ciclo de vida de las
Alertas (ver temporal/workflows.py::AlertaWorkflow).

Filosofía: Temporal orquesta la temporización de la normalización, pero
Postgres sigue siendo la única fuente de verdad. Si el Temporal Server o
el Worker están caídos, un request de signos vitales o de intervención
NO debe fallar por eso -- en el peor caso, esa alerta puntual se queda
sin auto-normalizar hasta que el Worker vuelva, pero el resto del
sistema (mediciones, alertas, intervenciones manuales) sigue andando.
Por eso todas las funciones acá son "best effort": capturan cualquier
excepción, la loguean, y devuelven sin romper al que las llamó.
"""

import logging

from temporalio.client import Client

from app.config.config import settings
from temporal.shared import TASK_QUEUE
from temporal.workflows import AlertaWorkflow

logger = logging.getLogger(__name__)

_client: Client | None = None


async def get_temporal_client() -> Client:
    """
    Conexión perezosa y compartida: la primera vez que hace falta un
    cliente de Temporal en el proceso de FastAPI, se conecta una sola
    vez y se reutiliza para todos los requests siguientes (igual que el
    engine de SQLAlchemy en app/config/database.py).
    """
    global _client
    if _client is None:
        _client = await Client.connect(settings.temporal_host, namespace="default")
    return _client


async def iniciar_alerta_workflow(
    workflow_id: str, alerta_id: str, severidad_inicial: str
) -> None:
    """
    Arranca el AlertaWorkflow para una Alerta recién creada. Se llama
    DESPUÉS de que la medición + el evento + la alerta ya se
    comiteraron en Postgres (nunca antes, para no arrancar un workflow
    correlacionado con una fila que después termina no existiendo por
    un rollback).
    """
    try:
        client = await get_temporal_client()
        await client.start_workflow(
            AlertaWorkflow.run,
            args=[alerta_id, severidad_inicial],
            id=workflow_id,
            task_queue=TASK_QUEUE,
        )
    except Exception:
        logger.exception(
            "No se pudo iniciar el AlertaWorkflow (alerta_id=%s, workflow_id=%s). "
            "La alerta se creó igual; solo no se va a auto-normalizar hasta "
            "que Temporal esté disponible.",
            alerta_id,
            workflow_id,
        )


async def senalizar_alerta_workflow(workflow_id: str | None, severidad: str) -> None:
    """
    Le avisa al AlertaWorkflow en curso que llegó una medición nueva
    para esa alerta, con su severidad calculada. Esto es lo que resetea
    (o arranca) la cuenta regresiva de 10 segundos de normalidad
    sostenida dentro del workflow.
    """
    if not workflow_id:
        return
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(AlertaWorkflow.nueva_medicion, severidad)
    except Exception:
        logger.exception(
            "No se pudo señalizar nueva_medicion al workflow %s.", workflow_id
        )


async def resolver_alerta_workflow(workflow_id: str | None) -> None:
    """
    Le avisa al AlertaWorkflow que la alerta se resolvió (se registró
    una Intervencion), para que termine en vez de quedar esperando para
    siempre.
    """
    if not workflow_id:
        return
    try:
        client = await get_temporal_client()
        handle = client.get_workflow_handle(workflow_id)
        await handle.signal(AlertaWorkflow.intervencion_registrada)
    except Exception:
        logger.exception(
            "No se pudo señalizar intervencion_registrada al workflow %s.",
            workflow_id,
        )
