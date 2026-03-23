"""
核心配置模块
Core Configuration Module
"""

from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    """应用配置"""
    
    # 应用基本信息
    APP_NAME: str = "智慧农业平台"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    
    # 数据库配置
    DATABASE_URL: str = "postgresql://smartagri:smartagri_secret@localhost:5432/smart_agriculture"
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 10
    
    # Redis 配置
    REDIS_URL: str = "redis://localhost:6379/0"
    
    # RabbitMQ 配置
    RABBITMQ_URL: str = "amqp://smartagri:smartagri_secret@localhost:5672/"
    
    # JWT 配置
    SECRET_KEY: str = "your-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 120
    
    # MiniMax LLM 配置
    MINIMAX_API_KEY: str = ""
    MINIMAX_BASE_URL: str = "https://api.minimax.chat"
    MINIMAX_MODEL: str = "MiniMax-2.5"
    
    # CORS 配置
    CORS_ORIGINS: List[str] = ["*"]
    
    # MQTT 配置
    MQTT_BROKER_URL: str = "mqtt://localhost:1883"
    MQTT_BROKER_USERNAME: str = ""
    MQTT_BROKER_PASSWORD: str = ""
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
