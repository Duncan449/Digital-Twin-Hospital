from typing import List
from fastapi import HTTPException
from app.config.database import db
from app.schemas.categoria import CategoriaIn, CategoriaOut


# Función auxiliar
async def get_categoria_by_id(
    id: int,
) -> CategoriaOut:  # GET - Trae a la categoría con el id indicado
    query = "SELECT * FROM categorias WHERE id = :id"
    row = await db.fetch_one(query=query, values={"id": id})
    if not row:
        raise HTTPException(status_code=404, detail="Categoría no encontrada")
    return row


# CRUD CATEGORIA

async def get_all_categorias() -> (
    List[CategoriaOut]
):  # GET - Trae a todas las categorias visibles de la BD
    try:
        query = "SELECT * FROM categorias WHERE activa = true"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        print(f"Error al obtener categorias: {e}")
        raise HTTPException(
            status_code=500, detail="Error al obtener las categorias. Intente nuevamente."
        )

async def get_all_categorias_borradas(usuario_actual) -> (
    List[CategoriaOut]
):  # GET - Trae a todas las categorias borradas de la BD
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para ver las categorias borradas")

    try:
        query = "SELECT * FROM categorias WHERE activa = false"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        print(f"Error al obtener categorias borradas: {e}")
        raise HTTPException(
            status_code=500, detail="Error al obtener las categorias borradas. Intente nuevamente."
        )


async def create_categoria(
    categoria: CategoriaIn, usuario_actual
) -> CategoriaOut:  # POST - Crea un categoria

    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para crear categorías")
    
    #verificar que el nombre no esté vacío
    if not categoria.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre de la categoría no puede estar vacío")

    revision_query = "SELECT id FROM categorias WHERE nombre = :nombre "
    existe = await db.fetch_one(
        revision_query, values={"nombre": categoria.nombre}
    )  # Verificación de que la categoría no esté ya registrada
    if existe:
        raise HTTPException(
            status_code=400,
            detail=f"La categoría {categoria.nombre} ya está registrada",
        )

    try:
        query = """
            INSERT INTO categorias (nombre, descripcion, activa)
            VALUES (:nombre, :descripcion, :activa)
        """
        last_record_id = await db.execute(query=query, values=categoria.dict())
        return await get_categoria_by_id(last_record_id)

    except Exception as e:
        print(f"Error al crear categoría: {e}")
        raise HTTPException(
            status_code=500, detail="Error al crear la categoría. Intente nuevamente."
        )


async def update_categoria(
    categoria_id: int, categoria: CategoriaIn, usuario_actual
) -> CategoriaOut:  # PUT - Modifica el categoria con el id indicado
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar categorías")

    revision_query = "SELECT id FROM categorias WHERE id = :id"  # Verificación de que la categoria exista
    existing = await db.fetch_one(revision_query, values={"id": categoria_id})
    if not existing:
        raise HTTPException(
            status_code=404, detail=f"Categoria con id {categoria_id} no encontrada"
        )
    
        #verificar que el nombre no esté vacío
    if not categoria.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre de la categoría no puede estar vacío")

    nombre_query = "SELECT id FROM categorias WHERE nombre = :nombre AND id != :id"  # Para evitar ponerle el nombre de una categoría ya existente
    nombre_exists = await db.fetch_one(
        nombre_query, values={"nombre": categoria.nombre, "id": categoria_id}
    )
    if nombre_exists:
        raise HTTPException(
            status_code=400, detail=f"El nombre {categoria.nombre} ya está en uso"
        )

    try:
        query = """
            UPDATE categorias
            SET nombre = :nombre,
                descripcion = :descripcion,
                activa = :activa
            WHERE id = :id
        """
        values = {**categoria.dict(), "id": categoria_id}
        await db.execute(query=query, values=values)
        return await get_categoria_by_id(categoria_id)

    except Exception as e:
        print(f"Error al actualizar categoría: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar la categoría")


async def delete_categoria(
    id: int, usuario_actual
) -> dict:  # DELETE - Elimina la categoria con el id indicado - Soft delete
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar categorías")

    revision_query = (
        "SELECT id FROM categorias WHERE id = :id AND activa = true"  # Verifica que exista la categoria
    )
    existe = await db.fetch_one(revision_query, values={"id": id})
    if not existe:
        raise HTTPException(
            status_code=404, detail=f"Categoria con id {id} no encontrada o ya está eliminada"
        )

    try:
        query = "UPDATE categorias SET activa = false WHERE id = :id"
        await db.execute(query=query, values={"id": id})
        return {"message": f"Categoria con id {id} eliminada correctamente"}

    except Exception as e:
        print(f"Error al eliminar categoría: {e}")
        raise HTTPException(status_code=400, detail="Error al eliminar la categoría")

async def restore_categoria(
    id: int, usuario_actual
) -> dict:  # Restaurar una categoria borrada 
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para restaurar categorías")

    revision_query = (
        "SELECT id FROM categorias WHERE id = :id AND activa = false"  # Verifica que exista la categoria borrada
    )
    existe = await db.fetch_one(revision_query, values={"id": id})
    if not existe:
        raise HTTPException(
            status_code=404, detail=f"Categoria con id {id} no encontrada o ya está activa"
        )

    try:
        query = "UPDATE categorias SET activa = true WHERE id = :id"
        await db.execute(query=query, values={"id": id})
        return {"message": f"Categoria con id {id} restaurada correctamente"}

    except Exception as e:
        print(f"Error al restaurar categoría: {e}")
        raise HTTPException(status_code=400, detail="Error al restaurar la categoría")
