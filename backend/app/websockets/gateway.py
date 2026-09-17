import json

from fastapi import APIRouter, WebSocket, WebSocketDisconnect

from app.config.redis_client import get_redis_client
from app.websockets.eventos import CANAL_EVENTOS

router = APIRouter(tags=["WebSockets"])


class ConnectionManager:
    """
    Mantiene el registro de conexiones WebSocket abiertas tanto por paciente_id como globales (Dashboard). 
    """

    def __init__(self) -> None:
        self._conexiones: dict[str, set[WebSocket]] = {}
        self._conexiones_globales: set[WebSocket] = set()

    async def conectar(self, paciente_id: str, websocket: WebSocket) -> None:
        await websocket.accept()
        self._conexiones.setdefault(paciente_id, set()).add(websocket)

    def desconectar(self, paciente_id: str, websocket: WebSocket) -> None:
        conexiones = self._conexiones.get(paciente_id)
        if conexiones:
            conexiones.discard(websocket)
            if not conexiones:
                del self._conexiones[paciente_id]
    
    async def conectar_global(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self._conexiones_globales.add(websocket)
        
    def desconectar_global(self, websocket: WebSocket) -> None:
        self._conexiones_globales.discard(websocket)

    async def enviar_a_paciente(self, paciente_id: str, mensaje: dict) -> None:
        conexiones = self._conexiones.get(paciente_id)
        if not conexiones:
            return  
        # Copiamos a una lista antes de iterar, si una conexión falla y
        # la sacamos dentro del loop, no queremos modificar el set
        # mientras lo estamos recorriendo.
        for websocket in list(conexiones):
            try:
                await websocket.send_json(mensaje)
            except Exception:
                self.desconectar(paciente_id, websocket)
    
    async def enviar_a_todos(self, mensaje: dict) -> None:
        for websocket in list(self._conexiones_globales):
            try:
                await websocket.send_json(mensaje)
            except Exception:
                self.desconectar_global(websocket)


manager = ConnectionManager()


@router.websocket("/ws/pacientes/{paciente_id}")
async def websocket_paciente_endpoint(websocket: WebSocket, paciente_id: str):
    """
    Endpoint que abre el frontend para recibir en vivo los eventos de un paciente puntual.
    """
    await manager.conectar(paciente_id, websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.desconectar(paciente_id, websocket)

@router.websocket("/ws/eventos")
async def websocket_eventos_globales_endpoint(websocket: WebSocket):
    """
    Endpoint que abre el frontend para recibir en vivo todos los eventos de todos los pacientes.
    Utilizado por el Dashboard de la clínica, para ver en tiempo real qué está pasando con todos los pacientes.
    """
    await manager.conectar_global(websocket)
    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.desconectar_global(websocket)


async def escuchar_eventos_redis() -> None:
    """
    Tarea de fondo que arranca una vez por proceso de FastAPI 
    Se suscribe al canal de Redis y, por cada mensaje que llega
    lo reenvía a las conexiones WS del paciente correspondiente.
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
            await manager.enviar_a_todos(contenido)
    except Exception as error:
        print(f"Error en el listener de eventos Redis: {error}")