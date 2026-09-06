from datetime import timedelta
from temporalio import workflow

# Con Temporal, las Activities se importan dentro de un bloque especial
# (unsafe.imports_passed_through) porque el Workflow corre en un entorno
# "sandboxed" y determinista: no puede importar código con efectos
# secundarios directamente, solo puede *invocar* Activities a través del
# motor de Temporal.
with workflow.unsafe.imports_passed_through():
    from temporal.activities import generar_saludo


@workflow.defn
class SaludoWorkflow:
    """
    Un Workflow es la orquestación: define QUÉ pasos siguen y en qué orden,
    pero no ejecuta trabajo "real" él mismo — delega eso a las Activities.

    La gracia de esto es que si el Worker se cae en medio de la ejecución,
    Temporal sabe exactamente en qué paso se quedó (gracias al historial
    que guarda en su Postgres interno) y lo retoma solo, sin que vos
    tengas que programar esa lógica de recuperación a mano.
    """

    @workflow.run
    async def run(self, nombre: str) -> str:
        resultado = await workflow.execute_activity(
            generar_saludo,
            nombre,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return resultado