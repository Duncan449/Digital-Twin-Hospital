import uuid

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hashear_password, verificar_password
from app.models.usuarios import Usuario
from app.schemas.usuarios import UsuarioActualizar, UsuarioCrear, UsuarioLogin


async def crear_usuario(db: AsyncSession, datos: UsuarioCrear) -> Usuario:
    """Hashea la password antes de guardar. Nunca se guarda ni se loguea
    la contraseña original."""
    nuevo_usuario = Usuario(
        id=uuid.uuid4(),
        nombre=datos.nombre,
        email=datos.email,
        password_hash=hashear_password(datos.password),
        rol_id=datos.rol_id,
    )
    db.add(nuevo_usuario)

    try:
        await db.commit()
    except IntegrityError:
        # Salta si el email ya existe (unique=True) o si rol_id no existe (FK).
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="El email ya está registrado o el rol indicado no existe.",
        )

    await db.refresh(nuevo_usuario)
    return nuevo_usuario


async def obtener_usuario_por_email(db: AsyncSession, email: str) -> Usuario | None:
    resultado = await db.execute(select(Usuario).where(Usuario.email == email))
    return resultado.scalar_one_or_none()


async def obtener_usuario_por_id(db: AsyncSession, usuario_id: uuid.UUID) -> Usuario | None:
    resultado = await db.execute(select(Usuario).where(Usuario.id == usuario_id))
    return resultado.scalar_one_or_none()


async def autenticar_usuario(db: AsyncSession, datos: UsuarioLogin) -> Usuario:
    """
    Verifica credenciales para el login.

    A propósito el error es el MISMO para "email no existe" y "password
    incorrecta": si fueran distintos, alguien podría usar el login para
    averiguar qué emails están registrados en el sistema (user enumeration).
    """
    usuario = await obtener_usuario_por_email(db, datos.email)

    if usuario is None or not verificar_password(datos.password, usuario.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email o contraseña incorrectos.",
        )

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo.",
        )

    return usuario


async def listar_usuarios(db: AsyncSession) -> list[Usuario]:
    resultado = await db.execute(select(Usuario))
    return list(resultado.scalars().all())


async def actualizar_usuario(
    db: AsyncSession, usuario_id: uuid.UUID, datos: UsuarioActualizar
) -> Usuario:
    usuario = await obtener_usuario_por_id(db, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.")

    # exclude_unset: solo pisamos los campos que vinieron en el body del PATCH.
    for campo, valor in datos.model_dump(exclude_unset=True).items():
        setattr(usuario, campo, valor)

    await db.commit()
    await db.refresh(usuario)
    return usuario


async def desactivar_usuario(db: AsyncSession, usuario_id: uuid.UUID) -> Usuario:
    """Soft delete: nunca se borran filas de usuarios, solo activo=False."""
    usuario = await obtener_usuario_por_id(db, usuario_id)
    if usuario is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Usuario no encontrado.")

    usuario.activo = False
    await db.commit()
    await db.refresh(usuario)
    return usuario