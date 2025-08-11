from sqlalchemy import Column, String, DateTime, Integer, Text, JSON, Boolean, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()

class Alert(Base):
    """告警模型"""
    __tablename__ = "alerts"
    
    # 基础字段
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(100), unique=True, nullable=False, comment="告警唯一标识")
    
    # 告警来源信息
    source_module = Column(String(50), nullable=False, comment="告警来源模块")
    source_ip = Column(String(45), comment="源IP地址")
    target_url = Column(String(500), comment="目标URL")
    domain = Column(String(255), comment="域名")
    
    # 告警内容
    alert_type = Column(String(50), nullable=False, comment="告警类型")
    severity = Column(String(20), nullable=False, comment="严重级别: low/medium/high/critical")
    title = Column(String(200), nullable=False, comment="告警标题")
    description = Column(Text, comment="告警描述")
    evidence = Column(JSON, comment="证据数据")
    
    # 状态管理
    status = Column(String(20), default="open", comment="告警状态: open/in_progress/resolved/closed")
    priority = Column(Integer, default=3, comment="优先级: 1-5")
    
    # 处理信息
    assigned_to = Column(String(100), comment="分配给")
    handler = Column(String(100), comment="处理人")
    resolution = Column(Text, comment="解决方案")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    resolved_at = Column(DateTime, comment="解决时间")
    
    # 通知相关
    notification_sent = Column(Boolean, default=False, comment="是否已发送通知")
    notification_channels = Column(JSON, comment="通知渠道")
    
    # 关联关系
    actions = relationship("AlertAction", back_populates="alert", cascade="all, delete-orphan")
    notifications = relationship("NotificationLog", back_populates="alert", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<Alert(id={self.id}, alert_id={self.alert_id}, severity={self.severity})>"
    
    def to_dict(self):
        """转换为字典格式"""
        return {
            "id": self.id,
            "alert_id": self.alert_id,
            "source_module": self.source_module,
            "source_ip": self.source_ip,
            "target_url": self.target_url,
            "domain": self.domain,
            "alert_type": self.alert_type,
            "severity": self.severity,
            "title": self.title,
            "description": self.description,
            "evidence": self.evidence,
            "status": self.status,
            "priority": self.priority,
            "assigned_to": self.assigned_to,
            "handler": self.handler,
            "resolution": self.resolution,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
            "notification_sent": self.notification_sent,
            "notification_channels": self.notification_channels
        }

class AlertAction(Base):
    """告警处置动作模型"""
    __tablename__ = "alert_actions"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False)
    
    # 动作信息
    action_type = Column(String(50), nullable=False, comment="动作类型")
    action_name = Column(String(100), nullable=False, comment="动作名称")
    action_params = Column(JSON, comment="动作参数")
    
    # 执行状态
    status = Column(String(20), default="pending", comment="执行状态: pending/running/success/failed")
    result = Column(JSON, comment="执行结果")
    error_message = Column(Text, comment="错误信息")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow)
    executed_at = Column(DateTime, comment="执行时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 关联关系
    alert = relationship("Alert", back_populates="actions")
    
    def __repr__(self):
        return f"<AlertAction(id={self.id}, action_type={self.action_type}, status={self.status})>"

class NotificationLog(Base):
    """通知日志模型"""
    __tablename__ = "notification_logs"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    alert_id = Column(String(36), ForeignKey("alerts.id"), nullable=False)
    
    # 通知信息
    channel = Column(String(50), nullable=False, comment="通知渠道: email/sms/webhook")
    recipient = Column(String(200), nullable=False, comment="接收人")
    subject = Column(String(200), comment="主题")
    content = Column(Text, comment="通知内容")
    
    # 发送状态
    status = Column(String(20), default="pending", comment="发送状态: pending/sent/failed")
    error_message = Column(Text, comment="错误信息")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow)
    sent_at = Column(DateTime, comment="发送时间")
    
    # 关联关系
    alert = relationship("Alert", back_populates="notifications")
    
    def __repr__(self):
        return f"<NotificationLog(id={self.id}, channel={self.channel}, status={self.status})>"

class AlertRule(Base):
    """告警规则模型"""
    __tablename__ = "alert_rules"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    
    # 规则信息
    name = Column(String(100), nullable=False, comment="规则名称")
    description = Column(Text, comment="规则描述")
    rule_type = Column(String(50), nullable=False, comment="规则类型")
    
    # 匹配条件
    conditions = Column(JSON, nullable=False, comment="匹配条件")
    
    # 动作配置
    actions = Column(JSON, comment="触发动作")
    notification_config = Column(JSON, comment="通知配置")
    
    # 状态管理
    enabled = Column(Boolean, default=True, comment="是否启用")
    priority = Column(Integer, default=3, comment="优先级")
    
    # 时间字段
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f"<AlertRule(id={self.id}, name={self.name}, enabled={self.enabled})>"