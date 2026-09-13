# backend/app/config/redis_client.py
import redis as redis_sincrono
import redis.asyncio as redis

from app.config.config import settings

# Canal separado del de eventos clínicos (CANAL_EVENTOS, en
# app/websockets/eventos.py): coordina exclusivamente entre los scripts
# de demo (joystick_simulador.py <-> monitor_continuo.py) cuándo pausar
# o reanudar el control automático de un paciente puntual. A propósito
# NO es el mismo canal que reenvía el WS Gateway al frontend -- esto es
# plomería interna entre dos scripts de demo, no un evento clínico que
# un médico necesite ver en pantalla.
CANAL_COORDINACION_SIMULADOR = "coordinacion_simulador"

_cliente: redis.Redis | None = None
_cliente_sincrono: redis_sincrono.Redis | None = None


async def get_redis_client() -> redis.Redis:
    """
    Devuelve una conexión Redis reutilizable. Tanto el proceso de FastAPI
    como el proceso del Worker de Temporal importan esta misma función:
    cada uno arma SU PROPIA conexión (son procesos distintos, no pueden
    compartir un objeto Python en memoria), pero ambos apuntan al mismo
    servidor Redis, que es lo que realmente los conecta.
    """
    global _cliente
    if _cliente is None:
        _cliente = redis.from_url(settings.redis_url, decode_responses=True)
    return _cliente


def get_redis_client_sincrono() -> redis_sincrono.Redis:
    """
    Versión síncrona de get_redis_client(), para scripts standalone que
    no corren sobre asyncio
    """
    global _cliente_sincrono
    if _cliente_sincrono is None:
        _cliente_sincrono = redis_sincrono.Redis.from_url(
            settings.redis_url, decode_responses=True
        )
    return _cliente_sincrono
