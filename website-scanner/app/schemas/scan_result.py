from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class ScanStatus(str, Enum):
    """扫描状态枚举"""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

class ComplianceStatus(str, Enum):
    """合规状态枚举"""
    COMPLIANT = "compliant"
    NON_COMPLIANT = "non_compliant"
    UNKNOWN = "unknown"
    PARTIAL = "partial"

class ScanResultBase(BaseModel):
    """扫描结果基础模型"""
    url: str = Field(..., description="扫描的URL")
    task_id: str = Field(..., description="任务ID")
    status: ScanStatus = Field(..., description="扫描状态")
    compliance_status: ComplianceStatus = Field(..., description="合规状态")
    
class ScanResultCreate(ScanResultBase):
    """创建扫描结果模型"""
    scan_data: Optional[Dict[str, Any]] = Field(None, description="扫描数据")
    issues: Optional[List[Dict[str, Any]]] = Field(None, description="发现的问题")
    
class ScanResultUpdate(BaseModel):
    """更新扫描结果模型"""
    status: Optional[ScanStatus] = None
    compliance_status: Optional[ComplianceStatus] = None
    scan_data: Optional[Dict[str, Any]] = None
    issues: Optional[List[Dict[str, Any]]] = None
    completed_at: Optional[datetime] = None

class ScanResultResponse(ScanResultBase):
    """扫描结果响应模型"""
    id: str = Field(..., description="结果ID")
    created_at: datetime = Field(..., description="创建时间")
    updated_at: Optional[datetime] = Field(None, description="更新时间")
    completed_at: Optional[datetime] = Field(None, description="完成时间")
    scan_data: Optional[Dict[str, Any]] = Field(None, description="扫描数据")
    issues: Optional[List[Dict[str, Any]]] = Field(None, description="发现的问题")
    score: Optional[float] = Field(None, description="合规评分")
    
    class Config:
        from_attributes = True

class ScanResultListResponse(BaseModel):
    """扫描结果列表响应模型"""
    items: List[ScanResultResponse] = Field(..., description="扫描结果列表")
    total: int = Field(..., description="总数量")
    page: int = Field(..., description="当前页码")
    page_size: int = Field(..., description="每页数量")
    total_pages: int = Field(..., description="总页数")

class ScanStatisticsResponse(BaseModel):
    """扫描统计响应模型"""
    total_scans: int = Field(..., description="总扫描数")
    completed_scans: int = Field(..., description="已完成扫描数")
    failed_scans: int = Field(..., description="失败扫描数")
    compliance_rate: float = Field(..., description="合规率")
    avg_score: float = Field(..., description="平均评分")
    daily_stats: List[Dict[str, Any]] = Field(..., description="每日统计")
    status_distribution: Dict[str, int] = Field(..., description="状态分布")
    compliance_distribution: Dict[str, int] = Field(..., description="合规状态分布")
    
class ScanHistoryItem(BaseModel):
    """扫描历史项模型"""
    id: str = Field(..., description="结果ID")
    scan_date: datetime = Field(..., description="扫描日期")
    status: ScanStatus = Field(..., description="扫描状态")
    compliance_status: ComplianceStatus = Field(..., description="合规状态")
    score: Optional[float] = Field(None, description="合规评分")
    issues_count: int = Field(..., description="问题数量")
    
    class Config:
        from_attributes = True

class ScanHistoryResponse(BaseModel):
    """扫描历史响应模型"""
    url: str = Field(..., description="网站URL")
    history: List[ScanHistoryItem] = Field(..., description="历史记录")
    total_scans: int = Field(..., description="总扫描次数")
    latest_scan: Optional[ScanHistoryItem] = Field(None, description="最新扫描")
    trend: Dict[str, Any] = Field(..., description="趋势分析")