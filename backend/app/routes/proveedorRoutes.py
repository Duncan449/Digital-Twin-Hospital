# backend/app/routes/proveedorRoutes.py
from typing import List
from fastapi import APIRouter, Depends
from app.schemas.proveedor import ProveedorIn, ProveedorOut
import app.services.proveedor as service
from app.services.auth import require_auth

router = APIRouter()


@router.get("/", response_model=List[ProveedorOut])
async def read_proveedores(usuario_actual=Depends(require_auth)):
    return await service.get_all_proveedores()


@router.get("/borrados", response_model=List[ProveedorOut])
async def read_proveedores_borrados(usuario_actual=Depends(require_auth)):
    return await service.get_all_proveedores_borrados(usuario_actual)


@router.post("/", response_model=ProveedorOut)
async def create_proveedor(
    proveedor: ProveedorIn, usuario_actual=Depends(require_auth)
):
    return await service.create_proveedor(proveedor, usuario_actual)


@router.put("/{id}", response_model=ProveedorOut)
async def update_proveedor(
    id: int, proveedor: ProveedorIn, usuario_actual=Depends(require_auth)
):
    return await service.update_proveedor(id, proveedor, usuario_actual)


@router.delete("/{id}")
async def delete_proveedor(id: int, usuario_actual=Depends(require_auth)):
    return await service.delete_proveedor(id, usuario_actual)

@router.put("/restaurar/{id}")
async def restore_proveedor(id: int, usuario_actual=Depends(require_auth)):
    return await service.restore_proveedor(id, usuario_actual)
