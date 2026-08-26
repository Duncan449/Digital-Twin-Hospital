import jwt
from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, Depends
from fastapi.security import OAuth2PasswordBearer
from jwt.exceptions import InvalidTokenError, ExpiredSignatureError
from passlib.context import CryptContext
from app.config.database import db
from app.schemas.usuario import UsuarioOut
from app.services.usuario import get_usuario_by_id
import os
from dotenv import load_dotenv

load_dotenv()

# Configuración de JWT desde variables de entorno
SECRET_KEY = os.getenv("SECRET_KEY")
ALGORITHM = os.getenv("ALGORITHM")
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES"))

# Configuración de PassLib para hashing de contraseñas
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="auth/login")

# Funciones auxiliares de manejo de contraseñas


# Verifica si una contraseña coincide con su hash
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


# Encripta una contraseña usando bcrypt
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# Funciones auxiliares de manejo de tokens JWT


# Crea un token JWT con los datos proporcionados
def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    to_encode = data.copy()

    # Calcular tiempo de expiración
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(
            minutes=ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
    return encoded_jwt


# Valida el token JWT y devuelve el usuario asociado
async def get_user_from_token(token: str):
    credentials_exception = HTTPException(
        status_code=401,
        detail="No se pudieron validar las credenciales",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # Decodificar el token
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception

    except ExpiredSignatureError:
        raise HTTPException(
            status_code=401,
            detail="Sesión expirada, por favor vuelve a iniciar sesión",
            headers={"WWW-Authenticate": "Bearer"},
        )
    except InvalidTokenError:
        raise credentials_exception

    # Buscar usuario en la BD
    query = "SELECT id, nombre, email, rol FROM usuarios WHERE email = :email AND activo = true"
    usuario = await db.fetch_one(query, values={"email": email})

    if usuario is None:
        raise credentials_exception

    return dict(usuario)


# Dependency que requiere autenticación en los endpoints
async def require_auth(token: str = Depends(oauth2_scheme)):
    return await get_user_from_token(token)


# Logica de negocio


# Autentica un usuario y devuelve un token JWT si está activo
async def login_usuario(email: str, password: str) -> dict:
    # Buscar usuario por email
    query = "SELECT id, nombre, email, password_hash FROM usuarios WHERE email = :email AND activo = true"
    usuario = await db.fetch_one(query, values={"email": email})

    if not usuario:
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos ",
        )

    # Verificar contraseña
    if not verify_password(password, usuario["password_hash"]):
        raise HTTPException(
            status_code=401,
            detail="Email o contraseña incorrectos",
        )

    # Actualizar fecha de última sesión
    update_query = """
        UPDATE usuarios
        SET fecha_ultima_sesion = :fecha_ultima_sesion
        WHERE id = :id
    """
    await db.execute(
        query=update_query,
        values={"fecha_ultima_sesion": datetime.now(), "id": usuario["id"]},
    )

    # Crear token JWT
    access_token_expires = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = create_access_token(
        data={"sub": usuario["email"]}, expires_delta=access_token_expires
    )

    return {"access_token": access_token, "token_type": "bearer"}


# Registra un nuevo usuario y devuelve sus datos
async def registrar_usuario(
    nombre: str, email: str, password: str, rol: str
) -> UsuarioOut:

    # Verificar que el nombre no esté vacío
    if not nombre.strip():
        raise HTTPException(status_code=400, detail="El nombre del usuario no puede estar vacío")
    # Verificar que el email no esté vacío
    if not email.strip():
        raise HTTPException(status_code=400, detail="El email del usuario no puede estar vacío")
    # Verificar que la contraseña no esté vacía
    if not password.strip():
        raise HTTPException(status_code=400, detail="La contraseña del usuario no puede estar vacía")
    # Verificar que el rol no esté vacío
    if not rol.strip():
        raise HTTPException(status_code=400, detail="El rol del usuario no puede estar vacío")

    # Verificar que el correo no esté ya registrado
    revision_query = "SELECT id FROM usuarios WHERE email = :email"
    existe = await db.fetch_one(revision_query, values={"email": email})

    if existe:
        raise HTTPException(
            status_code=400,
            detail=f"El correo {email} ya está registrado",
        )

    # Hashear la contraseña
    password_hash = get_password_hash(password)

    try:
        # Insertar el nuevo usuario
        query = """
            INSERT INTO usuarios (nombre, email, password_hash, rol)
            VALUES (:nombre, :email, :password_hash, :rol)
        """
        values = {
            "nombre": nombre,
            "email": email,
            "password_hash": password_hash,
            "rol": rol,
        }

        last_record_id = await db.execute(query=query, values=values)

        # Devolver el usuario creado
        return await get_usuario_by_id(last_record_id)

    except Exception as e:
        print(f"Error al crear usuario: {e}")
        raise HTTPException(
            status_code=500,
            detail="Error al crear el usuario. Intente nuevamente.",
        )

#Obtener el usuario actual a partir del token
async def get_current_user(token: str = Depends(oauth2_scheme)):
    return await get_user_from_token(token)