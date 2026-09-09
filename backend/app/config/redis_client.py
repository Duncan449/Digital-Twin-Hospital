# backend/app/config/redis_client.py
import redis.asyncio as redis

from app.config.config import settings

_cliente: redis.Redis | None = None


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