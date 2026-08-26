from typing import List
from fastapi import HTTPException
from app.config.database import db
from app.schemas.producto import ProductoIn, ProductoOut


# Función auxiliar
async def get_producto_by_id(
    id: int,
) -> ProductoOut:  # GET - Trae al producto con el id indicado
    query = "SELECT * FROM productos WHERE id = :id"
    row = await db.fetch_one(query=query, values={"id": id})
    if not row:
        raise HTTPException(status_code=404, detail="Producto no encontrado")
    return row


# VALIDACIONES


def validar_precios(precio_compra: float, precio_venta: float):
    # Los precios deben ser positivos y el de venta mayor al de compra

    if precio_compra <= 0:
        raise HTTPException(
            status_code=400, detail="El precio de compra debe ser mayor a 0"
        )

    if precio_venta <= 0:
        raise HTTPException(
            status_code=400, detail="El precio de venta debe ser mayor a 0"
        )

    if precio_venta <= precio_compra:
        raise HTTPException(
            status_code=400,
            detail="El precio de venta debe ser mayor al precio de compra",
        )


def validar_stock_minimo(stock_minimo: int):
    # El stock mínimo no puede ser negativo
    if stock_minimo < 0:
        raise HTTPException(
            status_code=400, detail="El stock mínimo no puede ser negativo"
        )


async def validar_categoria(fk_categoria: int):
    # Valida si la categoría existe
    categoria_query = "SELECT id FROM categorias WHERE id = :id AND activa = true"
    categoria_existe = await db.fetch_one(categoria_query, values={"id": fk_categoria})
    if not categoria_existe:
        raise HTTPException(
            status_code=400,
            detail=f"La categoría con id {fk_categoria} no existe",
        )


async def validar_proveedor(fk_proveedor: int):
    # Valida si el proveedor existe
    proveedor_query = "SELECT id FROM proveedores WHERE id = :id AND activo = true"
    proveedor_existe = await db.fetch_one(proveedor_query, values={"id": fk_proveedor})
    if not proveedor_existe:
        raise HTTPException(
            status_code=400,
            detail=f"El proveedor con id {fk_proveedor} no existe",
        )


# CRUD PRODUCTO


async def get_all_productos() -> (
    List[ProductoOut]
):  # GET - Trae a todos los productos visibles de la BD
    try:
        query = "SELECT * FROM productos WHERE activo = true"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        print(f"Error al obtener productos: {e}")
        raise HTTPException(
            status_code=500, detail="Error al obtener los productos. Intente nuevamente."
        )

async def get_all_productos_borrados(usuario_actual) -> (
    List[ProductoOut]
):  # GET - Trae a todos los productos borrados de la BD
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para ver los productos borrados")

    try:
        query = "SELECT * FROM productos WHERE activo = false"
        rows = await db.fetch_all(query=query)
        return rows
    except Exception as e:
        print(f"Error al obtener productos borrados: {e}")
        raise HTTPException(
            status_code=500, detail="Error al obtener los productos borrados. Intente nuevamente."
        )


async def create_producto(
    producto: ProductoIn, usuario_actual
) -> ProductoOut:  # POST - Crea un producto
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para crear productos")
    
    #verificar que el nombre no esté vacío
    if not producto.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del producto no puede estar vacío")
    
    #verificar que el código no esté vacío
    if not producto.codigo.strip():
        raise HTTPException(status_code=400, detail="El código del producto no puede estar vacío")    

    validar_precios(producto.precio_compra, producto.precio_venta)
    validar_stock_minimo(producto.stock_minimo)
    await validar_categoria(producto.fk_categoria)
    await validar_proveedor(producto.fk_proveedor)

    revision_query = "SELECT id FROM productos WHERE codigo = :codigo"
    existe = await db.fetch_one(
        revision_query, values={"codigo": producto.codigo}
    )  # Verificación de que el producto no esté ya registrado
    if existe:
        raise HTTPException(
            status_code=400,
            detail=f"El producto {producto.codigo} ya está registrado",
        )

    try:
        query = """
            INSERT INTO productos (codigo, nombre, descripcion, precio_compra, precio_venta, fk_categoria, fk_proveedor, stock_minimo, activo)
            VALUES (:codigo, :nombre, :descripcion, :precio_compra, :precio_venta, :fk_categoria, :fk_proveedor, :stock_minimo, :activo)
        """
        last_record_id = await db.execute(query=query, values=producto.dict())
        return await get_producto_by_id(last_record_id)

    except Exception as e:
        print(f"Error al crear el producto: {e}")
        raise HTTPException(
            status_code=500, detail="Error al crear el producto. Intente nuevamente."
        )


async def update_producto(
    producto_id: int, producto: ProductoIn, usuario_actual
) -> ProductoOut:  # PUT - Modifica el producto con el id indicado

    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para modificar productos")
    
    #verificar que el nombre no esté vacío
    if not producto.nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del producto no puede estar vacío")
    
    #verificar que el código no esté vacío
    if not producto.codigo.strip():
        raise HTTPException(status_code=400, detail="El código del producto no puede estar vacío")

    validar_precios(producto.precio_compra, producto.precio_venta)
    validar_stock_minimo(producto.stock_minimo)
    await validar_categoria(producto.fk_categoria)
    await validar_proveedor(producto.fk_proveedor)

    revision_query = "SELECT id FROM productos WHERE id = :id"  # Verificación de que el producto exista
    existing = await db.fetch_one(revision_query, values={"id": producto_id})
    if not existing:
        raise HTTPException(
            status_code=404, detail=f"Producto con id {producto_id} no encontrado"
        )

    codigo_query = "SELECT id FROM productos WHERE codigo = :codigo AND id != :id"  # Para evitar ponerle el codigo de un producto ya existente
    codigo_exists = await db.fetch_one(
        codigo_query, values={"codigo": producto.codigo, "id": producto_id}
    )
    if codigo_exists:
        raise HTTPException(
            status_code=400, detail=f"Ya existe un producto llamado {producto.codigo}"
        )

    try:
        query = """
            UPDATE productos
            SET codigo = :codigo,
                nombre = :nombre,
                descripcion = :descripcion,
                precio_compra = :precio_compra,
                precio_venta = :precio_venta,
                fk_categoria = :fk_categoria,
                fk_proveedor = :fk_proveedor,
                stock_minimo = :stock_minimo,
                activo = :activo
            WHERE id = :id
        """
        values = {**producto.dict(), "id": producto_id}
        await db.execute(query=query, values=values)
        return await get_producto_by_id(producto_id)

    except Exception as e:
        print(f"Error al actualizar producto: {e}")
        raise HTTPException(status_code=500, detail="Error al actualizar el producto")


async def delete_producto(
    id: int, usuario_actual
) -> dict:  # DELETE - Elimina el producto con el id indicado - Soft delete
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para eliminar productos")

    revision_query = (
        "SELECT id FROM productos WHERE id = :id AND activo = true"  # Verifica que exista el producto
    )
    existe = await db.fetch_one(revision_query, values={"id": id})
    if not existe:
        raise HTTPException(
            status_code=404, detail=f"Producto con id {id} no encontrado o ya está eliminado"
        )

    try:
        query = "UPDATE productos SET activo = false WHERE id = :id"
        await db.execute(query=query, values={"id": id})
        return {"message": f"Producto con id {id} eliminado correctamente"}

    except Exception as e:
        print(f"Error al eliminar producto: {e}")
        raise HTTPException(status_code=400, detail="Error al eliminar el producto")

async def restore_producto(
    id: int, usuario_actual
) -> dict:  # POST- Restaurar un producto borrado 
    
    if usuario_actual["rol"] != "admin":
        raise HTTPException(status_code=403, detail="No tienes permiso para restaurar productos")

    revision_query = (
        "SELECT id FROM productos WHERE id = :id AND activo = false"  # Verifica que exista el producto
    )
    existe = await db.fetch_one(revision_query, values={"id": id})
    if not existe:
        raise HTTPException(
            status_code=404, detail=f"Producto con id {id} no encontrado o ya está activo"
        )

    try:
        query = "UPDATE productos SET activo = true WHERE id = :id"
        await db.execute(query=query, values={"id": id})
        return {"message": f"Producto con id {id} restaurado correctamente"}

    except Exception as e:
        print(f"Error al restaurar producto: {e}")
        raise HTTPException(status_code=400, detail="Error al restaurar el producto")
