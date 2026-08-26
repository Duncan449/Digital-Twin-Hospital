from typing import List
from fastapi import APIRouter, Depends
from app.schemas.almacen import AlmacenIn, AlmacenOut
import app.services.almacen as service
from app.services.auth import require_auth

router = APIRouter()


@router.get("/", response_model=List[AlmacenOut])
async def read_almacen(usuario_actual=Depends(require_auth)):
    return await service.get_all_almacenes()


@router.get("/borrados", response_model=List[AlmacenOut])
async def read_almacen_borrados(usuario_actual=Depends(require_auth)):
    return await service.get_all_almacenes_borrados(usuario_actual)


@router.post("/", response_model=AlmacenOut)
async def create_almacen(almacen: AlmacenIn, usuario_actual=Depends(require_auth)):
    return await service.create_almacen(almacen, usuario_actual)


@router.put("/{id}", response_model=AlmacenOut)
async def update_almacen(
    id: int, almacen: AlmacenIn, usuario_actual=Depends(require_auth)
):
    return await service.update_almacen(id, almacen, usuario_actual)


@router.delete("/{id}")
async def delete_almacen(id: int, usuario_actual=Depends(require_auth)):
    return await service.delete_almacen(id, usuario_actual)

@router.put("/restaurar/{id}")
async def restore_almacen(id: int, usuario_actual=Depends(require_auth)):
    return await service.restore_almacen(id, usuario_actual)
