from typing import Dict, List, Optional, Any
import logging
import asyncio
from datetime import datetime, timedelta
from celery import Celery
from sqlalchemy.orm import Session
from ..models.alert import Alert, AlertAction, NotificationLog
from ..services import AlertProcessorService, NotificationService, AutoActionService, TicketSystemService
from ..database import get_db

logger = logging.getLogger(__name__)

# Celery应用配置
celery_app = Celery(
    'alert_handler',
    broker='redis://localhost:6379/0',
    backend='redis://localhost:6379/0'
)

celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_routes={
        'alert_handler.tasks.*': {'queue': 'alerts'}
    }
)

@celery_app.task(bind=True, max_retries=3)
def process_alert_task(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    处理告警的异步任务
    
    Args:
        alert_data: 告警数据
        
    Returns:
        Dict: 处理结果
    """
    try:
        logger.info(f"Processing alert task: {alert_data.get('id')}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 初始化服务
        alert_processor = AlertProcessorService()
        
        # 处理告警
        result = asyncio.run(alert_processor.process_alert(alert_data, db))
        
        logger.info(f"Alert {alert_data.get('id')} processed successfully")
        return result
        
    except Exception as e:
        logger.error(f"Error processing alert {alert_data.get('id')}: {str(e)}")
        
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying alert processing, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        return {
            'success': False,
            'error': str(e),
            'alert_id': alert_data.get('id'),
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task(bind=True, max_retries=3)
def send_notification_task(self, notification_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    发送通知的异步任务
    
    Args:
        notification_data: 通知数据
        
    Returns:
        Dict: 发送结果
    """
    try:
        logger.info(f"Sending notification: {notification_data.get('type')}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 初始化通知服务
        notification_service = NotificationService()
        
        # 发送通知
        notification_type = notification_data.get('type')
        if notification_type == 'email':
            result = asyncio.run(notification_service.send_email(
                to_emails=notification_data.get('to_emails'),
                subject=notification_data.get('subject'),
                content=notification_data.get('content'),
                content_type=notification_data.get('content_type', 'text')
            ))
        elif notification_type == 'sms':
            result = asyncio.run(notification_service.send_sms(
                phone_numbers=notification_data.get('phone_numbers'),
                message=notification_data.get('message')
            ))
        elif notification_type == 'webhook':
            result = asyncio.run(notification_service.send_webhook(
                url=notification_data.get('url'),
                data=notification_data.get('data'),
                headers=notification_data.get('headers')
            ))
        elif notification_type == 'slack':
            result = asyncio.run(notification_service.send_slack(
                channel=notification_data.get('channel'),
                message=notification_data.get('message'),
                attachments=notification_data.get('attachments')
            ))
        else:
            raise ValueError(f"Unsupported notification type: {notification_type}")
        
        # 记录通知日志
        if notification_data.get('alert_id'):
            notification_log = NotificationLog(
                alert_id=notification_data.get('alert_id'),
                notification_type=notification_type,
                recipient=str(notification_data.get('to_emails') or notification_data.get('phone_numbers') or notification_data.get('channel')),
                status='sent' if result.get('success') else 'failed',
                error_message=result.get('error') if not result.get('success') else None,
                sent_at=datetime.utcnow()
            )
            db.add(notification_log)
            db.commit()
        
        logger.info(f"Notification sent successfully: {notification_type}")
        return result
        
    except Exception as e:
        logger.error(f"Error sending notification: {str(e)}")
        
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying notification sending, attempt {self.request.retries + 1}")
            raise self.retry(countdown=30 * (2 ** self.request.retries))
        
        # 记录失败的通知日志
        if notification_data.get('alert_id'):
            try:
                db = next(get_db())
                notification_log = NotificationLog(
                    alert_id=notification_data.get('alert_id'),
                    notification_type=notification_data.get('type'),
                    recipient=str(notification_data.get('to_emails') or notification_data.get('phone_numbers') or notification_data.get('channel')),
                    status='failed',
                    error_message=str(e),
                    sent_at=datetime.utcnow()
                )
                db.add(notification_log)
                db.commit()
                db.close()
            except Exception as log_error:
                logger.error(f"Error logging notification failure: {str(log_error)}")
        
        return {
            'success': False,
            'error': str(e),
            'notification_type': notification_data.get('type'),
            'timestamp': datetime.utcnow().isoformat()
        }

@celery_app.task(bind=True, max_retries=3)
def execute_auto_action_task(self, action_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    执行自动处置动作的异步任务
    
    Args:
        action_data: 动作数据
        
    Returns:
        Dict: 执行结果
    """
    try:
        logger.info(f"Executing auto action: {action_data.get('action_type')}")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 初始化自动处置服务
        auto_action_service = AutoActionService()
        
        # 执行动作
        action_type = action_data.get('action_type')
        if action_type == 'restart_service':
            result = asyncio.run(auto_action_service.restart_service(
                service_name=action_data.get('service_name'),
                host=action_data.get('host')
            ))
        elif action_type == 'scale_service':
            result = asyncio.run(auto_action_service.scale_service(
                service_name=action_data.get('service_name'),
                replicas=action_data.get('replicas'),
                namespace=action_data.get('namespace')
            ))
        elif action_type == 'execute_script':
            result = asyncio.run(auto_action_service.execute_script(
                script_path=action_data.get('script_path'),
                args=action_data.get('args'),
                host=action_data.get('host')
            ))
        elif action_type == 'api_call':
            result = asyncio.run(auto_action_service.make_api_call(
                url=action_data.get('url'),
                method=action_data.get('method', 'POST'),
                data=action_data.get('data'),
                headers=action_data.get('headers')
            ))
        elif action_type == 'create_ticket':
            # 初始化工单系统服务
            ticket_service = TicketSystemService()
            
            # 获取告警信息
            alert = db.query(Alert).filter(Alert.id == action_data.get('alert_id')).first()
            if alert:
                result = asyncio.run(ticket_service.create_ticket(
                    alert=alert,
                    ticket_system=action_data.get('ticket_system'),
                    additional_fields=action_data.get('additional_fields')
                ))
            else:
                raise ValueError(f"Alert {action_data.get('alert_id')} not found")
        else:
            raise ValueError(f"Unsupported action type: {action_type}")
        
        # 记录动作执行结果
        if action_data.get('alert_id'):
            alert_action = AlertAction(
                alert_id=action_data.get('alert_id'),
                action_type=action_type,
                action_data=action_data,
                status='completed' if result.get('success') else 'failed',
                result=result,
                executed_at=datetime.utcnow()
            )
            db.add(alert_action)
            db.commit()
        
        logger.info(f"Auto action executed successfully: {action_type}")
        return result
        
    except Exception as e:
        logger.error(f"Error executing auto action: {str(e)}")
        
        # 重试机制
        if self.request.retries < self.max_retries:
            logger.info(f"Retrying auto action execution, attempt {self.request.retries + 1}")
            raise self.retry(countdown=60 * (2 ** self.request.retries))
        
        # 记录失败的动作执行结果
        if action_data.get('alert_id'):
            try:
                db = next(get_db())
                alert_action = AlertAction(
                    alert_id=action_data.get('alert_id'),
                    action_type=action_data.get('action_type'),
                    action_data=action_data,
                    status='failed',
                    result={'success': False, 'error': str(e)},
                    executed_at=datetime.utcnow()
                )
                db.add(alert_action)
                db.commit()
                db.close()
            except Exception as log_error:
                logger.error(f"Error logging action failure: {str(log_error)}")
        
        return {
            'success': False,
            'error': str(e),
            'action_type': action_data.get('action_type'),
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def cleanup_old_alerts_task() -> Dict[str, Any]:
    """
    清理旧告警数据的定时任务
    
    Returns:
        Dict: 清理结果
    """
    try:
        logger.info("Starting cleanup of old alerts")
        
        # 获取数据库会话
        db = next(get_db())
        
        # 清理30天前的已解决告警
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        # 查询需要清理的告警
        old_alerts = db.query(Alert).filter(
            Alert.status == 'resolved',
            Alert.created_at < cutoff_date
        ).all()
        
        cleaned_count = 0
        for alert in old_alerts:
            # 删除相关的通知日志
            db.query(NotificationLog).filter(NotificationLog.alert_id == alert.id).delete()
            
            # 删除相关的动作记录
            db.query(AlertAction).filter(AlertAction.alert_id == alert.id).delete()
            
            # 删除告警
            db.delete(alert)
            cleaned_count += 1
        
        db.commit()
        
        logger.info(f"Cleaned up {cleaned_count} old alerts")
        return {
            'success': True,
            'cleaned_count': cleaned_count,
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error cleaning up old alerts: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def health_check_task() -> Dict[str, Any]:
    """
    健康检查任务
    
    Returns:
        Dict: 健康状态
    """
    try:
        # 检查数据库连接
        db = next(get_db())
        db.execute("SELECT 1")
        db.close()
        
        return {
            'success': True,
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Health check failed: {str(e)}")
        return {
            'success': False,
            'status': 'unhealthy',
            'error': str(e),
            'timestamp': datetime.utcnow().isoformat()
        }

# 定时任务配置
celery_app.conf.beat_schedule = {
    'cleanup-old-alerts': {
        'task': 'alert_handler.tasks.alert_tasks.cleanup_old_alerts_task',
        'schedule': 86400.0,  # 每天执行一次
    },
    'health-check': {
        'task': 'alert_handler.tasks.alert_tasks.health_check_task',
        'schedule': 300.0,  # 每5分钟执行一次
    },
}