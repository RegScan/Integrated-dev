from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool
from .core.config import settings
import logging
import redis
import json
from contextlib import contextmanager
from functools import lru_cache
import asyncio
from enum import Enum

class CacheKeys(Enum):
    """Redis缓存键枚举"""
    WEBSITE_INFO = "website:info:{domain}"
    SCAN_RESULT = "scan:result:{domain}:{timestamp}"
    SCAN_QUEUE = "scan:queue"
    SCAN_STATS = "scan:stats:{date}"
    MEMORY_USAGE = "system:memory"
    ACTIVE_SCANS = "scan:active"

logger = logging.getLogger(__name__)

# 数据库配置
Base = declarative_base()
engine = None
SessionLocal = None

def init_database():
    """初始化数据库连接"""
    global engine, SessionLocal
    try:
        # 对于website-scanner，我们主要使用MongoDB，这里提供SQLite作为备用
        database_url = getattr(settings, 'DATABASE_URL', 'sqlite:///./website_scanner.db')
        
        engine = create_engine(
            database_url,
            poolclass=QueuePool,
            pool_size=5,
            max_overflow=10,
            pool_pre_ping=True,
            pool_recycle=300
        )
        
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        
        # 创建表
        Base.metadata.create_all(bind=engine)
        logger.info("数据库初始化成功")
        return True
    except Exception as e:
        logger.error(f"数据库初始化失败: {e}")
        return False

def get_db():
    """获取数据库会话"""
    if SessionLocal is None:
        init_database()
    
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Redis缓存客户端
redis_client = None

def init_redis():
    """初始化Redis连接"""
    global redis_client
    try:
        redis_url = getattr(settings, 'redis_url', 'redis://localhost:6379/1')
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

# Redis内存管理配置
REDIS_MEMORY_CONFIG = {
    "max_memory": "2gb",
    "max_memory_policy": "allkeys-lru",
    "max_memory_samples": 5,
    "save_interval": "900 1 300 10 60 10000",
    "max_clients": 100,
    "timeout": 300,
    "tcp_keepalive": 300
}

# 缓存大小限制
CACHE_SIZE_LIMITS = {
    "scan_result": 1000,  # 最大缓存扫描结果数
    "beian_info": 5000,   # 最大缓存备案信息数
    "user_session": 1000, # 最大缓存用户会话数
    "api_rate_limit": 10000  # 最大缓存API限流数
}

class RedisMemoryManager:
    """Redis内存管理器"""
    
    def __init__(self, redis_client):
        self.redis = redis_client
        self.max_memory = 2 * 1024 * 1024 * 1024  # 2GB
    
    async def check_memory_usage(self) -> float:
        """检查Redis内存使用率"""
        try:
            info = await self.redis.info("memory")
            used_memory = int(info.get("used_memory", 0))
            return (used_memory / self.max_memory) * 100
        except Exception as e:
            logger.error(f"检查Redis内存使用失败: {e}")
            return 0.0
    
    async def cleanup_old_cache(self):
        """清理过期缓存"""
        try:
            # 清理过期的扫描结果
            scan_keys = await self.redis.keys("scan:result:*")
            if len(scan_keys) > CACHE_SIZE_LIMITS["scan_result"]:
                # 删除最旧的缓存
                oldest_keys = scan_keys[:-CACHE_SIZE_LIMITS["scan_result"]]
                if oldest_keys:
                    await self.redis.delete(*oldest_keys)
                    logger.info(f"清理了 {len(oldest_keys)} 个过期扫描结果缓存")
            
            # 清理过期的备案信息
            beian_keys = await self.redis.keys("beian:info:*")
            if len(beian_keys) > CACHE_SIZE_LIMITS["beian_info"]:
                oldest_keys = beian_keys[:-CACHE_SIZE_LIMITS["beian_info"]]
                if oldest_keys:
                    await self.redis.delete(*oldest_keys)
                    logger.info(f"清理了 {len(oldest_keys)} 个过期备案信息缓存")
                    
        except Exception as e:
            logger.error(f"清理缓存失败: {e}")
    
    async def enforce_memory_limit(self):
        """强制执行内存限制"""
        memory_usage = await self.check_memory_usage()
        if memory_usage > 90:  # 超过90%时强制清理
            logger.warning(f"Redis内存使用率过高: {memory_usage:.1f}%，开始强制清理")
            await self.cleanup_old_cache()
            
            # 如果还是过高，执行更激进的清理
            if await self.check_memory_usage() > 95:
                logger.error("Redis内存使用率仍然过高，执行激进清理")
                await self.redis.flushdb()
                logger.warning("已清空所有Redis数据")

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

# 在模块加载时初始化数据库和Redis
# init_database()  # 移除自动初始化调用
init_redis()

# 初始化Redis内存管理器
redis_memory_manager = RedisMemoryManager(redis_client)

# 定期内存清理任务
async def periodic_memory_cleanup():
    """定期内存清理任务"""
    while True:
        try:
            await redis_memory_manager.enforce_memory_limit()
            await asyncio.sleep(300)  # 每5分钟检查一次
        except Exception as e:
            logger.error(f"定期内存清理失败: {e}")
            await asyncio.sleep(60)

# 启动内存清理任务
async def start_memory_cleanup():
    """启动内存清理任务"""
    asyncio.create_task(periodic_memory_cleanup())
    logger.info("内存清理任务已启动")