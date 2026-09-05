import asyncio
from datetime import timedelta
from temporalio import workflow

# Con Temporal, las Activities se importan dentro de un bloque especial
# (unsafe.imports_passed_through) porque el Workflow corre en un entorno
# "sandboxed" y determinista: no puede importar código con efectos
# secundarios directamente, solo puede *invocar* Activities a través del
# motor de Temporal.
with workflow.unsafe.imports_passed_through():
    from temporal.activities import generar_saludo, marcar_alerta_normalizada


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


# Cuántos segundos tiene que sostenerse una medición en "normal" (sin que
# llegue ninguna medición fuera de rango en el medio) para que la alerta
# se considere normalizada. Constante acá porque la usa únicamente este
# workflow -- si algún día hace falta configurarla por tipo de signo vital,
# pasaría a ser un argumento de `run`.
SEGUNDOS_NORMALIDAD_SOSTENIDA = 10


@workflow.defn
class AlertaWorkflow:
    """
    Un workflow por cada Alerta activa (correlacionado vía
    Alerta.workflow_id_temporal == este workflow_id).

    Responsabilidad ÚNICA de este workflow: decidir cuándo el signo vital
    que originó la alerta "se normalizó" (severidad == normal sostenida
    SEGUNDOS_NORMALIDAD_SOSTENIDA segundos seguidos, sin ninguna medición
    fuera de rango en el medio) y, en ese caso, disparar la Activity que
    lo persiste en la base (Alerta.severidad = normal, normalizada_en =
    ahora).

    A propósito NO cierra la alerta ni la marca "resuelta": eso sigue
    dependiendo exclusivamente de que el personal médico registre una
    Intervencion (endpoint POST /alertas/{id}/intervenciones), que es
    quien nos avisa via la señal `intervencion_registrada` para que el
    workflow termine.

    Todo el estado que necesita ("¿cuál es la severidad más reciente?",
    "¿ya se resolvió?") vive en atributos de instancia actualizados por
    señales -- es el patrón estándar de Temporal para reaccionar a
    eventos externos sin tener que ir a buscarlos a una base de datos
    desde adentro del workflow (lo cual rompería el determinismo).
    """

    def __init__(self) -> None:
        self._severidad_actual: str = "critica"
        self._resuelta: bool = False

    @workflow.signal
    def nueva_medicion(self, severidad: str) -> None:
        """
        Señal disparada por la app cada vez que llega una medición nueva
        para el mismo paciente + tipo de signo mientras la alerta sigue
        abierta. Si la severidad vuelve a no ser "normal", esto corta
        cualquier cuenta regresiva de normalización en curso.
        """
        self._severidad_actual = severidad

    @workflow.signal
    def intervencion_registrada(self) -> None:
        """
        Señal disparada cuando el personal registra la Intervencion que
        cierra la alerta. A partir de acá el workflow ya no tiene nada
        más que hacer y termina.
        """
        self._resuelta = True

    @workflow.run
    async def run(self, alerta_id: str, severidad_inicial: str) -> None:
        self._severidad_actual = severidad_inicial

        while not self._resuelta:
            if self._severidad_actual != "normal":
                # Severidad activa (precaución o crítica): no hay nada que
                # temporizar, solo esperamos a que algo cambie -- ya sea
                # que la severidad mejore a "normal" o que se registre la
                # intervención directamente sin pasar por "normal" (ej:
                # el personal interviene mientras el paciente sigue mal).
                await workflow.wait_condition(
                    lambda: self._severidad_actual == "normal" or self._resuelta
                )
                continue

            # severidad_actual == "normal": arrancamos (o reiniciamos) la
            # cuenta regresiva de SEGUNDOS_NORMALIDAD_SOSTENIDA. Si en el
            # medio cambia la severidad o se resuelve la alerta,
            # wait_condition devuelve True ANTES del timeout y volvemos
            # al principio del loop sin marcar nada como normalizado.
            try:
                await workflow.wait_condition(
                    lambda: self._severidad_actual != "normal" or self._resuelta,
                    timeout=timedelta(seconds=SEGUNDOS_NORMALIDAD_SOSTENIDA),
                )
                continue
            except asyncio.TimeoutError:
                # Se sostuvo "normal" el tiempo completo sin interrupciones.
                if not self._resuelta and self._severidad_actual == "normal":
                    await workflow.execute_activity(
                        marcar_alerta_normalizada,
                        alerta_id,
                        start_to_close_timeout=timedelta(seconds=15),
                    )
                # La alerta ya está normalizada pero sigue pendiente de
                # revisión humana: esperamos indefinidamente a que se
                # resuelva (o a que el signo empeore de nuevo, en cuyo
                # caso el loop vuelve a vigilar la severidad activa).
                await workflow.wait_condition(
                    lambda: self._severidad_actual != "normal" or self._resuelta
                )
                continue
