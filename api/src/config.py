from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    environment: str = "development"
    postgres_host: str = "localhost"
    postgres_port: int = 5432
    postgres_db: str = "cerberusrisk"
    postgres_user: str = "cerberus"
    postgres_password: str = "devpassword"
    valkey_host: str = "localhost"
    valkey_port: int = 6379
    cors_origins: str = "http://localhost:8050"

    @property
    def database_url(self) -> str:
        return f"postgresql+psycopg://{self.postgres_user}:{self.postgres_password}@{self.postgres_host}:{self.postgres_port}/{self.postgres_db}"

    @property
    def is_production(self) -> bool:
        return self.environment == "production"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",")]


settings = Settings()
