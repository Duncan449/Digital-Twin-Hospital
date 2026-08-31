from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config import settings

# echo=True imprime cada sentencia SQL que ejecuta SQLAlchemy en la consola.
# Es muy útil mientras aprendemos/depuramos; conviene apagarlo (False) en producción.
engine = create_async_engine(settings.database_url, echo=True)

# Fábrica de sesiones. expire_on_commit=False evita que SQLAlchemy invalide
# los objetos Python después de un commit (si no, habría que volver a
# consultarlos para leer sus datos después de guardar).
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession:
    """
    Dependencia de FastAPI (se usa con Depends(get_db) en cada endpoint).
    Abre una sesión nueva por request, se la entrega al endpoint, y la
    cierra automáticamente al terminar -- haya terminado bien o con error.
    """
    async with AsyncSessionLocal() as session:
        yield session
