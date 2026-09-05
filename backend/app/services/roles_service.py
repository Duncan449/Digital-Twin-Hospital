import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.usuarios import Rol
from app.schemas.usuarios import RolCrear


async def crear_rol(db: AsyncSession, datos: RolCrear) -> Rol:
    nuevo_rol = Rol(
        id=uuid.uuid4(),
        nombre=datos.nombre,
        descripcion=datos.descripcion,
        permisos=datos.permisos,
    )
    db.add(nuevo_rol)

    try:
        await db.commit()
    except IntegrityError:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=f"Ya existe un rol con el nombre '{datos.nombre}'.",
        )

    await db.refresh(nuevo_rol)
    return nuevo_rol


async def listar_roles(db: AsyncSession) -> list[Rol]:
    resultado = await db.execute(select(Rol))
    return list(resultado.scalars().all())


async def obtener_rol_por_id(db: AsyncSession, rol_id: uuid.UUID) -> Rol:
    resultado = await db.execute(select(Rol).where(Rol.id == rol_id))
    rol = resultado.scalar_one_or_none()
    if rol is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Rol no encontrado.")
    return rol