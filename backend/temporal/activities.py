from temporalio import activity


@activity.defn
async def generar_saludo(nombre: str) -> str:
    """
    Una Activity es el lugar donde pasan cosas "reales" con efectos
    secundarios: llamadas a APIs, escrituras en la base, envío de
    notificaciones, etc. Temporal la reintenta automáticamente si falla.

    Por ahora, solo simula un trabajo simple para probar la conexión.
    """
    activity.logger.info(f"Generando saludo para: {nombre}")
    return f"¡Hola, {nombre}! Este mensaje pasó por Temporal."