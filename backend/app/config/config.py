from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centraliza la configuración leída desde el archivo .env.
    Pydantic valida que estas variables existan al arrancar la app, sino levanta un error.
    """

    database_url: str

    # --- Configuración de autenticación (JWT) ---
    secret_key: str  # clave para firmar los tokens. Generarla con: openssl rand -hex 32
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
