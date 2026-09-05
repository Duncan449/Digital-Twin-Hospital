"""
Script de seed: crea el usuario admin inicial.

Se ejecuta UNA sola vez a mano (no es parte del flujo normal de la app),
para romper el problema de huevo-y-gallina: necesitamos un usuario para
loguearnos, pero el único endpoint para crear usuarios va a estar
protegido detrás de un login.

Uso (desde la carpeta backend/, con el venv activado):
    python seed_admin.py
"""
import asyncio
import getpass

from sqlalchemy import select

from app.config.database import AsyncSessionLocal
from app.core.security import hashear_password
from app.models.usuarios import Rol, Usuario

NOMBRE_ROL_ADMIN = "admin"


async def seed_admin() -> None:
    async with AsyncSessionLocal() as db:
        # 1. Buscamos el rol "admin" que ya insertaste a mano en Neon
        #    (el que tiene permisos = {"todo": true}).
        resultado = await db.execute(select(Rol).where(Rol.nombre == NOMBRE_ROL_ADMIN))
        rol_admin = resultado.scalar_one_or_none()

        if rol_admin is None:
            print(f"No existe un rol llamado '{NOMBRE_ROL_ADMIN}' en la tabla roles.")
            print("Creá ese rol en Neon antes de correr este script.")
            return

        email = input("Email del usuario admin: ").strip()

        # 2. Evitamos duplicados: si ya hay un usuario con ese email, avisamos y salimos.
        resultado = await db.execute(select(Usuario).where(Usuario.email == email))
        if resultado.scalar_one_or_none() is not None:
            print(f"Ya existe un usuario con el email '{email}'. No se creó nada.")
            return

        nombre = input("Nombre del usuario admin: ").strip()

        # getpass, no input(): la contraseña no queda visible en la
        # terminal ni guardada en el historial de la consola al tipearla.
        password = getpass.getpass("Contraseña (mínimo 8 caracteres): ")
        if len(password) < 8:
            print("La contraseña debe tener al menos 8 caracteres. No se creó nada.")
            return

        # No hace falta pasar 'id': el modelo Usuario ya tiene
        # default=uuid.uuid4 en la columna, se genera solo.
        nuevo_usuario = Usuario(
            nombre=nombre,
            email=email,
            password_hash=hashear_password(password),
            rol_id=rol_admin.id,
        )
        db.add(nuevo_usuario)
        await db.commit()

        print(f"Usuario admin '{email}' creado correctamente (rol: {rol_admin.nombre}).")


if __name__ == "__main__":
    asyncio.run(seed_admin())