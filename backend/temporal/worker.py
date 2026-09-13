import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from temporal.activities import (
    aplicar_paso_estabilizacion,
    generar_saludo,
    marcar_alerta_resuelta,
    registrar_escalacion,
)
from temporal.workflows import AlertaWorkflow, SaludoWorkflow

TASK_QUEUE = "hospital-task-queue"


async def main():
    client = await Client.connect("localhost:7233", namespace="default")

    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[SaludoWorkflow, AlertaWorkflow],
        activities=[
            generar_saludo,
            marcar_alerta_resuelta,
            registrar_escalacion,
            aplicar_paso_estabilizacion,
        ],
    )

    print(f"Worker escuchando en la cola '{TASK_QUEUE}'... (Ctrl+C para salir)")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())
