from datetime import timedelta
from temporalio import workflow

with workflow.unsafe.imports_passed_through():
    from temporal.activities import generar_saludo, notificar_resolucion


@workflow.defn
class SaludoWorkflow:
    """Workflow de prueba del hello world inicial. Lo dejamos como referencia."""

    @workflow.run
    async def run(self, nombre: str) -> str:
        resultado = await workflow.execute_activity(
            generar_saludo,
            nombre,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return resultado


@workflow.defn
class AlertaWorkflow:
    """
    Representa el ciclo de vida de UNA alerta, desde que se genera hasta
    que el personal registra que la atendió. A diferencia de SaludoWorkflow,
    este NO termina apenas ejecuta una activity: se queda "pausado" (sin
    consumir recursos, Temporal lo persiste) hasta recibir un Signal.
    """

    def __init__(self) -> None:
        # Este estado vive en la memoria del workflow mientras corre, y
        # Temporal lo reconstruye automáticamente si el Worker se reinicia
        # (por eso más adelante la demo de tolerancia a fallos funciona).
        self._resuelta = False
        self._accion: str | None = None
        self._observaciones: str | None = None

    @workflow.signal
    def registrar_intervencion_finalizada(
        self, accion: str, observaciones: str | None = None
    ) -> None:
        """
        Un Signal es la única forma de "hablarle" a un workflow que ya está
        corriendo. Se ejecuta de forma determinista entre pasos del workflow:
        acá solo guardamos los datos y cambiamos una bandera, no hacemos
        trabajo pesado (eso es tarea de las activities).
        """
        self._accion = accion
        self._observaciones = observaciones
        self._resuelta = True

    @workflow.run
    async def run(self, alerta_id: str) -> str:
        workflow.logger.info(f"AlertaWorkflow iniciado para alerta {alerta_id}")

        # wait_condition pausa el workflow hasta que la lambda devuelva True.
        # No es un "while" que consume CPU: Temporal literalmente suspende
        # la ejecución y la retoma sola apenas el Signal cambia self._resuelta.
        await workflow.wait_condition(lambda: self._resuelta)

        resultado = await workflow.execute_activity(
            notificar_resolucion,
            args=[alerta_id, self._accion, self._observaciones],
            start_to_close_timeout=timedelta(seconds=10),
        )
        return resultado