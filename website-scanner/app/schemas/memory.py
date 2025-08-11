"""
内存监控数据模型
"""

from pydantic import BaseModel, Field
from typing import Dict, List, Optional, Any
from datetime import datetime

class MemoryMetric(BaseModel):
    """内存指标"""
    value: str
    change: str
    trend: str

class MemoryTrendData(BaseModel):
    """内存趋势数据"""
    times: List[str]
    values: List[float]
    change: float
    trend: str

class MemoryMetricsResponse(BaseModel):
    """内存指标响应"""
    total_memory: MemoryMetric
    browser_instances: MemoryMetric
    cache_hit_rate: MemoryMetric
    gc_frequency: MemoryMetric
    overall_status: str
    trend_data: Optional[MemoryTrendData] = None

class ServiceMemoryData(BaseModel):
    """服务内存数据"""
    service: str
    memory_usage: float
    memory_mb: float
    status: str
    last_update: float

class AlertHistoryItem(BaseModel):
    """告警历史项"""
    timestamp: float
    service: str
    level: str
    message: str
    resolved: bool

class AlertHistoryResponse(BaseModel):
    """告警历史响应"""
    alerts: List[AlertHistoryItem]
    total: int

class OptimizationConfig(BaseModel):
    """优化配置"""
    memory_threshold: float = Field(80.0, ge=50.0, le=95.0, description="内存使用阈值(%)")
    cleanup_interval: int = Field(300, ge=60, le=3600, description="清理间隔(秒)")
    max_concurrent: int = Field(5, ge=1, le=20, description="最大并发数")
    browser_memory_limit: int = Field(512, ge=256, le=2048, description="浏览器内存限制(MB)")

class MemoryTrendResponse(BaseModel):
    """内存趋势响应"""
    times: List[str]
    values: List[float]
    change: float
    trend: str

class MemoryDistributionResponse(BaseModel):
    """内存分布响应"""
    distribution: Dict[str, float]
    total_memory: float

class MemoryPoolStatus(BaseModel):
    """内存池状态"""
    pool_name: str
    total_memory: float
    used_memory: float
    available_memory: float
    usage_percent: float
    status: str

class MemoryPrediction(BaseModel):
    """内存预测"""
    predicted_usage: float
    predicted_time: datetime
    confidence: float
    trend: str

class MemoryOptimizationSuggestion(BaseModel):
    """内存优化建议"""
    type: str
    description: str
    impact: str
    priority: str
    action: str

class MemoryReport(BaseModel):
    """内存报告"""
    period: str
    total_scans: int
    average_memory_usage: float
    peak_memory_usage: float
    memory_leaks_detected: int
    optimization_applied: int
    recommendations: List[str] 