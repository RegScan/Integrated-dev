from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from sqlalchemy.pool import QueuePool
from datetime import datetime
from typing import Optional
import os
import logging
from functools import lru_cache
import redis
import json
from contextlib import contextmanager

from .config import get_database_url, get_redis_url

# 配置日志
logger = logging.getLogger(__name__)

# Redis缓存客户端
redis_client = None

def init_redis():
    """初始化Redis连接"""
    global redis_client
    try:
        redis_url = get_redis_url()
        redis_client = redis.from_url(
            redis_url,
            decode_responses=True,
            max_connections=50,
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        # 测试连接
        redis_client.ping()
        logger.info("Redis连接初始化成功")
        return True
    except Exception as e:
        logger.error(f"Redis连接初始化失败: {e}")
        return False

# 缓存配置
CACHE_CONFIG = {
    "default_ttl": 3600,  # 1小时
    "config_ttl": 1800,   # 30分钟
    "user_ttl": 7200,     # 2小时
    "template_ttl": 86400, # 24小时
}

class CacheKeys:
    """缓存键设计"""
    CONFIG = "config:{key}:{environment}"
    USER = "user:{user_id}"
    TEMPLATE = "template:{template_id}"
    CONFIG_GROUP = "config_group:{group_id}"

# 创建数据库引擎（优化连接池）
DATABASE_URL = get_database_url()
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {},
    # 连接池优化配置
    poolclass=QueuePool,
    pool_size=20,           # 连接池大小
    max_overflow=30,        # 最大溢出连接数
    pool_pre_ping=True,     # 连接前ping检查
    pool_recycle=3600,      # 连接回收时间（1小时）
    pool_timeout=30,        # 连接超时时间
    echo=False              # 生产环境关闭SQL日志
)

# 创建会话工厂
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建基类
Base = declarative_base()

# 数据库依赖（优化版本）
@contextmanager
def get_db():
    """获取数据库会话（使用上下文管理器）"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        logger.error(f"数据库操作失败: {e}")
        raise
    finally:
        db.close()

# 缓存装饰器
def cache_result(ttl: int = 3600, key_prefix: str = ""):
    """缓存装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            if redis_client is None:
                return func(*args, **kwargs)
            
            # 生成缓存键
            cache_key = f"{key_prefix}:{func.__name__}:{hash(str(args) + str(kwargs))}"
            
            # 尝试从缓存获取
            cached_result = redis_client.get(cache_key)
            if cached_result:
                logger.debug(f"缓存命中: {cache_key}")
                return json.loads(cached_result)
            
            # 执行函数
            result = func(*args, **kwargs)
            
            # 存入缓存
            try:
                redis_client.setex(cache_key, ttl, json.dumps(result))
                logger.debug(f"缓存存储: {cache_key}")
            except Exception as e:
                logger.warning(f"缓存存储失败: {e}")
            
            return result
        return wrapper
    return decorator

# 性能监控装饰器
def monitor_performance(func_name: str = None):
    """性能监控装饰器"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            start_time = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start_time
                logger.info(f"性能监控 - {func_name or func.__name__}: {duration:.3f}秒")
                return result
            except Exception as e:
                duration = time.time() - start_time
                logger.error(f"性能监控 - {func_name or func.__name__} 失败: {duration:.3f}秒, 错误: {e}")
                raise
        return wrapper
    return decorator

# 用户模型
class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100))
    is_active = Column(Boolean, default=True)
    is_superuser = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    
    # 关系
    configs = relationship("Config", back_populates="owner")
    config_versions = relationship("ConfigVersion", back_populates="user")

# 配置模型
class Config(Base):
    __tablename__ = "configs"
    
    id = Column(Integer, primary_key=True, index=True)
    key = Column(String(255), unique=True, index=True, nullable=False)
    value = Column(Text, nullable=False)
    description = Column(Text)
    category = Column(String(100), index=True)
    environment = Column(String(50), index=True, default="default")
    is_encrypted = Column(Boolean, default=False)
    is_sensitive = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    owner_id = Column(Integer, ForeignKey("users.id"))
    
    # 关系
    owner = relationship("User", back_populates="configs")
    versions = relationship("ConfigVersion", back_populates="config")

# 配置版本模型
class ConfigVersion(Base):
    __tablename__ = "config_versions"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    version = Column(Integer, nullable=False)
    value = Column(Text, nullable=False)
    change_reason = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    user_id = Column(Integer, ForeignKey("users.id"))
    
    # 关系
    config = relationship("Config", back_populates="versions")
    user = relationship("User", back_populates="config_versions")

# 配置模板模型
class ConfigTemplate(Base):
    __tablename__ = "config_templates"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    template_data = Column(Text, nullable=False)  # JSON格式的模板数据
    category = Column(String(100), index=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 配置组模型
class ConfigGroup(Base):
    __tablename__ = "config_groups"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, index=True, nullable=False)
    description = Column(Text)
    parent_group_id = Column(Integer, ForeignKey("config_groups.id"))
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

# 配置访问日志模型
class ConfigAccessLog(Base):
    __tablename__ = "config_access_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    config_id = Column(Integer, ForeignKey("configs.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"))
    action = Column(String(50), nullable=False)  # read, write, delete
    ip_address = Column(String(45))
    user_agent = Column(Text)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # 关系
    config = relationship("Config")
    user = relationship("User")

# 初始化Redis连接
init_redis() 