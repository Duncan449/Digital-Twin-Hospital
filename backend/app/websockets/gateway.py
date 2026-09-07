import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config.redis_client import get_redis_client
from app.websockets.eventos import CANAL_EVENTOS

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    """
    Mantiene el registro de qué conexión WebSocket está mirando a qué
    paciente. Un mismo paciente puede tener varias conexiones abiertas a
    la vez, por eso guardamos un set de conexiones por paciente_id, no una sola.
    """

    def __init__(self) -> None:
        self._conexiones: dict[str, set[WebSocket]] = {}

    async def conectar(self, paciente_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._conexiones.setdefault(paciente_id, set()).add(websocket)

    def desconectar(self, paciente_id: str, websocket: WebSocket) -> None:
        conexiones = self._conexiones.get(paciente_id)
        if conexiones:
            conexiones.discard(websocket)
            if not conexiones:
                del self._conexiones[paciente_id]

    async def enviar_a_paciente(self, paciente_id: str, mensaje: dict) -> None:
        conexiones = self._conexiones.get(paciente_id)
        if not conexiones:
            return  # Nadie mirando este paciente ahora mismo -- no pasa nada.

        # Copiamos a una lista antes de iterar: si una conexión falla y
        # la sacamos DENTRO del loop, no queremos modificar el set
        # mientras lo estamos recorriendo.
        for websocket in list(conexiones):
            try:
                await websocket.send_json(mensaje)
            except Exception:
                self.desconectar(paciente_id, websocket)


manager = ConnectionManager()


@router.websocket("/ws/pacientes/{paciente_id}")
async def websocket_paciente_endpoint(websocket: WebSocket, paciente_id: str):
    """
    Endpoint que abre el frontend para recibir 
    en vivo los eventos de UN paciente puntual.

    Es de solo lectura desde el punto de vista del cliente: no esperamos
    comandos del navegador en este MVP. El 'receive_text()' dentro del
    while solo existe para que FastAPI detecte cuándo el cliente cierra
    la pestaña (WebSocketDisconnect) -- sin ese await, la conexión
    quedaría "colgada" en el manager para siempre.
    """
    await manager.conectar(paciente_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.desconectar(paciente_id, websocket)


async def escuchar_eventos_redis() -> None:
    """
    Tarea de fondo que arranca UNA vez por proceso de FastAPI 
    ('lifespan' en main.py). Se suscribe al canal de Redis y, por cada
    mensaje que llega lo reenvía a las conexiones WS del paciente 
    correspondiente.

    El try/except envuelve todo el loop a propósito: 'create_task' no
    propaga excepciones a ningún lado visible si nadie hace 'await'
    sobre la tarea, así que sin este bloque, un error de conexión a
    Redis quedaría completamente silencioso en producción.
    """
    try:
        cliente_redis = await get_redis_client()
        pubsub = cliente_redis.pubsub()
        await pubsub.subscribe(CANAL_EVENTOS)

        async for mensaje in pubsub.listen():
            if mensaje["type"] != "message":
                continue  # Ignoramos la confirmación de suscripción.

            contenido = json.loads(mensaje["data"])
            await manager.enviar_a_paciente(contenido["paciente_id"], contenido)
    except Exception as error:
        print(f"Error en el listener de eventos Redis: {error}")