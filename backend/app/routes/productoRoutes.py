from typing import List
from fastapi import APIRouter, Depends
from app.schemas.producto import ProductoIn, ProductoOut
import app.services.producto as service
from app.services.auth import require_auth

router = APIRouter()


@router.get(
    "/",
    response_model=List[ProductoOut],
)
async def read_productos(usuario_actual=Depends(require_auth)):
    return await service.get_all_productos()


@router.get("/borrados", response_model=List[ProductoOut])
async def read_productos_borrados(usuario_actual=Depends(require_auth)):
    return await service.get_all_productos_borrados(usuario_actual)


@router.post("/", response_model=ProductoOut)
async def create_producto(producto: ProductoIn, usuario_actual=Depends(require_auth)):
    return await service.create_producto(producto, usuario_actual)


@router.put("/{id}", response_model=ProductoOut)
async def update_producto(
    id: int, producto: ProductoIn, usuario_actual=Depends(require_auth)
):
    return await service.update_producto(id, producto, usuario_actual)


@router.delete("/{id}")
async def delete_producto(id: int, usuario_actual=Depends(require_auth)):
    return await service.delete_producto(id, usuario_actual)

@router.put("/restaurar/{id}")
async def restore_producto(id: int, usuario_actual=Depends(require_auth)):
    return await service.restore_producto(id, usuario_actual)   
