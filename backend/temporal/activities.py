from temporalio import activity


@activity.defn
async def generar_saludo(nombre: str) -> str:
    """Activity de prueba del hello world inicial. La dejamos por ahora."""
    activity.logger.info(f"Generando saludo para: {nombre}")
    return f"¡Hola, {nombre}! Este mensaje pasó por Temporal."


@activity.defn
async def notificar_resolucion(alerta_id: str, accion: str, observaciones: str | None) -> str:
    """
    Por ahora solo registra en el log que la alerta se resolvió.
    Todavía NO toca Postgres — eso lo sumamos en el próximo paso del roadmap,
    cuando conectemos el workflow con la tabla "alertas" de verdad.
    """
    activity.logger.info(
        f"Alerta {alerta_id} resuelta. Acción: {accion}. Observaciones: {observaciones}"
    )
    return f"Alerta {alerta_id} resuelta con acción: '{accion}'"