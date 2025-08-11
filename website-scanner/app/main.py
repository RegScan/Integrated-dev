"""
Website Scanner 主应用
"""

from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import asyncio
import psutil
import logging
from contextlib import asynccontextmanager

from .core.config import settings
from .database import redis_client, start_memory_cleanup
from .api import scan, results, memory
from .services.memory_manager import MemoryManager

# 配置日志
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format=settings.LOG_FORMAT
)
logger = logging.getLogger(__name__)

# 全局内存监控器
memory_monitor = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    """应用生命周期管理"""
    global memory_monitor
    
    # 启动时
    logger.info("启动 Website Scanner 服务...")
    
    # 初始化内存监控器
    memory_monitor = MemoryManager()
    
    # 启动内存清理任务
    await start_memory_cleanup()
    
    # 启动内存监控任务
    asyncio.create_task(memory_monitoring_task())
    
    yield
    
    # 关闭时
    logger.info("关闭 Website Scanner 服务...")
    
    # 清理资源
    if memory_monitor:
        await memory_monitor.cleanup_browsers()

# 创建FastAPI应用
app = FastAPI(
    title="Website Scanner API",
    description="网站内容合规检测服务",
    version="2.0.0",
    lifespan=lifespan
)

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 内存监控中间件
@app.middleware("http")
async def memory_monitoring_middleware(request: Request, call_next):
    """内存监控中间件"""
    if memory_monitor:
        memory_usage = await memory_monitor.get_memory_usage()
        
        # 如果内存使用率过高，返回503错误
        if memory_usage > 95:
            logger.critical(f"内存使用率过高: {memory_usage:.1f}%，拒绝请求")
            return JSONResponse(
                status_code=503,
                content={
                    "error": "Service Unavailable",
                    "message": "系统内存使用率过高，请稍后重试",
                    "memory_usage": f"{memory_usage:.1f}%"
                }
            )
    
    response = await call_next(request)
    return response

# 注册路由
app.include_router(scan.router, prefix="/api/v1")
app.include_router(results.router, prefix="/api/v1")
app.include_router(memory.router, prefix="/api/v1")

# 健康检查
@app.get("/health")
async def health_check():
    """健康检查"""
    try:
        # 检查数据库连接
        await redis_client.ping()
        
        # 检查内存状态
        memory_status = "normal"
        if memory_monitor:
            memory_usage = await memory_monitor.get_memory_usage()
            if memory_usage > 90:
                memory_status = "critical"
            elif memory_usage > 80:
                memory_status = "warning"
        
        return {
            "status": "healthy",
            "service": "website-scanner",
            "version": "2.0.0",
            "memory_status": memory_status,
            "timestamp": asyncio.get_event_loop().time()
        }
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="服务不可用")

@app.get("/health/detailed")
async def detailed_health_check():
    """详细健康检查"""
    try:
        # 基础健康检查
        basic_health = await health_check()
        
        # 获取详细状态
        detailed_status = {
            **basic_health,
            "system_info": {
                "cpu_percent": psutil.cpu_percent(),
                "memory_percent": psutil.virtual_memory().percent,
                "disk_usage": psutil.disk_usage('/').percent
            }
        }
        
        # 如果内存监控器可用，添加内存详细信息
        if memory_monitor:
            memory_stats = await memory_monitor.get_memory_stats()
            detailed_status["memory_details"] = memory_stats
        
        return detailed_status
    except Exception as e:
        logger.error(f"详细健康检查失败: {e}")
        raise HTTPException(status_code=503, detail="服务不可用")

async def memory_monitoring_task():
    """内存监控任务"""
    while True:
        try:
            if memory_monitor:
                memory_usage = await memory_monitor.get_memory_usage()
                
                # 检查内存状态
                if memory_usage > 90:
                    logger.critical(f"内存使用率紧急: {memory_usage:.1f}%")
                    await trigger_memory_alert("emergency", f"内存使用率紧急: {memory_usage:.1f}%")
                elif memory_usage > 80:
                    logger.warning(f"内存使用率警告: {memory_usage:.1f}%")
                    await trigger_memory_alert("warning", f"内存使用率警告: {memory_usage:.1f}%")
                
                # 如果内存使用率过高，执行紧急清理
                if memory_usage > 95:
                    await emergency_memory_cleanup()
            
            await asyncio.sleep(settings.MEMORY_CHECK_INTERVAL)
            
        except Exception as e:
            logger.error(f"内存监控任务失败: {e}")
            await asyncio.sleep(10)

async def trigger_memory_alert(level: str, message: str):
    """触发内存告警"""
    try:
        # 记录告警到Redis
        alert_data = {
            'timestamp': asyncio.get_event_loop().time(),
            'service': 'website-scanner',
            'level': level,
            'message': message,
            'resolved': 'false'
        }
        
        await redis_client.hmset(
            f"memory:alert:{int(asyncio.get_event_loop().time())}",
            alert_data
        )
        
        logger.warning(f"内存告警已记录: {level} - {message}")
        
    except Exception as e:
        logger.error(f"记录内存告警失败: {e}")

async def emergency_memory_cleanup():
    """紧急内存清理"""
    try:
        logger.critical("执行紧急内存清理")
        
        if memory_monitor:
            # 清理所有浏览器实例
            await memory_monitor.cleanup_browsers()
            
            # 强制垃圾回收
            await memory_monitor.force_gc()
            
            # 清理Redis缓存
            await redis_client.flushdb()
            
            logger.info("紧急内存清理完成")
        
    except Exception as e:
        logger.error(f"紧急内存清理失败: {e}")

# 错误处理
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """全局异常处理"""
    logger.error(f"未处理的异常: {exc}")
    return JSONResponse(
        status_code=500,
        content={
            "error": "Internal Server Error",
            "message": "服务器内部错误",
            "detail": str(exc) if settings.DEBUG else "请稍后重试"
        }
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8001,
        reload=settings.DEBUG
    )
