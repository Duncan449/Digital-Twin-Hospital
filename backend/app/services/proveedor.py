# backend/app/services/proveedor.py
from typing import List
from fastapi import HTTPException
from app.config.database import db
from app.schemas.proveedor import ProveedorIn, ProveedorOut


# Función auxiliar
async def get_proveedor_by_id(id: int) -> ProveedorOut:
    # GET - Trae al proveedor con el id indicado
    if id <= 0:
        raise HTTPException(status_code=400, detail="El ID debe ser un número positivo")

    try:
        query = "SELECT * FROM proveedores WHERE id = :id"
        row = await db.fetch_one(query=query, values={"id": id})
        if not row:
            raise HTTPException(
                status_code=404,
                detail=f"Proveedor con ID {id} no encontrado",
            )
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proveedor: {e}")


# FUNCIONES DE VALIDACIÓN


def validar_nombre(nombre: str) -> str: ## Validar el nombre del proveedor
    if not nombre or nombre.strip() == "":
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")

    nombre = nombre.strip()

    if len(nombre) < 3:
        raise HTTPException(
            status_code=400, detail="El nombre debe tener al menos 3 caracteres"
        )

    if len(nombre) > 100:
        raise HTTPException(
            status_code=400, detail="El nombre no puede tener más de 100 caracteres"
        )

    return nombre


def validar_telefono(telefono: str) -> str: # Validar el teléfono del proveedor
    if not telefono:
        return None

    if not telefono.strip():
        return None

    # Quitar espacios y caracteres especiales comunes
    telefono_limpio = (
        telefono.strip()
        .replace(" ", "")
        .replace("-", "")
        .replace("(", "")
        .replace(")", "")
    )

    if not telefono_limpio.isdigit():
        raise HTTPException(
            status_code=400, detail="El teléfono solo debe contener números"
        )

    if len(telefono_limpio) < 10:
        raise HTTPException(
            status_code=400, detail="El teléfono debe tener al menos 10 dígitos"
        )

    if len(telefono_limpio) > 20:
        raise HTTPException(
            status_code=400, detail="El teléfono no puede tener más de 20 dígitos"
        )

    return telefono_limpio


def validar_email(email: str) -> str: #convierte el email a minúsculas y elimina espacios
    if email:
        return email.strip().lower()
    return None


# CRUD PROVEEDORES


async def get_all_proveedores() -> List[ProveedorOut]:
    # GET - Trae a todos los proveedores de la BD
    try:
        query = "SELECT * FROM proveedores WHERE activo = true ORDER BY nombre"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener proveedores: {e}"
        )

async def get_all_proveedores_borrados(usuario_actual) -> List[ProveedorOut]:
    # GET - Trae a todos los proveedores borrados de la BD
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para ver los proveedores borrados")

    try:
        query = "SELECT * FROM proveedores WHERE activo = false ORDER BY nombre"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error al obtener proveedores borrados: {e}"
        )


async def create_proveedor(proveedor: ProveedorIn, usuario_actual) -> ProveedorOut:
    # POST - Crea un proveedor

    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para crear proveedores")
    
    try:
        # VALIDAR CAMPOS
        nombre_validado = validar_nombre(proveedor.nombre)
        telefono_validado = validar_telefono(proveedor.telefono)
        email_validado = validar_email(proveedor.email)

        # Validar nombre duplicado
        query_check = "SELECT id FROM proveedores WHERE LOWER(nombre) = LOWER(:nombre)"
        existing = await db.fetch_one(query_check, values={"nombre": nombre_validado})
        if existing:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe un proveedor con el nombre '{nombre_validado}'",
            )

        # Validar email duplicado
        if email_validado:
            query_email = (
                "SELECT id FROM proveedores WHERE LOWER(email) = LOWER(:email)"
            )
            existing_email = await db.fetch_one(
                query_email, values={"email": email_validado}
            )
            if existing_email:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe un proveedor con el email '{email_validado}'",
                )

        # Validar teléfono duplicado
        if telefono_validado:
            query_telefono = (
                "SELECT id, nombre FROM proveedores WHERE telefono = :telefono"
            )
            existing_telefono = await db.fetch_one(
                query_telefono, values={"telefono": telefono_validado}
            )
            if existing_telefono:
                raise HTTPException(
                    status_code=400,
                    detail=f"El teléfono '{telefono_validado}' ya está registrado para el proveedor '{existing_telefono['nombre']}'",
                )

        # Insertar proveedor con valores validados
        query = """
            INSERT INTO proveedores (nombre, telefono, email, direccion, ciudad, activo)
            VALUES (:nombre, :telefono, :email, :direccion, :ciudad, :activo)
        """
        values = {
            "nombre": nombre_validado,
            "telefono": telefono_validado,
            "email": email_validado,
            "direccion": proveedor.direccion,
            "ciudad": proveedor.ciudad,
            "activo": proveedor.activo,
        }

        last_record_id = await db.execute(query=query, values=values)
        return await get_proveedor_by_id(last_record_id)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en create_proveedor: {e}")
        raise HTTPException(status_code=500, detail=f"Error al crear proveedor: {e}")


async def update_proveedor(proveedor_id: int, proveedor: ProveedorIn, usuario_actual) -> ProveedorOut:
    # PUT - Modifica el proveedor con el id indicado

    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar proveedores")

    try:
        # Validar que el ID sea positivo
        if proveedor_id <= 0:
            raise HTTPException(
                status_code=400, detail="El ID debe ser un número positivo"
            )

        # VALIDAR CAMPOS
        nombre_validado = validar_nombre(proveedor.nombre)
        telefono_validado = validar_telefono(proveedor.telefono)
        email_validado = validar_email(proveedor.email)

        # Verificar que el proveedor existe
        query_exists = "SELECT id FROM proveedores WHERE id = :id"
        exists = await db.fetch_one(query_exists, values={"id": proveedor_id})
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"Proveedor con ID {proveedor_id} no encontrado",
            )

        # Validar nombre duplicado
        query_nombre = "SELECT id FROM proveedores WHERE LOWER(nombre) = LOWER(:nombre) AND id != :id"
        existing_nombre = await db.fetch_one(
            query_nombre, values={"nombre": nombre_validado, "id": proveedor_id}
        )
        if existing_nombre:
            raise HTTPException(
                status_code=400,
                detail=f"Ya existe otro proveedor con el nombre '{nombre_validado}'",
            )

        # Validar email duplicado si se proporciona
        if email_validado:
            query_email = "SELECT id FROM proveedores WHERE LOWER(email) = LOWER(:email) AND id != :id"
            existing_email = await db.fetch_one(
                query_email, values={"email": email_validado, "id": proveedor_id}
            )
            if existing_email:
                raise HTTPException(
                    status_code=400,
                    detail=f"Ya existe otro proveedor con el email '{email_validado}'",
                )

        # Validar teléfono duplicado si se proporciona
        if telefono_validado:
            query_telefono = "SELECT id, nombre FROM proveedores WHERE telefono = :telefono AND id != :id"
            existing_telefono = await db.fetch_one(
                query_telefono,
                values={"telefono": telefono_validado, "id": proveedor_id},
            )
            if existing_telefono:
                raise HTTPException(
                    status_code=400,
                    detail=f"El teléfono '{telefono_validado}' ya está registrado para el proveedor '{existing_telefono['nombre']}'",
                )

        # Actualizar con valores validados
        query = """
            UPDATE proveedores
            SET nombre = :nombre,
                telefono = :telefono,
                email = :email,
                direccion = :direccion,
                ciudad = :ciudad,
                activo = :activo
            WHERE id = :id
        """
        values = {
            "nombre": nombre_validado,
            "telefono": telefono_validado,
            "email": email_validado,
            "direccion": proveedor.direccion,
            "ciudad": proveedor.ciudad,
            "activo": proveedor.activo,
            "id": proveedor_id,
        }

        await db.execute(query=query, values=values)
        return await get_proveedor_by_id(proveedor_id)

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en update_proveedor: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error al actualizar proveedor: {e}"
        )


async def delete_proveedor(id: int, usuario_actual) -> dict:
    # DELETE - Elimina el proveedor con el id indicado - Soft delete

    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar proveedores")

    try:
        # Validar ID positivo
        if id <= 0:
            raise HTTPException(
                status_code=400, detail="El ID debe ser un número positivo"
            )

        # Verificar que existe antes de eliminar
        query_exists = "SELECT id FROM proveedores WHERE id = :id AND activo = true"
        exists = await db.fetch_one(query_exists, values={"id": id})
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"Proveedor con ID {id} no encontrado o ya está eliminado",
            )

        query = "UPDATE proveedores SET activo = false WHERE id = :id"
        await db.execute(query=query, values={"id": id})
        return {"message": f"Proveedor con ID {id} eliminado correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en delete_proveedor: {e}")
        raise HTTPException(status_code=500, detail=f"Error al eliminar proveedor: {e}")

async def restore_proveedor(
    id: int, usuario_actual
) -> dict:  # POST- Restaurar un proveedor borrado 
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para restaurar proveedores")

    try:
        # Validar ID positivo
        if id <= 0:
            raise HTTPException(
                status_code=400, detail="El ID debe ser un número positivo"
            )

        # Verificar que existe antes de restaurar
        query_exists = "SELECT id FROM proveedores WHERE id = :id AND activo = false"
        exists = await db.fetch_one(query_exists, values={"id": id})
        if not exists:
            raise HTTPException(
                status_code=404,
                detail=f"Proveedor con ID {id} no encontrado o ya está activo",
            )

        query = "UPDATE proveedores SET activo = true WHERE id = :id"
        await db.execute(query=query, values={"id": id})
        return {"message": f"Proveedor con ID {id} restaurado correctamente"}

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error en restore_proveedor: {e}")
        raise HTTPException(status_code=500, detail=f"Error al restaurar proveedor: {e}")
