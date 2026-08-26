from typing import List
from fastapi import HTTPException
from app.config.database import db
from app.schemas.stock_almacen import Stock_AlmacenIn, Stock_AlmacenOut, StockConProductoOut, StockDetalladoOut, StockPorAlmacenOut, StockPorProductoOut


# Función auxiliar
async def get_stock_almacen_by_id(id: int) -> Stock_AlmacenOut:  #Trae el stock_almacen con el id indicado

    try:
        query = "SELECT * FROM stock_almacen WHERE id = :id"
        row = await db.fetch_one(query=query, values={"id": id})
        if not row:
            raise HTTPException(status_code=404, detail="Stock_almacen no encontrado")
        return row
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener el stock_almacen: {e}")

# CRUD STOCK_ALMACEN

async def get_stock_detallado() -> List[StockDetalladoOut]: # OBTENER un reporte detallado del stock en todos los almacenes, incluyendo el nombre del producto y del almacén, y la cantidad total disponible y reservada por producto en cada almacén
    query = """
        SELECT 
            p.nombre AS producto,
            a.nombre AS almacen,
            SUM(sa.cantidad_disponible) AS total_disponible,
            SUM(sa.cantidad_reservada) AS total_reservada
        FROM stock_almacen sa
        INNER JOIN productos p ON sa.fk_producto = p.id
        INNER JOIN almacenes a ON sa.fk_almacen = a.id
        GROUP BY p.nombre, a.nombre
        ORDER BY p.nombre, a.nombre
    """
    rows = await db.fetch_all(query=query)
    return rows


async def get_stock_con_producto(producto_id: int) -> List[StockConProductoOut]:  # OBTENER el stock de un producto específico junto con su nombre
    query = """
        SELECT sa.*, p.nombre AS nombre_producto
        FROM stock_almacen sa
        INNER JOIN productos p ON sa.fk_producto = p.id
        WHERE p.id = :producto_id
    """
    rows = await db.fetch_all(query=query, values={"producto_id": producto_id})
    return rows


async def get_stock_por_producto() -> List[StockPorProductoOut]:   # OBTENER la cantidad total disponible por producto en todos los almacenes
    query = """
        SELECT fk_producto, SUM(cantidad_disponible) AS total_disponible
        FROM stock_almacen
        GROUP BY fk_producto
    """
    rows = await db.fetch_all(query=query)
    return rows


async def get_stock_por_almacen(almacen_id: int) -> List[StockPorAlmacenOut]:   # OBTENER el stock de un almacén específico
    query = """
        SELECT 
            p.id AS fk_producto,
            p.codigo AS codigo_producto,
            p.nombre AS nombre_producto,
            sa.cantidad_disponible AS cantidad_disponible,
            sa.cantidad_reservada AS cantidad_reservada
        FROM stock_almacen sa
        INNER JOIN productos p ON sa.fk_producto = p.id
        WHERE sa.fk_almacen = :almacen_id
        ORDER BY p.nombre
    """
    rows = await db.fetch_all(query=query, values={"almacen_id": almacen_id})

    if not rows:
        raise HTTPException(
            status_code=404,
            detail=f"No se encontró stock en el almacén con id {almacen_id}",
        )

    return rows


async def create_stock_almacen(stock_almacen: Stock_AlmacenIn, usuario_actual) -> Stock_AlmacenOut:  # CREAR un nuevo registro en la tabla stock_almacen
    try:

        if usuario_actual["rol"] != "admin":
            raise HTTPException(status_code=403, detail="No tienes permiso para crear un stock_almacen")

        if stock_almacen.cantidad_disponible < 0:
            raise HTTPException(status_code=400, detail="La cantidad disponible no puede ser negativa")  # Validar que la cantidad no sea menor a 0 

        if stock_almacen.cantidad_reservada < 0:
            raise HTTPException(status_code=400, detail="La cantidad reservada no puede ser negativa")
        
        if stock_almacen.cantidad_reservada >= stock_almacen.cantidad_disponible:
            raise HTTPException(status_code=400, detail="La cantidad reservada no puede ser mayor a la cantidad disponible")  # Validar que la cantidad no sea mayor a la reservada
        
        # Verificar si ya existe un registro para el mismo producto en el mismo almacén
        check_query = "SELECT id FROM stock_almacen WHERE fk_producto = :fk_producto AND fk_almacen = :fk_almacen"
        existing = await db.fetch_one(check_query, values={
            "fk_producto": stock_almacen.fk_producto,
            "fk_almacen": stock_almacen.fk_almacen
        })
        if existing:
            raise HTTPException(
                status_code=400, 
                detail=f"Ya existe un registro de stock para el producto {stock_almacen.fk_producto} en el almacén {stock_almacen.fk_almacen}"
            )

        # Obtener stock mínimo del producto
        producto_query = "SELECT stock_minimo FROM productos WHERE id = :id"
        producto = await db.fetch_one(producto_query, values={"id": stock_almacen.fk_producto})
        
        if producto and producto["stock_minimo"] is not None:
            if stock_almacen.cantidad_disponible < producto["stock_minimo"]:
                raise HTTPException(
                    status_code=400, 
                    detail=f"La cantidad disponible ({stock_almacen.cantidad_disponible}) es menor al stock mínimo requerido ({producto['stock_minimo']}) para este producto"
                )

        query = """
            INSERT INTO stock_almacen (fk_producto, fk_almacen, cantidad_disponible, cantidad_reservada)
            VALUES (:fk_producto, :fk_almacen, :cantidad_disponible, :cantidad_reservada)
        """
        last_record_id = await db.execute(query=query, values=stock_almacen.dict())  # Crea y retorna el nuevo stock_almacén
        return await get_stock_almacen_by_id(last_record_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear stock_almacen: {e}")  


async def update_stock_almacen(stock_almacen_id: int, stock_almacen: Stock_AlmacenIn, usuario_actual) -> Stock_AlmacenOut:  # ACTUALIZAR un registro de stock_almacen
    try:

        if usuario_actual["rol"] != "admin":
            raise HTTPException(status_code=403, detail="No tienes permiso para actualizar un stock_almacen")

        if stock_almacen_id <= 0:  # Validar IDs negativos o cero
            raise HTTPException(status_code=400, detail="ID inválido")

        # Validar cambios de FK en UPDATE (evitar duplicados)
        current_query = "SELECT fk_producto, fk_almacen FROM stock_almacen WHERE id = :id"
        current = await db.fetch_one(current_query, values={"id": stock_almacen_id})
        
        if (stock_almacen.fk_producto != current["fk_producto"] or  # Si cambió el producto o el almacén, verificar que no exista la nueva combinación
            stock_almacen.fk_almacen != current["fk_almacen"]):
            
            check_query = """
                SELECT id FROM stock_almacen 
                WHERE fk_producto = :fk_producto 
                AND fk_almacen = :fk_almacen 
                AND id != :current_id
            """
            existing = await db.fetch_one(check_query, values={
                "fk_producto": stock_almacen.fk_producto,
                "fk_almacen": stock_almacen.fk_almacen,
                "current_id": stock_almacen_id
            })
            if existing:
                raise HTTPException(
                    status_code=400, 
                    detail=f"Ya existe un registro de stock para el producto {stock_almacen.fk_producto} en el almacén {stock_almacen.fk_almacen}"
                )
        
        if stock_almacen.cantidad_disponible < 0:
            raise HTTPException(status_code=400, detail="La cantidad disponible no puede ser negativa")  # Validar que la cantidad no sea menor a 0 

        if stock_almacen.cantidad_reservada < 0:
            raise HTTPException(status_code=400, detail="La cantidad reservada no puede ser negativa") 
        
        if stock_almacen.cantidad_reservada > stock_almacen.cantidad_disponible:        # Validar que la cantidad reservada no sea mayor a la disponible - overselling
            raise HTTPException(status_code=400, detail="La cantidad reservada no puede ser mayor a la cantidad disponible")  
        
        revision_query = "SELECT id FROM stock_almacen WHERE id = :id"
        existing = await db.fetch_one(revision_query, values={"id": stock_almacen_id})
        if not existing:
            raise HTTPException(
                status_code=404, detail=f"Stock_almacen con id {stock_almacen_id} no encontrado"
            )
        query = """
            UPDATE stock_almacen
            SET fk_producto = :fk_producto,
                fk_almacen = :fk_almacen,
                cantidad_disponible = :cantidad_disponible,
                cantidad_reservada = :cantidad_reservada
            WHERE id = :id
        """
        values = {**stock_almacen.dict(), "id": stock_almacen_id}
        await db.execute(query=query, values=values)
        return await get_stock_almacen_by_id(stock_almacen_id)
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar stock_almacen: {e}")

