from typing import List
from fastapi import HTTPException
from app.config.database import db
from app.schemas.movimiento_inventario import MovimientoInventarioIn, MovimientoInventarioOut


# Función auxiliar
async def get_movimiento_by_id(
    id: int,
) -> MovimientoInventarioOut:  # GET - Trae un movimiento por id
    try:
        if id <= 0:
            raise HTTPException(status_code=400, detail="ID inválido")

        query = "SELECT * FROM movimientos_inventario WHERE id = :id"
        row = await db.fetch_one(query=query, values={"id": id})

        if not row:
            raise HTTPException(status_code=404, detail="Movimiento no encontrado")

        return row

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al obtener movimiento: {e}")
        raise HTTPException(status_code=500, detail=f"Error al obtener movimiento: {e}")


# CRUD MOVIMIENTOS INVENTARIO

async def get_all_movimientos(usuario_actual) -> List[dict]: # GET - Trae todos los movimientos de inventario con nombre de usuario
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para ver los movimientos de inventario")
    
    try:
        
        query = """
            SELECT 
                mi.*,
                u.nombre AS nombre_usuario
            FROM movimientos_inventario mi
            LEFT JOIN usuarios u ON mi.fk_usuario = u.id
            ORDER BY mi.fecha_movimiento DESC
        """
        rows = await db.fetch_all(query=query)
        return rows

    except Exception as e:
        print(f"Error al obtener movimientos: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error al obtener movimientos: {e}"
        )

async def get_movimientos_por_usuario(fk_usuario: int, usuario_actual) -> List[dict]: # GET - Trae todos los movimientos de inventario de un usuario específico con nombre
   
    if usuario_actual["rol"] != "admin" and usuario_actual["id"] != fk_usuario:  # Solo admin o el mismo usuario pueden ver sus movimientos
        raise HTTPException(status_code=403, detail="No tienes permiso para ver los movimientos de este usuario")

    try:
        
        query = """
            SELECT 
                mi.*,
                u.nombre AS nombre_usuario
            FROM movimientos_inventario mi 
            LEFT JOIN usuarios u ON mi.fk_usuario = u.id
            WHERE mi.fk_usuario = :fk_usuario 
            ORDER BY mi.fecha_movimiento DESC
        """
        rows = await db.fetch_all(query=query, values={"fk_usuario": fk_usuario})
        return rows
        

    except Exception as e:
        print(f"Error al obtener movimientos del usuario {fk_usuario}: {e}")
        raise HTTPException(
            status_code=500, detail=f"Error al obtener movimientos del usuario: {e}"
        )


async def create_movimiento(
    movimiento: MovimientoInventarioIn, usuario_actual
) -> MovimientoInventarioOut:   # POST - Crea un nuevo movimiento de inventario usando un stored procedure

    # Validación de permiso para crear movimiento
    if (
        usuario_actual["rol"] != "admin"
        and usuario_actual["id"] != movimiento.fk_usuario
    ):
        raise HTTPException(
            status_code=403,
            detail="No tienes permiso para crear un movimiento para otro usuario",
        )

    try:
        # Llamar al stored procedure
        query = """
            CALL procesar_movimiento_inventario(
                :p_fk_producto,
                :p_fk_almacen,
                :p_tipo_movimiento,
                :p_cantidad,
                :p_motivo,
                :p_fk_usuario,
                :p_fk_proveedor,
                @p_resultado,
                @p_nuevo_movimiento_id
            )
        """

        await db.execute(
            query=query,
            values={
                "p_fk_producto": movimiento.fk_producto,
                "p_fk_almacen": movimiento.fk_almacen,
                "p_tipo_movimiento": movimiento.tipo_movimiento.lower(),
                "p_cantidad": movimiento.cantidad,
                "p_motivo": movimiento.motivo,
                "p_fk_usuario": movimiento.fk_usuario,
                "p_fk_proveedor": movimiento.fk_proveedor,
            },
        )

        # Obtener los valores de salida del SP
        result_query = (
            "SELECT @p_resultado as resultado, @p_nuevo_movimiento_id as movimiento_id"
        )
        result = await db.fetch_one(result_query)

        # Si el SP retornó un error, lanzar excepción con el mensaje
        if result["resultado"] != "SUCCESS":
            raise HTTPException(status_code=400, detail=result["resultado"])

        # Retornar el movimiento creado
        return await get_movimiento_by_id(result["movimiento_id"])

    except HTTPException:
        raise
    except Exception as e:
        print(f"Error al procesar movimiento: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al procesar el movimiento. Intente nuevamente.",
        )
