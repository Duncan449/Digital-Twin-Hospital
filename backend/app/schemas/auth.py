from pydantic import BaseModel, EmailStr


class Token(BaseModel):  # Definimos como es el token generado tras el login
    access_token: str
    token_type: str


class TokenData(BaseModel):  # Los datos que contendrá el token
    email: str | None = None


class UsuarioLogin(BaseModel):
    email: EmailStr
    password: str

    class Config:
        example = {"email": "usuario@example.com", "password": "micontraseña123"}
