from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    app_name: str = "QA Testing API"
    debug: bool = False

    database_url: str = "postgresql://qa_user:qa_password@db:5432/qa_db"

    secret_key: str = "qa-testing-secret-key-change-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440  # 24 hours for QA convenience

    class Config:
        env_file = ".env"


settings = Settings()
