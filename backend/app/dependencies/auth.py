import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.config.database import get_db
from app.core.security import decodificar_token
from app.models.usuarios import Usuario
from app.services.usuarios_service import obtener_usuario_por_id

# OAuth2PasswordBearer no hace magia: solo le dice a FastAPI DÓNDE espera
# encontrar el token (header "Authorization: Bearer <token>") y qué endpoint
# documentar en Swagger como el que emite ese token. tokenUrl apunta a la
# ruta de login que armamos en el próximo paso.
esquema_oauth2 = OAuth2PasswordBearer(tokenUrl="/auth/login")


async def get_current_user(
    token: str = Depends(esquema_oauth2),
    db: AsyncSession = Depends(get_db),
) -> Usuario:
    """
    Dependencia base para cualquier endpoint protegido.

    Flujo: toma el token del header -> lo decodifica y verifica firma/expiración
    -> busca en DB el usuario que dice ser -> lo devuelve. Si cualquier paso
    falla, corta con 401 antes de que el endpoint se ejecute.

    Nota: SIEMPRE volvemos a buscar el usuario en la DB (no confiamos
    ciegamente en lo que dice el token) para poder chequear 'activo' y traer
    el rol/permisos actualizados -- si alguien fue desactivado hace 2 minutos,
    su token viejo no le sigue sirviendo.
    """
    credenciales_invalidas = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="No se pudieron validar las credenciales.",
        headers={"WWW-Authenticate": "Bearer"},
    )

    payload = decodificar_token(token)
    if payload is None:
        raise credenciales_invalidas

    usuario_id_str = payload.get("sub")
    if usuario_id_str is None:
        raise credenciales_invalidas

    try:
        usuario_id = uuid.UUID(usuario_id_str)
    except ValueError:
        raise credenciales_invalidas

    usuario = await obtener_usuario_por_id(db, usuario_id)
    if usuario is None:
        raise credenciales_invalidas

    if not usuario.activo:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="El usuario está inactivo.",
        )

    return usuario


def require_permiso(permiso: str):
    """
    Factory de dependencias: devuelve una dependencia específica para el
    permiso pedido, ej: Depends(require_permiso("pacientes:crear")).

    Chequea el JSONB de Rol.permisos. Como tu rol 'admin' está cargado con
    {"todo": true} en vez de listar cada permiso, primero probamos esa
    clave comodín antes de buscar el permiso puntual -- así no hace falta
    mantener una lista gigante de permisos para el admin.
    """

    def dependencia(usuario_actual: Usuario = Depends(get_current_user)) -> Usuario:
        permisos = usuario_actual.rol.permisos or {}

        tiene_acceso = permisos.get("todo", False) or permisos.get(permiso, False)

        if not tiene_acceso:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"No tenés permiso para: {permiso}",
            )
        return usuario_actual

    return dependencia