import uuid

from fastapi import APIRouter
from pydantic import BaseModel

from temporal.client import get_temporal_client
from temporal.workflows import AlertaWorkflow

router = APIRouter(prefix="/alertas", tags=["Alertas (prueba Temporal)"])

TASK_QUEUE = "hospital-task-queue"


@router.post("/prueba")
async def crear_alerta_prueba():
    """
    Dispara un AlertaWorkflow con un UUID generado al vuelo (sin tocar
    Postgres). Usamos start_workflow (no execute_workflow como en el script
    de prueba anterior) porque este SÍ necesita devolver la respuesta HTTP
    de inmediato, sin quedarse esperando a que alguien lo resuelva.
    """
    alerta_id = uuid.uuid4()
    client = await get_temporal_client()

    await client.start_workflow(
        AlertaWorkflow.run,
        str(alerta_id),
        id=str(alerta_id),
        task_queue=TASK_QUEUE,
    )

    return {
        "alerta_id": str(alerta_id),
        "mensaje": "Workflow iniciado, esperando intervención.",
    }


class IntervencionPrueba(BaseModel):
    accion: str
    observaciones: str | None = None


@router.post("/prueba/{alerta_id}/resolver")
async def resolver_alerta_prueba(alerta_id: str, datos: IntervencionPrueba):
    client = await get_temporal_client()
    handle = client.get_workflow_handle(alerta_id)

    # Con dos o más argumentos, hay que pasarlos agrupados en args=[...],
    # no como parámetros sueltos. El SDK internamente los "desempaqueta"
    # y se los pasa al método del Signal en orden.
    await handle.signal(
        AlertaWorkflow.registrar_intervencion_finalizada,
        args=[datos.accion, datos.observaciones],
    )

    return {"mensaje": "Signal enviado. El workflow debería resolverse."}