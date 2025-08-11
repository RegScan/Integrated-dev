from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class ActionTemplate(Base):
    """处置动作模板模型"""
    __tablename__ = "action_templates"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 模板信息
    name = Column(String(100), nullable=False, comment="模板名称")
    description = Column(Text, comment="模板描述")
    action_type = Column(String(50), nullable=False, comment="动作类型")
    
    # 模板配置
    template_config = Column(JSON, nullable=False, comment="模板配置")
    default_params = Column(JSON, comment="默认参数")
    required_params = Column(JSON, comment="必需参数")
    
    # 执行配置
    timeout = Column(Integer, default=300, comment="超时时间(秒)")
    retry_count = Column(Integer, default=3, comment="重试次数")
    retry_interval = Column(Integer, default=60, comment="重试间隔(秒)")
    
    # 状态管理
    enabled = Column(Boolean, default=True, comment="是否启用")
    category = Column(String(50), comment="动作分类")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<ActionTemplate(id={self.id}, name={self.name}, action_type={self.action_type})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "action_type": self.action_type,
            "template_config": self.template_config,
            "default_params": self.default_params,
            "required_params": self.required_params,
            "timeout": self.timeout,
            "retry_count": self.retry_count,
            "retry_interval": self.retry_interval,
            "enabled": self.enabled,
            "category": self.category,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None
        }

class ActionExecution(Base):
    """动作执行记录模型"""
    __tablename__ = "action_executions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联信息
    alert_id = Column(String(36), comment="关联告警ID")
    template_id = Column(String(36), ForeignKey("action_templates.id"), comment="模板ID")
    
    # 执行信息
    execution_id = Column(String(100), unique=True, nullable=False, comment="执行唯一标识")
    action_type = Column(String(50), nullable=False, comment="动作类型")
    action_name = Column(String(100), nullable=False, comment="动作名称")
    
    # 执行参数
    input_params = Column(JSON, comment="输入参数")
    execution_context = Column(JSON, comment="执行上下文")
    
    # 执行状态
    status = Column(String(20), default="pending", comment="执行状态: pending/running/success/failed/timeout/cancelled")
    progress = Column(Integer, default=0, comment="执行进度(0-100)")
    
    # 执行结果
    result = Column(JSON, comment="执行结果")
    output_data = Column(JSON, comment="输出数据")
    error_message = Column(Text, comment="错误信息")
    error_code = Column(String(50), comment="错误代码")
    
    # 重试信息
    retry_count = Column(Integer, default=0, comment="已重试次数")
    max_retries = Column(Integer, default=3, comment="最大重试次数")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    started_at = Column(DateTime, comment="开始执行时间")
    completed_at = Column(DateTime, comment="完成时间")
    timeout_at = Column(DateTime, comment="超时时间")
    
    # 执行环境
    executor = Column(String(100), comment="执行者")
    execution_node = Column(String(100), comment="执行节点")
    
    # 关联关系
    template = relationship("ActionTemplate")
    
    def __repr__(self):
        return f"<ActionExecution(id={self.id}, execution_id={self.execution_id}, status={self.status})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "template_id": self.template_id,
            "execution_id": self.execution_id,
            "action_type": self.action_type,
            "action_name": self.action_name,
            "input_params": self.input_params,
            "execution_context": self.execution_context,
            "status": self.status,
            "progress": self.progress,
            "result": self.result,
            "output_data": self.output_data,
            "error_message": self.error_message,
            "error_code": self.error_code,
            "retry_count": self.retry_count,
            "max_retries": self.max_retries,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "timeout_at": self.timeout_at.isoformat() if self.timeout_at else None,
            "executor": self.executor,
            "execution_node": self.execution_node
        }

class ActionSchedule(Base):
    """动作调度模型"""
    __tablename__ = "action_schedules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 调度信息
    schedule_name = Column(String(100), nullable=False, comment="调度名称")
    template_id = Column(String(36), ForeignKey("action_templates.id"), nullable=False)
    
    # 调度配置
    schedule_type = Column(String(20), nullable=False, comment="调度类型: cron/interval/once")
    schedule_config = Column(JSON, nullable=False, comment="调度配置")
    
    # 执行参数
    default_params = Column(JSON, comment="默认参数")
    
    # 状态管理
    enabled = Column(Boolean, default=True, comment="是否启用")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_run_at = Column(DateTime, comment="上次执行时间")
    next_run_at = Column(DateTime, comment="下次执行时间")
    
    # 关联关系
    template = relationship("ActionTemplate")
    
    def __repr__(self):
        return f"<ActionSchedule(id={self.id}, schedule_name={self.schedule_name}, enabled={self.enabled})>"

class ActionAuditLog(Base):
    """动作审计日志模型"""
    __tablename__ = "action_audit_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 关联信息
    execution_id = Column(String(36), ForeignKey("action_executions.id"), comment="执行记录ID")
    
    # 审计信息
    operation = Column(String(50), nullable=False, comment="操作类型")
    operator = Column(String(100), comment="操作者")
    operation_details = Column(JSON, comment="操作详情")
    
    # 变更信息
    before_state = Column(JSON, comment="变更前状态")
    after_state = Column(JSON, comment="变更后状态")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # 关联关系
    execution = relationship("ActionExecution")
    
    def __repr__(self):
        return f"<ActionAuditLog(id={self.id}, operation={self.operation}, operator={self.operator})>"