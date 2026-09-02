import asyncio
from temporalio.client import Client
from temporalio.worker import Worker

from temporal.activities import generar_saludo
from temporal.workflows import SaludoWorkflow

# Nombre de la "cola de tareas". Es como un canal: el Client publica
# workflows en esta cola, y solo los Workers suscriptos a la misma cola
# los recogen. Nos va a servir más adelante para separar, por ejemplo,
# una cola de "alertas" de una cola de "notificaciones".
TASK_QUEUE = "hospital-task-queue"


async def main():
    # Se conecta al Temporal Server que levantamos con Docker,
    # en el puerto 7233 (el gRPC que expusimos en el docker-compose.yml)
    client = await Client.connect("localhost:7233", namespace="default")

    # El Worker queda "escuchando" la task queue, listo para ejecutar
    # cualquier Workflow o Activity que le llegue. Este proceso corre
    # de forma indefinida hasta que lo detengas manualmente (Ctrl+C).
    worker = Worker(
        client,
        task_queue=TASK_QUEUE,
        workflows=[SaludoWorkflow],
        activities=[generar_saludo],
    )

    print(f"Worker escuchando en la cola '{TASK_QUEUE}'... (Ctrl+C para salir)")
    await worker.run()


if __name__ == "__main__":
    asyncio.run(main())