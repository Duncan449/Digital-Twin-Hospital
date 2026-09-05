from datetime import datetime, timedelta, timezone

from jose import JWTError, jwt
from passlib.context import CryptContext

from app.config.config import settings

# CryptContext administra el algoritmo de hasheo. "bcrypt" es el esquema que
# elegiste; deprecated="auto" hace que si algún día migramos a otro esquema,
# passlib siga pudiendo VERIFICAR los hashes viejos sin romper nada.
contexto_hash = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hashear_password(password: str) -> str:
    """Convierte una contraseña en texto plano en un hash irreversible para guardar en la DB.
    Nunca se guarda ni se compara la contraseña original."""
    return contexto_hash.hash(password)


def verificar_password(password_plano: str, password_hash: str) -> bool:
    """Compara la contraseña que manda el usuario en el login contra el hash guardado."""
    return contexto_hash.verify(password_plano, password_hash)


def crear_token_acceso(data: dict) -> str:
    """
    Genera un JWT firmado. 'data' lleva el id del usuario (claim 'sub').

    La idea del JWT es que es AUTOCONTENIDO: una vez firmado, en cada
    request siguiente no consultamos la DB para saber "quién es" —
    solo verificamos la firma (con secret_key) y que no haya expirado.
    Eso es lo que lo hace rápido comparado con sesiones tradicionales.
    """
    a_codificar = data.copy()
    expira = datetime.now(timezone.utc) + timedelta(
        minutes=settings.access_token_expire_minutes
    )
    a_codificar.update({"exp": expira})
    return jwt.encode(a_codificar, settings.secret_key, algorithm=settings.algorithm)


def decodificar_token(token: str) -> dict | None:
    """Verifica firma y expiración. Si el token fue manipulado, es de otra
    secret_key, o ya expiró, jose tira JWTError y acá devolvemos None."""
    try:
        return jwt.decode(token, settings.secret_key, algorithms=[settings.algorithm])
    except JWTError:
        return None