from pydantic_settings import BaseSettings
from typing import Optional, List
import os

class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "Config Manager"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    ENVIRONMENT: str = "development"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8000
    
    # 数据库配置
    DATABASE_URL: str = "sqlite:///./data/config.db"
    
    # Redis配置（性能优化）
    REDIS_URL: Optional[str] = "redis://redis:6379/0"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    
    # 缓存配置（性能优化）
    CACHE_TTL: int = 3600  # 1小时
    CACHE_CONFIG_TTL: int = 1800  # 30分钟
    CACHE_USER_TTL: int = 7200  # 2小时
    CACHE_TEMPLATE_TTL: int = 86400  # 24小时
    CACHE_ENABLED: bool = True
    
    # 数据库连接池配置（性能优化）
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True
    
    # 安全配置
    SECRET_KEY: str = "your-secret-key-here"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    # 配置文件路径
    CONFIG_DIR: str = "configs"
    DEFAULT_CONFIG: str = "default.yaml"
    DEVELOPMENT_CONFIG: str = "development.yaml"
    PRODUCTION_CONFIG: str = "production.yaml"
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    LOG_FILE: str = "logs/config-manager.log"
    
    # 限流配置
    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_REQUESTS_PER_MINUTE: int = 60
    RATE_LIMIT_BURST_SIZE: int = 10
    
    # 监控配置
    METRICS_ENABLED: bool = True
    HEALTH_CHECK_INTERVAL: int = 30
    
    # 性能监控配置
    PERFORMANCE_MONITORING: bool = True
    SLOW_QUERY_THRESHOLD: float = 1.0  # 1秒
    API_RESPONSE_TIME_THRESHOLD: float = 0.5  # 500ms
    
    # 异步任务配置
    ASYNC_TASK_ENABLED: bool = True
    ASYNC_TASK_WORKERS: int = 4
    ASYNC_TASK_QUEUE_SIZE: int = 1000
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 创建全局设置实例
settings = Settings()

# 环境变量配置
def get_config_path() -> str:
    """根据环境获取配置文件路径"""
    env = os.getenv("ENVIRONMENT", "development").lower()
    
    if env == "production":
        return settings.PRODUCTION_CONFIG
    elif env == "development":
        return settings.DEVELOPMENT_CONFIG
    else:
        return settings.DEFAULT_CONFIG

def get_database_url() -> str:
    """获取数据库连接URL"""
    return os.getenv("DATABASE_URL", settings.DATABASE_URL)

def get_secret_key() -> str:
    """获取密钥"""
    return os.getenv("SECRET_KEY", settings.SECRET_KEY)

def get_redis_url() -> str:
    """获取Redis连接URL"""
    return os.getenv("REDIS_URL", settings.REDIS_URL)

def get_cache_config() -> dict:
    """获取缓存配置"""
    return {
        "default_ttl": settings.CACHE_TTL,
        "config_ttl": settings.CACHE_CONFIG_TTL,
        "user_ttl": settings.CACHE_USER_TTL,
        "template_ttl": settings.CACHE_TEMPLATE_TTL,
        "enabled": settings.CACHE_ENABLED
    }

def get_db_pool_config() -> dict:
    """获取数据库连接池配置"""
    return {
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_recycle": settings.DB_POOL_RECYCLE,
        "pool_timeout": settings.DB_POOL_TIMEOUT,
        "pool_pre_ping": settings.DB_POOL_PRE_PING
    } 