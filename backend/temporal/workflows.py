import asyncio
from datetime import timedelta
from decimal import Decimal

from temporalio import workflow
from temporalio.common import RetryPolicy
from temporalio.exceptions import ActivityError

from app.utils.series import generar_serie_lineal

with workflow.unsafe.imports_passed_through():
    from temporal.activities import (
        aplicar_paso_estabilizacion,
        generar_saludo,
        marcar_alerta_resuelta,
        registrar_escalacion,
    )

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

# Pasos y cadencia de la estabilización post-intervención. 6 x 15s = ~90s,
# debe entrar dentro de VENTANA_SUPRESION_SEG (deteccion.py, 110s).
PASOS_ESTABILIZACION = 6
INTERVALO_ESTABILIZACION_SEG = 15

@workflow.defn
class AlertaWorkflow:
    """Representa el ciclo de vida de UNA alerta, desde que se genera hasta
    que el personal registra que la atendió. Si nadie interviene dentro
    de INTERVALO_ESCALADO, escala repetidamente hasta que llegue el Signal.
    Se encarga también de la resoulción y la estabilización del paciente tras la intervención."""

    def __init__(self) -> None:
        self._fase = "esperando_intervencion"
        self._nivel_escalacion = 0
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

    @workflow.query
    def estado_actual(self) -> dict:
        """
        Consultada por el panel de Fase 6. Devuelve el estado VIVO del
        workflow -- lo sirve Temporal desde su historial persistido,
        así que responde igual aunque el worker esté caído en este
        momento. Es la prueba más directa de que el progreso no
        depende de que haya un proceso corriendo ahora mismo.
        """
        return {"fase": self._fase, "nivel_escalacion": self._nivel_escalacion}

    @workflow.run
    async def run(self, alerta_id: str) -> str:
        workflow.logger.info(f"AlertaWorkflow iniciado para alerta {alerta_id}")
        # Fase 1: espera de intervención. Si no llega, escala y vuelve a esperar.
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
                self._nivel_escalacion += 1
                self._fase = "escalando"
                await workflow.execute_activity(
                    registrar_escalacion,
                    args=[alerta_id, self._nivel_escalacion],
                    start_to_close_timeout=timedelta(seconds=10),
                )
                self._fase = "esperando_intervencion"
                # No hacemos "return" ni "break": el while vuelve a
                # evaluar la condición y arranca otra espera igual.

        # Fase 2: intervención registrada. Marcamos la alerta como resuelta.
        self._fase = "resolviendo"
        datos = await workflow.execute_activity(
            marcar_alerta_resuelta,
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

        # Fase 3: estabilización del paciente tras la intervención.
        if datos["tipo_signo_id"] is not None:
            self._fase = "estabilizando"
            valores = generar_serie_lineal(
                Decimal(datos["valor_inicial"]),
                Decimal(datos["valor_objetivo"]),
                PASOS_ESTABILIZACION,
            )
            for i, valor in enumerate(valores):
                try:
                    await workflow.execute_activity(
                        aplicar_paso_estabilizacion,
                        args=[datos["paciente_id"], datos["tipo_signo_id"], str(valor)],
                        start_to_close_timeout=timedelta(seconds=10),
                        retry_policy=RetryPolicy(maximum_attempts=3),
                    )
                except ActivityError as error:
                    # Best-effort, un paso fallido no debe frenar el
                    # resto de la rampa ni el cierre del workflow.
                    workflow.logger.warning(
                        f"Paso {i + 1}/{PASOS_ESTABILIZACION} de estabilización falló: {error}"
                    )
                if i < len(valores) - 1:
                    await asyncio.sleep(INTERVALO_ESTABILIZACION_SEG)

        self._fase = "resuelta"
        return f"Alerta {alerta_id} resuelta y estabilizada."
