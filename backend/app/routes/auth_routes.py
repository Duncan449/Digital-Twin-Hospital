from fastapi import APIRouter, Depends
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.core.security import crear_token_acceso
from app.schemas.usuarios import Token, UsuarioLogin
from app.services.usuarios_service import autenticar_usuario

router = APIRouter(prefix="/auth", tags=["Autenticación"])


@router.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    db: AsyncSession = Depends(get_db),
):
    """
    Login. Usa OAuth2PasswordRequestForm (no nuestro schema UsuarioLogin)
    porque es el formato que espera el botón "Authorize" de Swagger y el
    estándar OAuth2 que declaramos en esquema_oauth2 -- FastAPI arma
    automáticamente el formulario correcto en /docs para probarlo ahí mismo.

    form_data.username en este caso es el EMAIL (OAuth2 llama "username"
    al campo, aunque nosotros lo usemos como email).
    """
    datos_login = UsuarioLogin(email=form_data.username, password=form_data.password)
    usuario = await autenticar_usuario(db, datos_login)

    # 'sub' (subject) es el claim estándar de JWT para "de quién es este
    # token". Guardamos el id como string porque JWT solo serializa
    # tipos simples (UUID no es serializable directo a JSON).
    token = crear_token_acceso(data={"sub": str(usuario.id)})

    return Token(access_token=token)