from temporalio.client import Client

# Guardamos la conexión en una variable global para no reconectar a Temporal
# en cada request. Es el mismo patrón que "engine" en app/config/database.py:
# se crea una sola vez y se reutiliza.
_client: Client | None = None


async def get_temporal_client() -> Client:
    global _client
    if _client is None:
        _client = await Client.connect("localhost:7233", namespace="default")
    return _client