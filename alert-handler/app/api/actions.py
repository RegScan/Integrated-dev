from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime
from sqlalchemy.orm import Session
from pydantic import BaseModel

from ..models.action import ActionTemplate, ActionExecution, ActionSchedule
from ..services.auto_action import AutoActionService
from ..database import get_db
import logging

router = APIRouter(prefix="/actions", tags=["actions"])
logger = logging.getLogger(__name__)

# Pydantic模型定义
class ActionTemplateCreate(BaseModel):
    """创建动作模板请求模型"""
    name: str
    description: Optional[str] = None
    action_type: str  # email/sms/webhook/script/api_call
    config: Dict[str, Any]
    is_active: bool = True
    timeout: Optional[int] = 300
    retry_count: Optional[int] = 3
    retry_interval: Optional[int] = 60

class ActionTemplateUpdate(BaseModel):
    """更新动作模板请求模型"""
    name: Optional[str] = None
    description: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    is_active: Optional[bool] = None
    timeout: Optional[int] = None
    retry_count: Optional[int] = None
    retry_interval: Optional[int] = None

class ActionTemplateResponse(BaseModel):
    """动作模板响应模型"""
    id: str
    name: str
    description: Optional[str]
    action_type: str
    config: Dict[str, Any]
    is_active: bool
    timeout: int
    retry_count: int
    retry_interval: int
    created_at: datetime
    updated_at: datetime
    created_by: Optional[str]
    updated_by: Optional[str]

class ActionExecutionCreate(BaseModel):
    """创建动作执行请求模型"""
    template_id: str
    alert_id: str
    parameters: Optional[Dict[str, Any]] = None
    scheduled_at: Optional[datetime] = None
    priority: Optional[int] = 3

class ActionExecutionResponse(BaseModel):
    """动作执行响应模型"""
    id: str
    execution_id: str
    template_id: str
    alert_id: str
    status: str
    parameters: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    started_at: Optional[datetime]
    completed_at: Optional[datetime]
    duration: Optional[int]
    retry_count: int
    priority: int
    created_at: datetime
    updated_at: datetime

class ActionScheduleCreate(BaseModel):
    """创建动作调度请求模型"""
    template_id: str
    alert_id: str
    scheduled_at: datetime
    parameters: Optional[Dict[str, Any]] = None
    priority: Optional[int] = 3
    max_retries: Optional[int] = 3

class ActionScheduleResponse(BaseModel):
    """动作调度响应模型"""
    id: str
    schedule_id: str
    template_id: str
    alert_id: str
    status: str
    scheduled_at: datetime
    executed_at: Optional[datetime]
    parameters: Optional[Dict[str, Any]]
    result: Optional[Dict[str, Any]]
    error_message: Optional[str]
    retry_count: int
    max_retries: int
    priority: int
    created_at: datetime
    updated_at: datetime

class ActionListResponse(BaseModel):
    """动作列表响应模型"""
    items: List[Any]
    total: int
    page: int
    page_size: int

class ActionStatistics(BaseModel):
    """动作统计响应模型"""
    total_executions: int
    successful_executions: int
    failed_executions: int
    pending_executions: int
    executions_by_type: Dict[str, int]
    executions_by_status: Dict[str, int]
    average_execution_time: float

# 依赖注入
def get_auto_action_service():
    """获取自动处置服务"""
    return AutoActionService()

# 动作模板管理
@router.post("/templates", response_model=ActionTemplateResponse)
async def create_action_template(
    template_data: ActionTemplateCreate,
    db: Session = Depends(get_db)
):
    """创建动作模板"""
    try:
        # 创建新模板
        template = ActionTemplate(
            **template_data.dict(),
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(template)
        db.commit()
        db.refresh(template)
        
        logger.info(f"Action template created: {template.name}")
        
        return ActionTemplateResponse(**template.to_dict())
    except Exception as e:
        logger.error(f"Error creating action template: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to create action template")

@router.get("/templates", response_model=ActionListResponse)
async def get_action_templates(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    action_type: Optional[str] = Query(None, description="动作类型过滤"),
    is_active: Optional[bool] = Query(None, description="是否激活过滤"),
    db: Session = Depends(get_db)
):
    """获取动作模板列表"""
    try:
        query = db.query(ActionTemplate)
        
        if action_type:
            query = query.filter(ActionTemplate.action_type == action_type)
        if is_active is not None:
            query = query.filter(ActionTemplate.is_active == is_active)
        
        total = query.count()
        templates = query.order_by(ActionTemplate.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        template_responses = [ActionTemplateResponse(**template.to_dict()) for template in templates]
        
        return ActionListResponse(
            items=template_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error getting action templates: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get action templates")

@router.get("/templates/{template_id}", response_model=ActionTemplateResponse)
async def get_action_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """获取单个动作模板"""
    try:
        template = db.query(ActionTemplate).filter(ActionTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Action template not found")
        
        return ActionTemplateResponse(**template.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action template {template_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get action template")

@router.put("/templates/{template_id}", response_model=ActionTemplateResponse)
async def update_action_template(
    template_id: str,
    template_update: ActionTemplateUpdate,
    db: Session = Depends(get_db)
):
    """更新动作模板"""
    try:
        template = db.query(ActionTemplate).filter(ActionTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Action template not found")
        
        # 更新字段
        update_data = template_update.dict(exclude_unset=True)
        for field, value in update_data.items():
            setattr(template, field, value)
        
        template.updated_at = datetime.utcnow()
        
        db.commit()
        db.refresh(template)
        
        logger.info(f"Action template {template_id} updated")
        
        return ActionTemplateResponse(**template.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating action template {template_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to update action template")

@router.delete("/templates/{template_id}")
async def delete_action_template(
    template_id: str,
    db: Session = Depends(get_db)
):
    """删除动作模板"""
    try:
        template = db.query(ActionTemplate).filter(ActionTemplate.id == template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Action template not found")
        
        db.delete(template)
        db.commit()
        
        logger.info(f"Action template {template_id} deleted")
        
        return {"status": "success", "message": "Action template deleted"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting action template {template_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to delete action template")

# 动作执行管理
@router.post("/executions", response_model=Dict[str, str])
async def execute_action(
    execution_data: ActionExecutionCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    service: AutoActionService = Depends(get_auto_action_service)
):
    """执行动作"""
    try:
        # 验证模板存在
        template = db.query(ActionTemplate).filter(ActionTemplate.id == execution_data.template_id).first()
        if not template:
            raise HTTPException(status_code=404, detail="Action template not found")
        
        if not template.is_active:
            raise HTTPException(status_code=400, detail="Action template is not active")
        
        # 启动后台执行任务
        if execution_data.scheduled_at and execution_data.scheduled_at > datetime.utcnow():
            # 调度执行
            background_tasks.add_task(
                service.schedule_action,
                execution_data.template_id,
                execution_data.alert_id,
                execution_data.scheduled_at,
                execution_data.parameters or {},
                db
            )
            message = "Action scheduled for execution"
        else:
            # 立即执行
            background_tasks.add_task(
                service.execute_action,
                execution_data.template_id,
                execution_data.alert_id,
                execution_data.parameters or {},
                db
            )
            message = "Action execution started"
        
        logger.info(f"Action execution requested: template={execution_data.template_id}, alert={execution_data.alert_id}")
        
        return {
            "status": "success",
            "message": message
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing action: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to execute action")

@router.get("/executions", response_model=ActionListResponse)
async def get_action_executions(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    template_id: Optional[str] = Query(None, description="模板ID过滤"),
    alert_id: Optional[str] = Query(None, description="告警ID过滤"),
    status: Optional[str] = Query(None, description="状态过滤"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db)
):
    """获取动作执行列表"""
    try:
        query = db.query(ActionExecution)
        
        if template_id:
            query = query.filter(ActionExecution.template_id == template_id)
        if alert_id:
            query = query.filter(ActionExecution.alert_id == alert_id)
        if status:
            query = query.filter(ActionExecution.status == status)
        if start_date:
            query = query.filter(ActionExecution.created_at >= start_date)
        if end_date:
            query = query.filter(ActionExecution.created_at <= end_date)
        
        total = query.count()
        executions = query.order_by(ActionExecution.created_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        execution_responses = [ActionExecutionResponse(**execution.to_dict()) for execution in executions]
        
        return ActionListResponse(
            items=execution_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error getting action executions: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get action executions")

@router.get("/executions/{execution_id}", response_model=ActionExecutionResponse)
async def get_action_execution(
    execution_id: str,
    db: Session = Depends(get_db)
):
    """获取单个动作执行详情"""
    try:
        execution = db.query(ActionExecution).filter(ActionExecution.id == execution_id).first()
        if not execution:
            raise HTTPException(status_code=404, detail="Action execution not found")
        
        return ActionExecutionResponse(**execution.to_dict())
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting action execution {execution_id}: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get action execution")

# 动作调度管理
@router.get("/schedules", response_model=ActionListResponse)
async def get_action_schedules(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    status: Optional[str] = Query(None, description="状态过滤"),
    db: Session = Depends(get_db)
):
    """获取动作调度列表"""
    try:
        query = db.query(ActionSchedule)
        
        if status:
            query = query.filter(ActionSchedule.status == status)
        
        total = query.count()
        schedules = query.order_by(ActionSchedule.scheduled_at.desc()).offset((page - 1) * page_size).limit(page_size).all()
        
        schedule_responses = [ActionScheduleResponse(**schedule.to_dict()) for schedule in schedules]
        
        return ActionListResponse(
            items=schedule_responses,
            total=total,
            page=page,
            page_size=page_size
        )
    except Exception as e:
        logger.error(f"Error getting action schedules: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get action schedules")

@router.delete("/schedules/{schedule_id}")
async def cancel_action_schedule(
    schedule_id: str,
    db: Session = Depends(get_db)
):
    """取消动作调度"""
    try:
        schedule = db.query(ActionSchedule).filter(ActionSchedule.id == schedule_id).first()
        if not schedule:
            raise HTTPException(status_code=404, detail="Action schedule not found")
        
        if schedule.status != "pending":
            raise HTTPException(status_code=400, detail="Can only cancel pending schedules")
        
        schedule.status = "cancelled"
        schedule.updated_at = datetime.utcnow()
        
        db.commit()
        
        logger.info(f"Action schedule {schedule_id} cancelled")
        
        return {"status": "success", "message": "Action schedule cancelled"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error cancelling action schedule {schedule_id}: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="Failed to cancel action schedule")

# 统计信息
@router.get("/statistics/overview", response_model=ActionStatistics)
async def get_action_statistics(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db)
):
    """获取动作执行统计信息"""
    try:
        from datetime import timedelta
        
        # 计算时间范围
        start_date = datetime.utcnow() - timedelta(days=days)
        
        # 基础查询
        base_query = db.query(ActionExecution).filter(ActionExecution.created_at >= start_date)
        
        # 总执行数
        total_executions = base_query.count()
        
        # 成功执行数
        successful_executions = base_query.filter(ActionExecution.status == "completed").count()
        
        # 失败执行数
        failed_executions = base_query.filter(ActionExecution.status == "failed").count()
        
        # 待执行数
        pending_executions = base_query.filter(ActionExecution.status.in_(["pending", "running"])).count()
        
        # 按类型统计
        executions_by_type = {}
        type_counts = db.query(
            ActionTemplate.action_type,
            db.func.count(ActionExecution.id)
        ).join(
            ActionExecution, ActionTemplate.id == ActionExecution.template_id
        ).filter(
            ActionExecution.created_at >= start_date
        ).group_by(ActionTemplate.action_type).all()
        
        for action_type, count in type_counts:
            executions_by_type[action_type] = count
        
        # 按状态统计
        executions_by_status = {}
        for status in ["pending", "running", "completed", "failed", "cancelled"]:
            count = base_query.filter(ActionExecution.status == status).count()
            executions_by_status[status] = count
        
        # 平均执行时间
        avg_duration = db.query(db.func.avg(ActionExecution.duration)).filter(
            ActionExecution.created_at >= start_date,
            ActionExecution.duration.isnot(None)
        ).scalar() or 0.0
        
        return ActionStatistics(
            total_executions=total_executions,
            successful_executions=successful_executions,
            failed_executions=failed_executions,
            pending_executions=pending_executions,
            executions_by_type=executions_by_type,
            executions_by_status=executions_by_status,
            average_execution_time=float(avg_duration)
        )
    except Exception as e:
        logger.error(f"Error getting action statistics: {str(e)}")
        raise HTTPException(status_code=500, detail="Failed to get action statistics")