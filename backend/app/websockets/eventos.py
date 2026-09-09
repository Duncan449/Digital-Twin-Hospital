# backend/app/websockets/eventos.py
import json
from datetime import datetime, timezone
from typing import Any

from app.config.redis_client import get_redis_client

# Un solo canal para todos los eventos clínicos. Cada mensaje lleva su
# propio paciente_id adentro, así el WS Gateway sabe a quién reenviárselo.
# (Si a futuro el volumen de eventos crece mucho, se podría separar en
# canales por paciente_id -- para el MVP, un canal único alcanza y sobra.)
CANAL_EVENTOS = "eventos_pacientes"


async def publicar_evento(paciente_id: str, tipo: str, data: dict[str, Any]) -> None:
    """
    Este es el ÚNICO punto de contacto
    entre la lógica del programa (venga de un endpoint de FastAPI o de una
    Activity de Temporal corriendo en el Worker) y los
    WebSockets. Publican acá y Redis se encarga de avisarle a quien esté
    escuchando (el WS Gateway, definido en gateway.py).
    """
    cliente_redis = await get_redis_client()
    mensaje = {
        "paciente_id": str(paciente_id),
        "tipo": tipo,
        "data": data,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    # default=str: por si algún valor Decimal se cuela sin convertir a str antes.
    await cliente_redis.publish(CANAL_EVENTOS, json.dumps(mensaje, default=str))