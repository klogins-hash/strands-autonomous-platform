import os
from typing import List
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # Database
    database_url: str = "postgresql+asyncpg://user:password@localhost:5432/strands_platform"
    redis_url: str = "redis://localhost:6379/0"
    
    # AI Models
    anthropic_api_key: str
    openai_api_key: str
    openrouter_api_key: str = ""
    cohere_api_key: str = ""
    
    # Specialized Services
    cartesia_api_key: str = ""
    mem0_api_key: str = ""
    firecrawl_api_key: str = ""
    tavily_api_key: str = ""
    
    # Object Storage (MinIO)
    minio_endpoint: str = "localhost:9000"
    minio_access_key: str = "minioadmin"
    minio_secret_key: str = "minioadmin"
    minio_bucket_name: str = "strands-platform"
    minio_use_ssl: bool = False
    
    # E2B Sandboxes
    e2b_api_key: str
    
    # Security
    secret_key: str
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 30
    
    # Application
    debug: bool = True
    cors_origins: List[str] = ["http://localhost:3000", "http://localhost:5173"]
    max_concurrent_agents: int = 10
    sandbox_timeout: int = 3600
    llm_daily_limit: float = 50.00
    
    class Config:
        env_file = ".env"


settings = Settings()
