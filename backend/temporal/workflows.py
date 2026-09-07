import asyncio
from datetime import timedelta
from temporalio import workflow
from temporalio.common import RetryPolicy

with workflow.unsafe.imports_passed_through():
    from temporal.activities import generar_saludo, notificar_resolucion, registrar_escalacion


@workflow.defn
class SaludoWorkflow:
    """Workflow de prueba del hello world inicial. Se deja como referencia."""

    @workflow.run
    async def run(self, nombre: str) -> str:
        resultado = await workflow.execute_activity(
            generar_saludo,
            nombre,
            start_to_close_timeout=timedelta(seconds=10),
        )
        return resultado


# Intervalo corto a modo de prueba
INTERVALO_ESCALADO = timedelta(seconds=45)


@workflow.defn
class AlertaWorkflow:
    """Representa el ciclo de vida de UNA alerta, desde que se genera hasta
    que el personal registra que la atendió. Si nadie interviene dentro
    de INTERVALO_ESCALADO, escala repetidamente hasta que llegue el Signal."""

    def __init__(self) -> None:
        self._resuelta = False
        self._accion: str | None = None
        self._observaciones: str | None = None

    @workflow.signal
    def registrar_intervencion_finalizada(
        self, accion: str, observaciones: str | None = None
    ) -> None:
        self._accion = accion
        self._observaciones = observaciones
        self._resuelta = True

    @workflow.run
    async def run(self, alerta_id: str) -> str:
        workflow.logger.info(f"AlertaWorkflow iniciado para alerta {alerta_id}")

        # Mientras no llegue el Signal, esperamos con un límite de
        # tiempo. Si se cumple el límite (TimeoutError), escalamos y
        # volvemos a esperar -- por eso el "while not self._resuelta"
        # envolviendo todo: el loop se repite tantas veces como haga
        # falta hasta que finalmente llegue la intervención.
        while not self._resuelta:
            try:
                await workflow.wait_condition(
                    lambda: self._resuelta, timeout=INTERVALO_ESCALADO
                )
            except asyncio.TimeoutError:
                await workflow.execute_activity(
                    registrar_escalacion,
                    alerta_id,
                    start_to_close_timeout=timedelta(seconds=10),
                )
                # No hacemos "return" ni "break": el while vuelve a
                # evaluar la condición y arranca otra espera igual.

        resultado = await workflow.execute_activity(
            notificar_resolucion,
            args=[alerta_id, self._accion, self._observaciones],
            start_to_close_timeout=timedelta(seconds=10),
            retry_policy=RetryPolicy(
                initial_interval=timedelta(seconds=2),
                backoff_coefficient=2.0,
                maximum_interval=timedelta(seconds=30),
                maximum_attempts=5,
                non_retryable_error_types=["ValueError"],
            ),
        )
        return resultado