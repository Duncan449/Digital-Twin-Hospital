from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.routes.pacientes_routes import router as pacientes_router
from app.routes.auth_routes import router as auth_router
from app.routes.signos_vitales_routes import router as signos_vitales_router

app = FastAPI(title="Sistema de Monitorización Sanitaria - Digital Twin")

app.include_router(pacientes_router)
app.include_router(auth_router)
app.include_router(signos_vitales_router)


@app.get("/salud")
async def salud(db: AsyncSession = Depends(get_db)):
    """
    Endpoint de diagnóstico: confirma que FastAPI puede conectarse a Neon.
    """
    resultado = await db.execute(text("SELECT 1"))
    return {"estado": "ok", "conexion_db": resultado.scalar() == 1}
