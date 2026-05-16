from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int

    ETH_RPC_URL: str | None = None
    BSC_RPC_URL: str | None = None
    POLYGON_RPC_URL: str | None = None

    class Config:
        env_file = ".env"

settings = Settings()
