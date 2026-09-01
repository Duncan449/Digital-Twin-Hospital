from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Centraliza la configuración leída desde el archivo .env.
    Pydantic valida que DATABASE_URL exista al arrancar la app, sino levanta un error.
    """

    database_url: str

    model_config = SettingsConfigDict(env_file=".env", extra="ignore") # Esta linea le dice a Pydantic que lea el archivo .env y que ignore cualquier variable de entorno que no esté definida en esta clase Settings.


settings = Settings()
