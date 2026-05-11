from functools import lru_cache
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "自媒体工作台接口"
    api_prefix: str = "/api/v1"
    cors_origins: List[str] = Field(default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"])
    connection_timeout_seconds: float = 3.0

    postgres_host: Optional[str] = None
    postgres_port: int = 5432
    postgres_user: Optional[str] = None
    postgres_password: Optional[str] = None
    postgres_database: str = "vo_mate"
    postgres_min_pool_size: int = 1
    postgres_max_pool_size: int = 5

    mongo_host: Optional[str] = None
    mongo_port: int = 27017
    mongo_user: Optional[str] = None
    mongo_password: Optional[str] = None
    mongo_database: str = "vo_mate"
    mongo_auth_source: str = "admin"

    redis_host: Optional[str] = None
    redis_port: int = 6379
    redis_database: int = 0
    redis_user: Optional[str] = None
    redis_password: Optional[str] = None

    milvus_host: Optional[str] = None
    milvus_port: int = 19530
    milvus_secure: bool = False
    milvus_token: Optional[str] = None
    milvus_database: Optional[str] = None

    llm_provider: str = "mock"
    deepseek_api_key: Optional[str] = None
    deepseek_base_url: str = "https://api.deepseek.com"
    deepseek_model: str = "deepseek-v4-flash"
    deepseek_timeout_seconds: float = 60.0

    embedding_provider: str = "mock"
    dashscope_api_key: Optional[str] = None
    dashscope_base_url: str = "https://dashscope.aliyuncs.com/api/v1"
    dashscope_embedding_model: str = "text-embedding-v3"
    dashscope_embedding_dimension: int = 1024

    sqladmin_enabled: bool = True
    sqladmin_title: str = "自媒体工作台后台"
    sqladmin_base_url: str = "/admin"
    sqladmin_auto_create_tables: bool = False
    sqladmin_auth_enabled: bool = True
    sqladmin_username: Optional[str] = None
    sqladmin_password: Optional[str] = None
    sqladmin_password_sha256: Optional[str] = None
    sqladmin_session_secret: Optional[str] = None
    sqladmin_role: str = "viewer"

    model_config = SettingsConfigDict(env_file=".env", env_prefix="VO_MATE_", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
