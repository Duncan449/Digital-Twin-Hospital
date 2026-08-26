from fastapi import APIRouter, Depends
from app.schemas.auth import Token
from app.schemas.usuario import UsuarioIn, UsuarioOut
import app.services.auth as service
from fastapi.security import OAuth2PasswordRequestForm

router = APIRouter()


@router.post("/login", response_model=Token)
async def login(form_data: OAuth2PasswordRequestForm = Depends()) -> Token:
    return await service.login_usuario(form_data.username, form_data.password)


@router.post(
    "/registro", response_model=UsuarioOut
)  # POST - Registrar un nuevo usuario
async def registro(usuario: UsuarioIn) -> UsuarioOut:
    return await service.registrar_usuario(
        usuario.nombre, usuario.email, usuario.password, usuario.rol
    )

@router.get("/me", response_model=UsuarioOut)
async def read_current_user(current_user=Depends(service.get_current_user)):
    return current_user
