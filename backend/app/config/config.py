from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centraliza la configuración leída desde el archivo .env.
    Pydantic valida que DATABASE_URL exista al arrancar la app: si falta,
    el servidor ni siquiera levanta (mejor fallar rápido que en runtime).
    """

    database_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
