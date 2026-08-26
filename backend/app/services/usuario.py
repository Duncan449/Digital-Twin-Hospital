from typing import List
from fastapi import HTTPException
from app.config.database import db
from app.schemas.usuario import UsuarioIn, UsuarioOut, UsuarioUpdate


# Función auxiliar
async def get_usuario_by_id(
    id: int,
) -> UsuarioOut:  # GET - Trae al usuario con el id indicado

    try:
        query = "SELECT * FROM usuarios WHERE id = :id"
        row = await db.fetch_one(query=query, values={"id": id})
        if not row:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return row
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el usuario: {e}")


# CRUD USUARIOS

async def get_all_usuarios(usuario_actual) -> (
    List[UsuarioOut]
):  # GET - Trae a todos los usuarios visibles de la BD
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para ver los usuarios")

    try:
        query = "SELECT * FROM usuarios WHERE activo = true"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios: {e}")

async def get_all_usuarios_borrados(usuario_actual) -> (
    List[UsuarioOut]
):  # GET - Trae a todos los usuarios borrados de la BD
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para ver los usuarios borrados")

    try:
        query = "SELECT * FROM usuarios WHERE activo = false"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener usuarios borrados: {e}")


async def update_usuario(
    usuario_id: int, usuario: UsuarioUpdate, usuario_actual
) -> UsuarioOut:  # PUT - Modifica el usuario con el id indicado
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar un usuario")

    revision_query = "SELECT id FROM usuarios WHERE id = :id"  # Verificación de que el usuario exista
    existe = await db.fetch_one(revision_query, values={"id": usuario_id})
    if not existe:
        raise HTTPException(
            status_code=404, detail=f"Usuario con id {usuario_id} no encontrado"
        )
    
    #verificar que el nuevo nombre no esté vacío
    if not usuario.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del usuario no puede estar vacío")
    #verificar que el nuevo email no esté vacío
    if not usuario.email.strip():
        raise HTTPException(status_code=400, detail="El email del usuario no puede estar vacío")
    #verificar que el nuevo rol no esté vacío
    if not usuario.rol.strip():
        raise HTTPException(status_code=400, detail="El rol del usuario no puede estar vacío")

    email_query = "SELECT id FROM usuarios WHERE email = :email AND id != :id"  # Verificación de que el nuevo email no esté ya en uso
    email_existe = await db.fetch_one(
        email_query, values={"email": usuario.email, "id": usuario_id}
    )
    if email_existe:
        raise HTTPException(
            status_code=400, detail=f"El email {usuario.email} ya está en uso"
        )

    try:
        query = """
            UPDATE usuarios
            SET nombre = :nombre,
                email = :email,
                rol = :rol
            WHERE id = :id
        """
        values = {**usuario.dict(), "id": usuario_id}
        await db.execute(query=query, values=values)
        return await get_usuario_by_id(usuario_id)

    except Exception as e:
        print(f"Error al actualizar usuario: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el usuario")


async def delete_usuario(
    id: int, usuario_actual
) -> dict:  # DELETE - Elimina el usuario con el id indicado - Soft delete
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar un usuario")

    revision_query = (
        "SELECT id FROM usuarios WHERE id = :id AND activo = true"  # Verifica que exista el usuario
    )
    existe = await db.fetch_one(revision_query, values={"id": id})
    if not existe:
        raise HTTPException(
            status_code=404, detail=f"Usuario con id {id} no encontrado o ya está eliminado"
        )

    try:
        query = "UPDATE usuarios SET activo = false WHERE id = :id"
        await db.execute(query=query, values={"id": id})
        return {"message": f"Usuario con id {id} eliminado correctamente"}

    except Exception as e:
        print(f"Error al eliminar usuario: {e}")
        raise HTTPException(status_code=400, detail="Error al eliminar el usuario")

async def restore_usuario(
    id: int, usuario_actual
) -> dict:  # PUT - Restaura el usuario con el id indicado
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para restaurar un usuario")

    revision_query = (
        "SELECT id FROM usuarios WHERE id = :id AND activo = false"  # Verifica que exista el usuario borrado
    )
    existe = await db.fetch_one(revision_query, values={"id": id})
    if not existe:
        raise HTTPException(
            status_code=404, detail=f"Usuario con id {id} no encontrado o ya está activo"
        )

    try:
        query = "UPDATE usuarios SET activo = true WHERE id = :id"
        await db.execute(query=query, values={"id": id})
        return {"message": f"Usuario con id {id} restaurado correctamente"}

    except Exception as e:
        print(f"Error al restaurar usuario: {e}")
        raise HTTPException(status_code=400, detail="Error al restaurar el usuario")
