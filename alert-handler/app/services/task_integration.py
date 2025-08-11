import asyncio
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime, timedelta
import sys
import os
import json

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from utils.config_client import config_client

logger = logging.getLogger(__name__)

class TaskIntegration:
    """任务集成服务 - 处理告警与任务调度系统的集成"""
    
    def __init__(self):
        self.config_client = config_client
        self.task_enabled = True
        self.auto_action_enabled = True
        self.celery_broker_url = "redis://localhost:6379/0"
        self.celery_app = None
    
    async def initialize(self):
        """初始化任务集成配置"""
        try:
            # 从配置服务获取任务相关配置
            self.task_enabled = await self.config_client.get_config(
                "task_enabled", True, "alert-handler"
            )
            self.auto_action_enabled = await self.config_client.get_config(
                "auto_action_enabled", True, "alert-handler"
            )
            self.celery_broker_url = await self.config_client.get_config(
                "celery_broker_url", "redis://localhost:6379/0", "task-scheduler"
            )
            
            # 初始化Celery连接
            await self._initialize_celery()
            
            logger.info(f"Task integration initialized: enabled={self.task_enabled}, auto_action={self.auto_action_enabled}")
        except Exception as e:
            logger.error(f"Failed to initialize task integration: {e}")
    
    async def _initialize_celery(self):
        """初始化Celery连接"""
        try:
            from celery import Celery
            
            self.celery_app = Celery(
                'alert_handler',
                broker=self.celery_broker_url,
                backend=self.celery_broker_url
            )
            
            # 配置Celery
            self.celery_app.conf.update(
                task_serializer='json',
                accept_content=['json'],
                result_serializer='json',
                timezone='Asia/Shanghai',
                enable_utc=True,
                task_routes={
                    'alert_handler.tasks.*': {'queue': 'alert_queue'},
                    'notification.tasks.*': {'queue': 'notification_queue'},
                    'scanner.tasks.*': {'queue': 'scanner_queue'}
                }
            )
            
            logger.info("Celery connection initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Celery: {e}")
            self.celery_app = None
    
    async def schedule_alert_action(self, alert_data: Dict[str, Any], 
                                  action_type: str, delay_seconds: int = 0) -> Optional[str]:
        """调度告警处理任务"""
        if not self.task_enabled or not self.celery_app:
            logger.warning("Task scheduling is disabled or Celery not available")
            return None
        
        try:
            task_data = {
                "alert_id": alert_data.get("id"),
                "action_type": action_type,
                "alert_data": alert_data,
                "scheduled_at": datetime.now().isoformat(),
                "metadata": {
                    "source": "alert-handler",
                    "priority": alert_data.get("priority", 3),
                    "severity": alert_data.get("severity", "medium")
                }
            }
            
            # 根据动作类型选择任务
            task_name = self._get_task_name(action_type)
            
            if delay_seconds > 0:
                # 延迟执行
                eta = datetime.now() + timedelta(seconds=delay_seconds)
                result = self.celery_app.send_task(
                    task_name,
                    args=[task_data],
                    eta=eta,
                    queue=self._get_queue_name(action_type)
                )
            else:
                # 立即执行
                result = self.celery_app.send_task(
                    task_name,
                    args=[task_data],
                    queue=self._get_queue_name(action_type)
                )
            
            logger.info(f"Scheduled task {task_name} for alert {alert_data.get('id')}: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to schedule alert action: {e}")
            return None
    
    def _get_task_name(self, action_type: str) -> str:
        """根据动作类型获取任务名称"""
        task_mapping = {
            "send_notification": "notification.tasks.send_alert_notification",
            "send_email": "notification.tasks.send_email_notification",
            "send_sms": "notification.tasks.send_sms_notification",
            "send_webhook": "notification.tasks.send_webhook_notification",
            "auto_block": "security.tasks.auto_block_domain",
            "escalate": "alert_handler.tasks.escalate_alert",
            "rescan": "scanner.tasks.rescan_domain",
            "generate_report": "reporting.tasks.generate_alert_report",
            "update_blacklist": "security.tasks.update_domain_blacklist",
            "create_ticket": "integration.tasks.create_support_ticket"
        }
        
        return task_mapping.get(action_type, "alert_handler.tasks.process_generic_action")
    
    def _get_queue_name(self, action_type: str) -> str:
        """根据动作类型获取队列名称"""
        queue_mapping = {
            "send_notification": "notification_queue",
            "send_email": "notification_queue",
            "send_sms": "notification_queue",
            "send_webhook": "notification_queue",
            "auto_block": "security_queue",
            "escalate": "alert_queue",
            "rescan": "scanner_queue",
            "generate_report": "reporting_queue",
            "update_blacklist": "security_queue",
            "create_ticket": "integration_queue"
        }
        
        return queue_mapping.get(action_type, "alert_queue")
    
    async def schedule_notification(self, alert_data: Dict[str, Any], 
                                  notification_config: Dict[str, Any]) -> List[str]:
        """调度通知任务"""
        task_ids = []
        
        if not self.task_enabled:
            return task_ids
        
        try:
            # 根据配置发送不同类型的通知
            if notification_config.get("email_enabled", False):
                task_id = await self.schedule_alert_action(alert_data, "send_email")
                if task_id:
                    task_ids.append(task_id)
            
            if notification_config.get("sms_enabled", False):
                task_id = await self.schedule_alert_action(alert_data, "send_sms")
                if task_id:
                    task_ids.append(task_id)
            
            if notification_config.get("webhook_enabled", False):
                task_id = await self.schedule_alert_action(alert_data, "send_webhook")
                if task_id:
                    task_ids.append(task_id)
            
            logger.info(f"Scheduled {len(task_ids)} notification tasks for alert {alert_data.get('id')}")
            
        except Exception as e:
            logger.error(f"Failed to schedule notifications: {e}")
        
        return task_ids
    
    async def schedule_auto_actions(self, alert_data: Dict[str, Any]) -> List[str]:
        """调度自动化处理动作"""
        task_ids = []
        
        if not self.auto_action_enabled:
            return task_ids
        
        try:
            severity = alert_data.get("severity", "medium")
            alert_type = alert_data.get("alert_type", "")
            
            # 根据告警严重程度和类型确定自动化动作
            auto_actions = await self._determine_auto_actions(alert_data)
            
            for action in auto_actions:
                action_type = action.get("type")
                delay = action.get("delay", 0)
                
                task_id = await self.schedule_alert_action(
                    alert_data, action_type, delay
                )
                
                if task_id:
                    task_ids.append(task_id)
            
            logger.info(f"Scheduled {len(task_ids)} auto actions for alert {alert_data.get('id')}")
            
        except Exception as e:
            logger.error(f"Failed to schedule auto actions: {e}")
        
        return task_ids
    
    async def _determine_auto_actions(self, alert_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """确定自动化处理动作"""
        actions = []
        
        severity = alert_data.get("severity", "medium")
        alert_type = alert_data.get("alert_type", "")
        confidence = alert_data.get("evidence", {}).get("confidence", 0)
        
        # 获取自动化规则配置
        auto_rules = await self.config_client.get_configs_by_category("auto_actions")
        
        # 立即通知
        if severity in ["critical", "high"]:
            actions.append({"type": "send_notification", "delay": 0})
        
        # 自动阻断（仅对高置信度的严重告警）
        if (severity == "critical" and confidence > 0.9 and 
            auto_rules.get("auto_block_enabled", "false").lower() == "true"):
            actions.append({"type": "auto_block", "delay": 60})  # 1分钟后执行
        
        # 自动重扫（对中等置信度的告警）
        if (0.5 <= confidence <= 0.8 and 
            auto_rules.get("auto_rescan_enabled", "false").lower() == "true"):
            actions.append({"type": "rescan", "delay": 300})  # 5分钟后重扫
        
        # 告警升级（对未处理的高优先级告警）
        if alert_data.get("priority", 3) <= 2:
            escalation_delay = int(auto_rules.get("escalation_delay", "1800"))  # 默认30分钟
            actions.append({"type": "escalate", "delay": escalation_delay})
        
        # 生成报告（对所有告警）
        if auto_rules.get("auto_report_enabled", "false").lower() == "true":
            actions.append({"type": "generate_report", "delay": 600})  # 10分钟后生成报告
        
        return actions
    
    async def cancel_scheduled_task(self, task_id: str) -> bool:
        """取消已调度的任务"""
        if not self.celery_app:
            return False
        
        try:
            self.celery_app.control.revoke(task_id, terminate=True)
            logger.info(f"Cancelled task {task_id}")
            return True
        except Exception as e:
            logger.error(f"Failed to cancel task {task_id}: {e}")
            return False
    
    async def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """获取任务状态"""
        if not self.celery_app:
            return {"status": "unknown", "error": "Celery not available"}
        
        try:
            result = self.celery_app.AsyncResult(task_id)
            return {
                "task_id": task_id,
                "status": result.status,
                "result": result.result if result.ready() else None,
                "traceback": result.traceback if result.failed() else None
            }
        except Exception as e:
            logger.error(f"Failed to get task status {task_id}: {e}")
            return {"status": "error", "error": str(e)}
    
    async def schedule_periodic_cleanup(self) -> Optional[str]:
        """调度定期清理任务"""
        if not self.task_enabled or not self.celery_app:
            return None
        
        try:
            # 调度每日清理任务
            result = self.celery_app.send_task(
                "alert_handler.tasks.cleanup_old_alerts",
                queue="maintenance_queue"
            )
            
            logger.info(f"Scheduled periodic cleanup task: {result.id}")
            return result.id
            
        except Exception as e:
            logger.error(f"Failed to schedule cleanup task: {e}")
            return None
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            celery_healthy = False
            if self.celery_app:
                # 检查Celery连接
                inspect = self.celery_app.control.inspect()
                stats = inspect.stats()
                celery_healthy = stats is not None and len(stats) > 0
            
            config_service_healthy = await self.config_client.health_check()
            
            return {
                "task_integration_enabled": self.task_enabled,
                "auto_action_enabled": self.auto_action_enabled,
                "celery_healthy": celery_healthy,
                "config_service_healthy": config_service_healthy,
                "broker_url": self.celery_broker_url,
                "status": "healthy" if celery_healthy and config_service_healthy else "unhealthy"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# 全局实例
task_integration = TaskIntegration()


# 便捷函数
async def schedule_alert_processing(alert_data: Dict[str, Any]) -> Dict[str, List[str]]:
    """调度告警处理的便捷函数"""
    result = {
        "notification_tasks": [],
        "auto_action_tasks": []
    }
    
    # 获取通知配置
    notification_config = await task_integration.config_client.get_configs_by_category("notifications")
    
    # 调度通知任务
    notification_tasks = await task_integration.schedule_notification(alert_data, notification_config)
    result["notification_tasks"] = notification_tasks
    
    # 调度自动化动作
    auto_action_tasks = await task_integration.schedule_auto_actions(alert_data)
    result["auto_action_tasks"] = auto_action_tasks
    
    return result


async def initialize_task_integration():
    """初始化任务集成的便捷函数"""
    await task_integration.initialize()