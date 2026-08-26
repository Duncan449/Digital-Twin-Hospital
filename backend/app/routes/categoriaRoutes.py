from typing import List
from fastapi import APIRouter, Depends
from app.schemas.categoria import CategoriaIn, CategoriaOut
import app.services.categoria as service
from app.services.auth import require_auth

router = APIRouter()


@router.get(
    "/",
    response_model=List[CategoriaOut],
)
async def read_categorias(usuario_actual=Depends(require_auth)):
    return await service.get_all_categorias()

@router.get("/borrados", response_model=List[CategoriaOut])
async def read_categorias_borradas(usuario_actual=Depends(require_auth)):
    return await service.get_all_categorias_borradas(usuario_actual)


@router.post("/", response_model=CategoriaOut)
async def create_categoria(
    categoria: CategoriaIn, usuario_actual=Depends(require_auth)
):
    return await service.create_categoria(categoria, usuario_actual)


@router.put("/{id}", response_model=CategoriaOut)
async def update_categoria(
    id: int, categoria: CategoriaIn, usuario_actual=Depends(require_auth)
):
    return await service.update_categoria(id, categoria, usuario_actual)


@router.delete("/{id}")
async def delete_categoria(id: int, usuario_actual=Depends(require_auth)):
    return await service.delete_categoria(id, usuario_actual)

@router.put("/restaurar/{id}")
async def restore_categoria(id: int, usuario_actual=Depends(require_auth)):
    return await service.restore_categoria(id, usuario_actual)
