"""Application configuration using Pydantic Settings."""

from typing import List, Optional
from pydantic import AnyHttpUrl, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # General Project Info
    PROJECT_NAME: str = "DOC_Intelligence Backend"
    API_V1_STR: str = "/api/v1"
    DEBUG: bool = False

    # Security & Tokens
    SECRET_KEY: str = "super-secret-key-change-in-production-use-strong-random-bytes"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24  # 1 day
    COLLECTION_LINK_EXPIRE_HOURS: int = 48  # RN-12: 48 hours for public collection links

    # CORS
    BACKEND_CORS_ORIGINS: List[str] = ["*"]

    # Database
    POSTGRES_SERVER: str = "localhost"
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "doc_intelligence"
    DATABASE_URL: Optional[str] = None
    SYNC_DATABASE_URL: Optional[str] = None

    @computed_field
    def async_database_url(self) -> str:
        if self.DATABASE_URL:
            return self.DATABASE_URL
        return (
            f"postgresql+asyncpg://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    @computed_field
    def sync_database_url(self) -> str:
        if self.SYNC_DATABASE_URL:
            return self.SYNC_DATABASE_URL
        return (
            f"postgresql+psycopg2://{self.POSTGRES_USER}:{self.POSTGRES_PASSWORD}"
            f"@{self.POSTGRES_SERVER}:{self.POSTGRES_PORT}/{self.POSTGRES_DB}"
        )

    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0
    REDIS_URL: Optional[str] = None

    @computed_field
    def redis_connection_url(self) -> str:
        if self.REDIS_URL:
            return self.REDIS_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    # Celery
    CELERY_BROKER_URL: Optional[str] = None
    CELERY_RESULT_BACKEND: Optional[str] = None

    @computed_field
    def celery_broker(self) -> str:
        if self.CELERY_BROKER_URL:
            return self.CELERY_BROKER_URL
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/1"

    @computed_field
    def celery_backend(self) -> str:
        if self.CELERY_RESULT_BACKEND:
            return self.CELERY_RESULT_BACKEND
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/2"

    # MinIO / S3 Storage
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: str = "minioadmin"
    MINIO_SECRET_KEY: str = "minioadmin"
    MINIO_BUCKET_NAME: str = "doc-intelligence-storage"
    MINIO_SECURE: bool = False
    MINIO_PUBLIC_URL: str = "http://localhost:9000"

    # Business Rules (regras_negocio.md RN-01 a RN-08)
    OCR_ENGINE: str = "easyocr"  # Strategy: 'easyocr' (PyTorch CRAFT) ou 'mock' (80% sucesso / 20% revisão manual)
    OCR_CONFIDENCE_THRESHOLD: float = 0.85  # RN-01: 85% minimum required for auto-approval
    TEMPLATE_DEDUCTION_THRESHOLD: float = 0.90  # RN-02: 90% confidence for auto-template deduction
    FUZZY_MATCH_MIN_RATIO: float = 0.80  # RN-03: 80% Levenshtein threshold
    FUZZY_MATCH_MAX_AUTO_RATIO: float = 0.99  # RN-03: 80%-99% auto-corrects
    LOCK_TTL_SECONDS: int = 600  # RN-08: 10 minutes (600s) TTL for pessimistic lock

    # File Inspection & Security Limits
    MAX_FILE_SIZE_BYTES: int = 25 * 1024 * 1024  # 25 MB
    MAX_IMAGE_PIXELS: int = 89_000_000  # Decompression Bomb prevention limit
    MAX_PDF_PAGES: int = 10
    PDF_RASTERIZE_DPI: int = 300  # RN-06: 300 DPI mandatory

    # Initial Superuser Seeding
    FIRST_SUPERUSER_EMAIL: str = "admin@docintelligence.com"
    FIRST_SUPERUSER_PASSWORD: str = "adminpassword123"


settings = Settings()
