from typing import List
from fastapi import APIRouter, Depends
from app.schemas.usuario import UsuarioOut, UsuarioUpdate
import app.services.usuario as service
from app.services.auth import require_auth

router = APIRouter()


@router.get(
    "/",
    response_model=List[UsuarioOut],
)
async def read_usuarios(usuario_actual=Depends(require_auth)):
    return await service.get_all_usuarios(usuario_actual)

@router.get(
    "/borrados",
    response_model=List[UsuarioOut],
)
async def read_usuarios_borrados(usuario_actual=Depends(require_auth)):
    return await service.get_all_usuarios_borrados(usuario_actual)


@router.put("/{id}", response_model=UsuarioOut)
async def update_usuario(
    id: int, usuario: UsuarioUpdate, usuario_actual=Depends(require_auth)
):
    return await service.update_usuario(id, usuario, usuario_actual)


@router.delete("/{id}")
async def delete_usuario(id: int, usuario_actual=Depends(require_auth)):
    return await service.delete_usuario(id, usuario_actual)

@router.put("/restaurar/{id}")
async def restore_usuario(id: int, usuario_actual=Depends(require_auth)):
    return await service.restore_usuario(id, usuario_actual)
