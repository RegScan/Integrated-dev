"""
内存监控API接口
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional
import time
import psutil
import gc
from datetime import datetime, timedelta

from ..core.config import settings
from ..services.memory_manager import MemoryManager
from ..database import redis_client
from ..schemas.memory import (
    MemoryMetricsResponse,
    ServiceMemoryData,
    AlertHistoryResponse,
    OptimizationConfig,
    MemoryTrendResponse,
    MemoryDistributionResponse
)

router = APIRouter(prefix="/api/v1/memory", tags=["memory"])

# 内存管理器实例
# memory_manager = MemoryManager()  # 延迟初始化，避免循环导入

@router.get("/metrics", response_model=MemoryMetricsResponse)
async def get_memory_metrics():
    """获取内存指标数据"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        memory_percent = process.memory_percent()
        
        # 获取浏览器实例数量
        browser_count = len(memory_manager.get_active_browsers())
        
        # 获取缓存命中率
        cache_hit_rate = await get_cache_hit_rate()
        
        # 获取垃圾回收频率
        gc_frequency = get_gc_frequency()
        
        # 计算趋势
        trend_data = await get_memory_trend_data()
        
        return MemoryMetricsResponse(
            total_memory={
                "value": f"{memory_percent:.1f}%",
                "change": f"{trend_data.get('change', 0):.1f}%",
                "trend": trend_data.get('trend', 'stable')
            },
            browser_instances={
                "value": str(browser_count),
                "change": str(trend_data.get('browser_change', 0)),
                "trend": trend_data.get('browser_trend', 'stable')
            },
            cache_hit_rate={
                "value": f"{cache_hit_rate:.1f}%",
                "change": "0.0%",
                "trend": "stable"
            },
            gc_frequency={
                "value": f"{gc_frequency}/min",
                "change": "0",
                "trend": "stable"
            },
            overall_status=get_overall_status(memory_percent),
            trend_data=trend_data
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内存指标失败: {str(e)}")

@router.get("/services", response_model=List[ServiceMemoryData])
async def get_service_memory_data():
    """获取服务内存数据"""
    try:
        services = []
        
        # 获取当前服务的内存使用
        process = psutil.Process()
        memory_percent = process.memory_percent()
        memory_mb = process.memory_info().rss / 1024 / 1024
        
        services.append(ServiceMemoryData(
            service="website-scanner",
            memory_usage=memory_percent,
            memory_mb=memory_mb,
            status=get_memory_status(memory_percent),
            last_update=time.time()
        ))
        
        # 获取其他服务的内存数据（如果有的话）
        # 这里可以通过Redis或其他方式获取其他服务的数据
        
        return services
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务内存数据失败: {str(e)}")

@router.get("/alerts", response_model=AlertHistoryResponse)
async def get_alert_history(
    limit: int = 50,
    service: Optional[str] = None,
    level: Optional[str] = None
):
    """获取告警历史"""
    try:
        # 从Redis获取告警历史
        alert_keys = await redis_client.keys("memory:alert:*")
        alerts = []
        
        for key in alert_keys[:limit]:
            alert_data = await redis_client.hgetall(key)
            if alert_data:
                # 过滤条件
                if service and alert_data.get('service') != service:
                    continue
                if level and alert_data.get('level') != level:
                    continue
                
                alerts.append({
                    "timestamp": float(alert_data.get('timestamp', 0)),
                    "service": alert_data.get('service', 'unknown'),
                    "level": alert_data.get('level', 'info'),
                    "message": alert_data.get('message', ''),
                    "resolved": alert_data.get('resolved', 'false') == 'true'
                })
        
        # 按时间排序
        alerts.sort(key=lambda x: x['timestamp'], reverse=True)
        
        return AlertHistoryResponse(
            alerts=alerts,
            total=len(alerts)
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警历史失败: {str(e)}")

@router.get("/config", response_model=OptimizationConfig)
async def get_optimization_config():
    """获取优化配置"""
    try:
        config = await redis_client.hgetall("memory:optimization_config")
        
        return OptimizationConfig(
            memory_threshold=float(config.get('memory_threshold', 80.0)),
            cleanup_interval=int(config.get('cleanup_interval', 300)),
            max_concurrent=int(config.get('max_concurrent', 5)),
            browser_memory_limit=int(config.get('browser_memory_limit', 512))
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取优化配置失败: {str(e)}")

@router.post("/config")
async def save_optimization_config(config: OptimizationConfig):
    """保存优化配置"""
    try:
        config_dict = config.dict()
        await redis_client.hmset("memory:optimization_config", config_dict)
        
        # 更新内存管理器配置
        memory_manager.update_config(config_dict)
        
        return {"message": "配置保存成功"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"保存优化配置失败: {str(e)}")

@router.post("/cleanup/{service_name}")
async def force_cleanup_service(service_name: str):
    """强制清理服务内存"""
    try:
        if service_name == "website-scanner":
            # 清理浏览器实例
            memory_manager.cleanup_browsers()
            
            # 强制垃圾回收
            gc.collect()
            
            # 清理Redis缓存
            await redis_client.flushdb()
            
            return {"message": f"服务 {service_name} 内存清理完成"}
        else:
            raise HTTPException(status_code=404, detail=f"服务 {service_name} 不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"清理服务内存失败: {str(e)}")

@router.get("/trend", response_model=MemoryTrendResponse)
async def get_memory_trend(hours: int = 24):
    """获取内存趋势数据"""
    try:
        # 从Redis获取历史数据
        trend_data = await get_memory_trend_data(hours)
        
        return MemoryTrendResponse(
            times=trend_data.get('times', []),
            values=trend_data.get('values', []),
            change=trend_data.get('change', 0.0),
            trend=trend_data.get('trend', 'stable')
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内存趋势失败: {str(e)}")

@router.get("/distribution", response_model=MemoryDistributionResponse)
async def get_memory_distribution():
    """获取内存分布数据"""
    try:
        process = psutil.Process()
        memory_info = process.memory_info()
        
        # 计算内存分布
        distribution = {
            "heap": memory_info.rss * 0.6,  # 堆内存
            "stack": memory_info.rss * 0.2,  # 栈内存
            "cache": memory_info.rss * 0.1,  # 缓存
            "other": memory_info.rss * 0.1   # 其他
        }
        
        return MemoryDistributionResponse(
            distribution=distribution,
            total_memory=memory_info.rss
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取内存分布失败: {str(e)}")

@router.post("/gc")
async def trigger_garbage_collection():
    """手动触发垃圾回收"""
    try:
        # 记录回收前的内存使用
        before_memory = psutil.Process().memory_info().rss
        
        # 执行垃圾回收
        collected = gc.collect()
        
        # 记录回收后的内存使用
        after_memory = psutil.Process().memory_info().rss
        freed_memory = before_memory - after_memory
        
        return {
            "message": "垃圾回收完成",
            "collected_objects": collected,
            "freed_memory_mb": freed_memory / 1024 / 1024
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"垃圾回收失败: {str(e)}")

# 辅助函数
async def get_cache_hit_rate() -> float:
    """获取缓存命中率"""
    try:
        # 从Redis获取缓存统计
        hit_count = await redis_client.get("cache:hit_count") or 0
        miss_count = await redis_client.get("cache:miss_count") or 0
        
        total = int(hit_count) + int(miss_count)
        if total > 0:
            return (int(hit_count) / total) * 100
        return 0.0
    except:
        return 0.0

def get_gc_frequency() -> int:
    """获取垃圾回收频率"""
    try:
        # 这里可以从监控数据中获取
        return 2  # 示例值
    except:
        return 0

async def get_memory_trend_data(hours: int = 24) -> Dict:
    """获取内存趋势数据"""
    try:
        # 从Redis获取历史数据
        trend_keys = await redis_client.keys("memory:trend:*")
        trend_data = []
        
        for key in trend_keys:
            data = await redis_client.hgetall(key)
            if data:
                trend_data.append({
                    "timestamp": float(data.get('timestamp', 0)),
                    "memory_usage": float(data.get('memory_usage', 0))
                })
        
        # 按时间排序
        trend_data.sort(key=lambda x: x['timestamp'])
        
        # 计算趋势
        if len(trend_data) >= 2:
            latest = trend_data[-1]['memory_usage']
            earliest = trend_data[0]['memory_usage']
            change = latest - earliest
            
            return {
                "times": [datetime.fromtimestamp(x['timestamp']).strftime('%H:%M') for x in trend_data],
                "values": [x['memory_usage'] for x in trend_data],
                "change": change,
                "trend": "up" if change > 0 else "down" if change < 0 else "stable"
            }
        
        return {
            "times": [],
            "values": [],
            "change": 0.0,
            "trend": "stable"
        }
    except:
        return {
            "times": [],
            "values": [],
            "change": 0.0,
            "trend": "stable"
        }

def get_overall_status(memory_percent: float) -> str:
    """获取整体状态"""
    if memory_percent > 90:
        return "emergency"
    elif memory_percent > 80:
        return "critical"
    elif memory_percent > 70:
        return "warning"
    else:
        return "normal"

def get_memory_status(memory_percent: float) -> str:
    """获取内存状态"""
    if memory_percent > 80:
        return "critical"
    elif memory_percent > 70:
        return "warning"
    else:
        return "normal" 