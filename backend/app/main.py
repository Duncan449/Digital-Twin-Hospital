from fastapi import Depends, FastAPI
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db

app = FastAPI(title="Sistema de Monitorización Sanitaria - Digital Twin")


@app.get("/salud")
async def salud(db: AsyncSession = Depends(get_db)):
    """
    Endpoint de diagnóstico: confirma que FastAPI puede conectarse a Neon.
    "SELECT 1" es la forma estándar de chequear que una conexión a la
    base está viva, sin depender de que exista ninguna tabla todavía.
    """
    resultado = await db.execute(text("SELECT 1"))
    return {"estado": "ok", "conexion_db": resultado.scalar() == 1}
