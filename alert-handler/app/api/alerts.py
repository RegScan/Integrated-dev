from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models.alert import Alert, AlertRule, NotificationLog
from ..services.alert_processor import AlertProcessorService
from ..services.notification import NotificationService
from ..database import get_db
import logging

router = APIRouter(prefix="/alerts", tags=["alerts"])
logger = logging.getLogger(__name__)

# Pydantic模型定义
class AlertCreate(BaseModel):
    """创建告警请求模型"""
    source_module: str
    source_ip: Optional[str] = None
    target_url: Optional[str] = None
    domain: Optional[str] = None
    alert_type: str
    severity: str  # low/medium/high/critical
    title: str
    description: Optional[str] = None
    evidence: Optional[Dict[str, Any]] = None
    priority: Optional[int] = 3

class AlertUpdate(BaseModel):
    """更新告警请求模型"""
    status: Optional[str] = None
    assigned_to: Optional[str] = None
    handler: Optional[str] = None
    resolution: Optional[str] = None
    priority: Optional[int] = None

class AlertResponse(BaseModel):
    """告警响应模型"""
    id: str
    alert_id: str
    source_module: str
    source_ip: Optional[str]
    target_url: Optional[str]
    domain: Optional[str]
    alert_type: str
    severity: str
    title: str
    description: Optional[str]
    evidence: Optional[Dict[str, Any]]
    status: str
    priority: int
    assigned_to: Optional[str]
    handler: Optional[str]
    resolution: Optional[str]
    created_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime]
    notification_sent: bool
    notification_channels: Optional[Dict[str, Any]]

class AlertListResponse(BaseModel):
    """告警列表响应模型"""
    alerts: List[AlertResponse]
    total: int
    page: int
    page_size: int

class AlertStatistics(BaseModel):
    """告警统计响应模型"""
    total_alerts: int
    open_alerts: int
    high_severity_alerts: int
    alerts_by_severity: Dict[str, int]
    alerts_by_status: Dict[str, int]
    alerts_by_type: Dict[str, int]

# 依赖注入
def get_alert_processor_service():
    """获取告警处理服务"""
    notification_service = NotificationService()
    return AlertProcessorService(notification_service=notification_service)

@router.post("/", response_model=Dict[str, str])
async def create_alert(
    alert_data: AlertCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    service: AlertProcessorService = Depends(get_alert_processor_service)
):
    """
    创建新告警并启动处理流程
    """
    try:
        # 启动后台处理任务
        background_tasks.add_task(service.process_alert, alert_data.dict(), db)
        
        logger.info(f"Alert received: {alert_data.alert_type} from {alert_data.source_module}")
        
        return {
            "status": "success",
            "message": "Alert received and is being processed"
        }
    except Exception as e:
        logger.error(f"Error creating alert: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to create alert")

@router.get("/", response_model=AlertListResponse)
async def get_alerts(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    severity: Optional[str] = Query(None, description="严重级别过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    alert_type: Optional[str] = Query(None, description="告警类型过滤"),
    source_module: Optional[str] = Query(None, description="来源模块过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """
    获取告警列表
    """
    try:
        # 构建查询条件
        query = db.query(Alert)
        
        if severity:
            query = query.filter(Alert.severity == severity)
        if status:
            query = query.filter(Alert.status == status)
        if alert_type:
            query = query.filter(Alert.alert_type == alert_type)
        if source_module:
            query = query.filter(Alert.source_module == source_module)
        if start_date:
            query = query.filter(Alert.created_at >= start_date)
        if end_date:
            query = query.filter(Alert.created_at <= end_date)
        
        # 获取总数
        total = query.count()
        
        # 分页查询
        alerts = query.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        # 转换为响应模型
        alert_responses = [AlertResponse(**alert.to_dict()) for alert in alerts]
        
        return AlertListResponse(
            alerts=alert_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error getting alerts: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alerts")

@router.get("/{alert_id}", response_model=AlertResponse)
async def get_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """
    获取单个告警详情
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        return AlertResponse(**alert.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting alert {alert_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alert")

@router.put("/{alert_id}", response_model=AlertResponse)
async def update_alert(
    alert_id: str,
    alert_update: AlertUpdate,
    db: Session = Depends(get_db)
):
    """
    更新告警信息
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        # 更新字段
        update_data = alert_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(alert, field, value)
        
        # 如果状态更新为已解决，设置解决时间
        if alert_update.status == "resolved" and alert.resolved_at is None:
            alert.resolved_at = datetime.utcnow()
        
        db.commit()
        db.refresh(alert)
        
        logger.info(f"Alert {alert_id} updated: {update_data}")
        
        return AlertResponse(**alert.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating alert {alert_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update alert")

@router.delete("/{alert_id}")
async def delete_alert(
    alert_id: str,
    db: Session = Depends(get_db)
):
    """
    删除告警
    """
    try:
        alert = db.query(Alert).filter(Alert.id == alert_id).first()
        if not alert:
            raise HTTPException(status_code=404, detail="Alert not found")
        
        db.delete(alert)
        db.commit()
        
        logger.info(f"Alert {alert_id} deleted")
        
        return {"status": "success", "message": "Alert deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting alert {alert_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete alert")

@router.get("/statistics/overview", response_model=AlertStatistics)
async def get_alert_statistics(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """
    获取告警统计信息
    """
    try:
        # 计算时间范围
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 基础查询
        base_query = db.query(Alert).filter(Alert.created_at >= start_date)
        
        # 总告警数
        total_alerts = base_query.count()
        
        # 未解决告警数
        open_alerts = base_query.filter(Alert.status.in_(["open", "in_progress"])).count()
        
        # 高危告警数
        high_severity_alerts = base_query.filter(Alert.severity.in_(["high", "critical"])).count()
        
        # 按严重级别统计
        alerts_by_severity = {}
        for severity in ["low", "medium", "high", "critical"]:
            count = base_query.filter(Alert.severity == severity).count()
            alerts_by_severity[severity] = count
        
        # 按状态统计
        alerts_by_status = {}
        for status in ["open", "in_progress", "resolved", "closed"]:
            count = base_query.filter(Alert.status == status).count()
            alerts_by_status[status] = count
        
        # 按类型统计（取前10个）
        alerts_by_type = {}
        type_counts = db.query(Alert.alert_type, db.func.count(Alert.id)).filter(
            Alert.created_at >= start_date
        ).group_by(Alert.alert_type).order_by(db.func.count(Alert.id).desc()).limit(10).all()
        
        for alert_type, count in type_counts:
            alerts_by_type[alert_type] = count
        
        return AlertStatistics(
            total_alerts=total_alerts,
            open_alerts=open_alerts,
            high_severity_alerts=high_severity_alerts,
            alerts_by_severity=alerts_by_severity,
            alerts_by_status=alerts_by_status,
            alerts_by_type=alerts_by_type
        )
    except Exception as e:
        logger.error(f"Error getting alert statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get alert statistics")