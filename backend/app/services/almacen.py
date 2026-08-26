from typing import List
from fastapi import HTTPException
from app.config.database import db
from app.schemas.almacen import AlmacenIn, AlmacenOut


# Función auxiliar
async def get_almacen_by_id(id: int) -> AlmacenOut:  # Obtener un almacen por id
    try:
        if id <= 0:  # Validar IDs negativos o cero
            raise HTTPException(status_code=400, detail="ID inválido")

        query = "SELECT * FROM almacenes WHERE id = :id"
        row = await db.fetch_one(query=query, values={"id": id})
        if not row:
            raise HTTPException(status_code=404, detail="Almacen no encontrado")
        return row
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener almacen: {e}")


# CRUD ALMACEN

async def get_all_almacenes() -> List[AlmacenOut]:  # Obtener todos los almacenes visibles
    try: 
        query = "SELECT * FROM almacenes WHERE activo = true"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener almacenes: {e}")

async def get_all_almacenes_borrados(usuario_actual) -> List[AlmacenOut]:  # Obtener todos los almacenes borrados

    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para ver los almacenes borrados")
    
    try: 
        query = "SELECT * FROM almacenes WHERE activo = false"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener almacenes borrados: {e}")


async def create_almacen(almacen: AlmacenIn, usuario_actual) -> AlmacenOut:  # Crear un nuevo almacen

    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para crear almacenes")
    
    try:
        if not almacen.nombre.strip():
            raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")  # Validar que el nombre no esté vacío
        if not almacen.ubicacion.strip():
            raise HTTPException(status_code=400, detail="La ubicación no puede estar vacía")  # Validar que la ubicación no esté vacía
        
        query = """
            INSERT INTO almacenes (nombre, ubicacion, activo)
            VALUES (:nombre, :ubicacion, :activo)
        """
        last_record_id = await db.execute(query=query, values=almacen.dict())  # Crea y retorna el nuevo almacén
        return await get_almacen_by_id(last_record_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear almacen: {e}")  


async def update_almacen(almacen_id: int, almacen: AlmacenIn, usuario_actual) -> AlmacenOut:  # Actualizar un almacen

    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para actualizar almacenes")
    
    #validar que el nombre no esté vacío
    if not almacen.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre no puede estar vacío")  

    try:
        revision_query = "SELECT id FROM almacenes WHERE id = :id"
        existing = await db.fetch_one(revision_query, values={"id": almacen_id})
        if not existing:
            raise HTTPException(
                status_code=404, detail=f"Almacen con id {almacen_id} no encontrado"
            )
        query = """
            UPDATE almacenes
            SET nombre = :nombre,
                ubicacion = :ubicacion,
                activo = :activo
            WHERE id = :id
        """
        values = {**almacen.dict(), "id": almacen_id}
        await db.execute(query=query, values=values)
        return await get_almacen_by_id(almacen_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar almacen: {e}")


async def delete_almacen(id: int, usuario_actual) -> dict:  # Eliminar un almacen - Soft delete
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar almacenes")

    try:
        query = "UPDATE almacenes SET activo = 0 WHERE id = :id AND activo = 1"
        result = await db.execute(query=query, values={"id": id})
        if not result:
            raise HTTPException(status_code=404, detail="Almacen no encontrado o ya está eliminado")
        return {"message": "Almacen eliminado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al eliminar almacen: {e}")


async def restore_almacen(id: int, usuario_actual) -> dict:  # Restaurar un almacen borrado 
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para restaurar almacenes")

    try:
        query = "UPDATE almacenes SET activo = 1 WHERE id = :id AND activo = 0"
        result = await db.execute(query=query, values={"id": id})
        if not result:
            raise HTTPException(status_code=404, detail="Almacen no encontrado o ya está activo")
        return {"message": "Almacen restaurado correctamente"}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al restaurar almacen: {e}")
