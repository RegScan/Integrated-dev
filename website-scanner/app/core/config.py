"""
配置管理模块
"""

import os
from typing import Optional, List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """应用配置类"""
    
    # 基础配置
    APP_NAME: str = "Website Scanner"
    VERSION: str = "1.0.0"
    DEBUG: bool = False
    TESTING: bool = False
    ENVIRONMENT: str = "development"
    
    # 服务器配置
    HOST: str = "0.0.0.0"
    PORT: int = 8001
    
    # 数据库配置
    MONGODB_URL: str = "mongodb://mongodb:27017/website_scanner"
    DATABASE_URL: str = "sqlite:///./data/website_scanner.db"
    
    # Redis配置（性能优化）
    REDIS_URL: str = "redis://redis:6379/1"
    REDIS_MAX_CONNECTIONS: int = 50
    REDIS_SOCKET_TIMEOUT: int = 5
    REDIS_SOCKET_CONNECT_TIMEOUT: int = 5
    REDIS_RETRY_ON_TIMEOUT: bool = True
    
    # 缓存配置（性能优化）
    CACHE_TTL: int = 3600  # 1小时
    CACHE_SCAN_RESULT_TTL: int = 86400  # 24小时
    CACHE_BEIAN_INFO_TTL: int = 604800  # 7天
    CACHE_WEBSITE_INFO_TTL: int = 3600  # 1小时
    CACHE_ENABLED: bool = True
    
    # 数据库连接池配置（性能优化）
    DB_POOL_SIZE: int = 20
    DB_MAX_OVERFLOW: int = 30
    DB_POOL_RECYCLE: int = 3600
    DB_POOL_TIMEOUT: int = 30
    DB_POOL_PRE_PING: bool = True
    
    # API配置
    BEIAN_API_KEY: str = ""
    CONTENT_API_KEY: str = ""
    
    # 百度AI内容审核API配置
    BAIDU_API_KEY: str = ""
    BAIDU_SECRET_KEY: str = ""
    
    # 阿里云内容安全API配置
    ALIYUN_ACCESS_KEY: str = ""
    ALIYUN_SECRET_KEY: str = ""
    ALIYUN_REGION: str = "cn-shanghai"
    
    # 扫描配置
    MAX_CONCURRENT_SCANS: int = 5  # 降低默认并发数
    MIN_CONCURRENT_SCANS: int = 1  # 最小并发数
    CONCURRENT_SCALE_FACTOR: float = 0.8  # 并发数缩放因子
    SCAN_TIMEOUT: int = 30
    MAX_IMAGES_PER_SITE: int = 5
    MAX_PAGES_PER_SITE: int = 10
    
    # 爬虫配置（性能优化）
    CRAWLER_TIMEOUT: int = 30
    CRAWLER_RETRY_TIMES: int = 3
    CRAWLER_RETRY_DELAY: int = 5
    CRAWLER_USER_AGENT: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
    
    # 浏览器配置（性能优化 + OOM防护）
    BROWSER_HEADLESS: bool = True
    BROWSER_TIMEOUT: int = 10000
    BROWSER_WAIT_TIMEOUT: int = 5000
    BROWSER_VIEWPORT_SIZE: dict = {"width": 1920, "height": 1080}

    # OOM防护配置
    MEMORY_MAX_PERCENT: float = 80.0  # 最大内存使用率
    MEMORY_CHECK_INTERVAL: int = 5  # 内存检查间隔（秒）
    MEMORY_WAIT_TIMEOUT: int = 30  # 内存等待超时（秒）
    BROWSER_MAX_MEMORY_MB: int = 512  # 单个浏览器最大内存使用（MB）
    BROWSER_MAX_IMAGES: int = 3  # 最大图片数量（减少内存使用）
    BROWSER_MAX_TEXT_LENGTH: int = 10000  # 最大文本长度
    BROWSER_DISABLE_JS: bool = False  # 是否禁用JavaScript
    BROWSER_DISABLE_IMAGES: bool = False  # 是否禁用图片加载
    BROWSER_DISABLE_CSS: bool = False  # 是否禁用CSS
    
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
    CRAWLER_RESPONSE_TIME_THRESHOLD: float = 10.0  # 10秒
    
    # 异步任务配置
    ASYNC_TASK_ENABLED: bool = True
    ASYNC_TASK_WORKERS: int = 4
    ASYNC_TASK_QUEUE_SIZE: int = 1000
    
    # 日志配置
    LOG_LEVEL: str = "INFO"
    LOG_FORMAT: str = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    
    # 内存管理配置
    CLEANUP_INTERVAL: int = 300  # 内存清理间隔（秒）
    MAX_MEMORY_USAGE: int = 80   # 最大内存使用率（%）
    MEMORY_WARNING_THRESHOLD: int = 70  # 内存警告阈值（%）
    LOG_FILE: str = "logs/website_scanner.log"
    
    # CORS配置
    ALLOWED_ORIGINS: List[str] = ["*"]
    ALLOWED_HOSTS: List[str] = ["*"]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# 全局配置实例
settings = Settings()

def get_cache_config() -> dict:
    """获取缓存配置"""
    return {
        "default_ttl": settings.CACHE_TTL,
        "scan_result_ttl": settings.CACHE_SCAN_RESULT_TTL,
        "beian_info_ttl": settings.CACHE_BEIAN_INFO_TTL,
        "website_info_ttl": settings.CACHE_WEBSITE_INFO_TTL,
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

def get_crawler_config() -> dict:
    """获取爬虫配置"""
    return {
        "timeout": settings.CRAWLER_TIMEOUT,
        "retry_times": settings.CRAWLER_RETRY_TIMES,
        "retry_delay": settings.CRAWLER_RETRY_DELAY,
        "user_agent": settings.CRAWLER_USER_AGENT,
        "max_images": settings.MAX_IMAGES_PER_SITE,
        "max_pages": settings.MAX_PAGES_PER_SITE
    }

def get_browser_config() -> dict:
    """获取浏览器配置"""
    return {
        "headless": settings.BROWSER_HEADLESS,
        "timeout": settings.BROWSER_TIMEOUT,
        "wait_timeout": settings.BROWSER_WAIT_TIMEOUT,
        "viewport_size": settings.BROWSER_VIEWPORT_SIZE
    }