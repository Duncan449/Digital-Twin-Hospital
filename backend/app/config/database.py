from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.config.config import settings

# echo=True imprime cada sentencia SQL que ejecuta SQLAlchemy en la consola. Eso significa que veremos en la consola cada SELECT, INSERT, UPDATE, etc. que haga nuestra app.
# Puede ser útil mientras depuramos pero conviene apagarlo (False) en producción.
engine = create_async_engine(settings.database_url, echo=True)

# Fábrica de sesiones. expire_on_commit=False evita que SQLAlchemy invalide los objetos Python después de un commit (si no, habría que volver a consultarlos para leer sus datos después de guardar).
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db() -> AsyncSession: 
    """Esta función es un "dependency" de FastAPI que nos da una sesión de base de datos para cada request.
      FastAPI se encarga de llamar a esta función, abrir la sesión, pasarla al endpoint y cerrarla automáticamente al terminar."""

    async with AsyncSessionLocal() as session:
        yield session
