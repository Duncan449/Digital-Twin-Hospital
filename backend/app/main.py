import asyncio
from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI
from fastapi.middleware.cors import CORSMiddleware

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession
from app.config.database import get_db

from app.routes.pacientes_routes import router as pacientes_router
from app.routes.auth_routes import router as auth_router
from app.routes.signos_vitales_routes import router as signos_vitales_router
from app.routes.intervenciones_routes import router as intervenciones_router
from app.routes.eventos_routes import router as eventos_router
from app.routes.tipos_signos_vitales_routes import router as tipos_signos_vitales_router
from app.routes.simulador_routes import router as simulador_router
from app.websockets.gateway import router as websockets_router, escuchar_eventos_redis
from app.routes.alertas_routes import router as alertas_router, router_paciente as alertas_paciente_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Arranca la tarea de fondo que escucha Redis apenas levanta el
    servidor, y la cancela cuando se apaga. Todo lo que va ANTES 
    del 'yield' corre en el arranque; lo que va después, en el apagado.
    """
    tarea_redis = asyncio.create_task(escuchar_eventos_redis())
    yield
    tarea_redis.cancel()


app = FastAPI(
    title="Sistema de Monitorización Sanitaria - Digital Twin",
    lifespan=lifespan,
)

# Sin esto, el navegador bloquea cualquier fetch del frontend (Vite, en
# otro puerto) hacia esta API, aunque el backend responda bien -- el
# navegador ni siquiera deja que el JS del frontend LEA la respuesta.
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(pacientes_router)
app.include_router(auth_router)
app.include_router(signos_vitales_router)
app.include_router(intervenciones_router)
app.include_router(eventos_router)
app.include_router(tipos_signos_vitales_router)
app.include_router(simulador_router)
app.include_router(websockets_router)
app.include_router(alertas_router)
app.include_router(alertas_paciente_router)

@app.get("/salud")
async def salud(db: AsyncSession = Depends(get_db)):
    resultado = await db.execute(text("SELECT 1"))
    return {"estado": "ok", "conexion_db": resultado.scalar() == 1}