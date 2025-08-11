from fastapi import FastAPI, Depends, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.responses import JSONResponse
from contextlib import asynccontextmanager
import time
import logging
from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, REGISTRY
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST

from .config import settings
from .database import get_db, init_redis
from .api import auth, config, users

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# Prometheus 指标 - 避免重复注册
def get_or_create_metric(metric_class, name, description, labels=None, registry=REGISTRY):
    """获取或创建指标，避免重复注册"""
    try:
        # 尝试从注册表中获取现有指标
        for collector in list(registry._collector_to_names.keys()):
            if hasattr(collector, '_name') and collector._name == name:
                return collector
        # 如果不存在，创建新指标
        if labels:
            return metric_class(name, description, labels, registry=registry)
        else:
            return metric_class(name, description, registry=registry)
    except Exception as e:
        logger.warning(f"指标创建/获取失败 {name}: {e}")
        # 返回一个虚拟对象，避免崩溃
        class DummyMetric:
            def inc(self, *args, **kwargs): pass
            def observe(self, *args, **kwargs): pass
            def set(self, *args, **kwargs): pass
        return DummyMetric()

REQUEST_COUNT = get_or_create_metric(Counter, 'http_requests_total', 'Total HTTP requests', ['method', 'endpoint', 'status'])
REQUEST_DURATION = get_or_create_metric(Histogram, 'http_request_duration_seconds', 'HTTP request duration')
ACTIVE_REQUESTS = get_or_create_metric(Gauge, 'http_active_requests', 'Number of active HTTP requests')
CACHE_HIT_RATIO = get_or_create_metric(Gauge, 'cache_hit_ratio', 'Cache hit ratio')
DB_CONNECTION_POOL_SIZE = get_or_create_metric(Gauge, 'db_connection_pool_size', 'Database connection pool size')

# 生命周期事件管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    # 启动事件
    logger.info(f"启动 {settings.APP_NAME} v{settings.VERSION}")
    
    # 初始化Redis
    try:
        if init_redis():
            logger.info("Redis连接初始化成功")
        else:
            logger.warning("Redis连接初始化失败，缓存功能将不可用")
    except Exception as e:
        logger.error(f"Redis初始化错误: {e}")
    
    # 创建数据库表
    try:
        from .database import Base, engine
        Base.metadata.create_all(bind=engine)
        logger.info("数据库表创建成功")
    except Exception as e:
        logger.error(f"数据库表创建失败: {e}")
    
    yield  # 应用运行阶段
    
    # 关闭事件
    logger.info(f"关闭 {settings.APP_NAME}")

# 创建FastAPI应用
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.VERSION,
    debug=settings.DEBUG,
    lifespan=lifespan
)

# 性能监控中间件
@app.middleware("http")
async def performance_middleware(request: Request, call_next):
    """性能监控中间件"""
    start_time = time.time()
    ACTIVE_REQUESTS.inc()
    
    try:
        response = await call_next(request)
        duration = time.time() - start_time
        
        # 记录请求指标
        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=request.url.path,
            status=response.status_code
        ).inc()
        
        REQUEST_DURATION.observe(duration)
        
        # 记录慢请求
        if duration > settings.SLOW_QUERY_THRESHOLD:
            logger.warning(f"慢请求: {request.method} {request.url.path} - {duration:.3f}秒")
        
        return response
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"请求失败: {request.method} {request.url.path} - {duration:.3f}秒, 错误: {e}")
        raise
    finally:
        ACTIVE_REQUESTS.dec()

# 健康检查中间件
@app.middleware("http")
async def health_check_middleware(request: Request, call_next):
    """健康检查中间件"""
    if request.url.path == "/health":
        # 检查数据库连接
        try:
            with get_db() as db:
                db.execute("SELECT 1")
            db_status = "healthy"
        except Exception as e:
            logger.error(f"数据库健康检查失败: {e}")
            db_status = "unhealthy"
        
        # 检查Redis连接
        try:
            from .database import redis_client
            if redis_client:
                redis_client.ping()
                redis_status = "healthy"
            else:
                redis_status = "unavailable"
        except Exception as e:
            logger.error(f"Redis健康检查失败: {e}")
            redis_status = "unhealthy"
        
        return JSONResponse({
            "status": "healthy" if db_status == "healthy" else "unhealthy",
            "timestamp": time.time(),
            "services": {
                "database": db_status,
                "redis": redis_status
            }
        })
    
    return await call_next(request)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 添加Gzip压缩中间件
app.add_middleware(GZipMiddleware, minimum_size=1000)

# 注册路由
app.include_router(auth.router, prefix="/api/v1/auth", tags=["认证"])
app.include_router(config.router, prefix="/api/v1/config", tags=["配置"])
app.include_router(users.router, prefix="/api/v1/users", tags=["用户"])

# 根路径
@app.get("/")
async def root():
    """根路径"""
    return {
        "app": settings.APP_NAME,
        "version": settings.VERSION,
        "status": "running"
    }

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    return {"status": "healthy", "timestamp": time.time()}

# 详细健康检查
@app.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    # 检查数据库连接
    try:
        with get_db() as db:
            db.execute("SELECT 1")
        db_status = "healthy"
    except Exception as e:
        logger.error(f"数据库健康检查失败: {e}")
        db_status = "unhealthy"
    
    # 检查Redis连接
    try:
        from .database import redis_client
        if redis_client:
            redis_client.ping()
            redis_status = "healthy"
        else:
            redis_status = "unavailable"
    except Exception as e:
        logger.error(f"Redis健康检查失败: {e}")
        redis_status = "unhealthy"
    
    return {
        "status": "healthy" if db_status == "healthy" else "unhealthy",
        "timestamp": time.time(),
        "services": {
            "database": db_status,
            "redis": redis_status
        },
        "config": {
            "environment": settings.ENVIRONMENT,
            "debug": settings.DEBUG,
            "cache_enabled": settings.CACHE_ENABLED
        }
    }

# Prometheus指标端点
@app.get("/metrics")
async def metrics():
    """Prometheus指标端点"""
    return JSONResponse(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )

# 注意：lifespan 事件已在应用创建时定义，这里移除旧的 on_event

# 异常处理器
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理器"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={"detail": "内部服务器错误"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower()
    )
