"""
应用配置管理
"""
from pydantic_settings import BaseSettings
from typing import Optional
import os


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用设置
    APP_NAME: str = "AI Gateway"
    APP_ENV: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = "your-secret-key-change-in-production"
    
    # 数据库设置
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/ai_gateway"
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis 设置
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    
    # 安全设置
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRATION_MINUTES: int = 1440
    API_KEY_PREFIX: str = "sk-"
    
    # 限流设置
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_BURST: int = 100
    
    # Model Provider 设置
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_BASE_URL: str = "https://api.openai.com/v1"
    
    CLAUDE_API_KEY: Optional[str] = None
    CLAUDE_BASE_URL: str = "https://api.anthropic.com/v1"
    
    # 日志设置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "json"
    
    # 监控设置
    PROMETHEUS_PORT: int = 9090
    
    class Config:
        env_file = ".env"
        case_sensitive = True


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """获取配置实例"""
    return settings
