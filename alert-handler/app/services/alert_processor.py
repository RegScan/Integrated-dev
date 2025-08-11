from typing import Dict, List, Optional, Any
from datetime import datetime
from sqlalchemy.orm import Session
from jinja2 import Template, Environment, FileSystemLoader
import uuid
import logging
import json
import os

from ..models.alert import Alert, AlertRule, NotificationLog
from ..services.notification import NotificationService
from ..services.auto_action import AutoActionService

logger = logging.getLogger(__name__)

class AlertProcessorService:
    """告警处理服务"""
    
    def __init__(self, notification_service: NotificationService):
        self.notification_service = notification_service
        self.auto_action_service = AutoActionService()
        
        # 初始化模板环境
        template_dir = os.path.join(os.path.dirname(__file__), '..', '..', 'templates')
        self.template_env = Environment(loader=FileSystemLoader(template_dir))
        
        # 告警级别映射
        self.severity_mapping = {
            'low': 1,
            'medium': 2, 
            'high': 3,
            'critical': 4
        }
    
    async def process_alert(self, alert_data: Dict[str, Any], db: Session) -> Alert:
        """
        处理告警数据
        
        Args:
            alert_data: 告警数据
            db: 数据库会话
            
        Returns:
            Alert: 创建的告警对象
        """
        try:
            # 1. 数据验证和预处理
            processed_data = self._preprocess_alert_data(alert_data)
            
            # 2. 创建告警记录
            alert = self._create_alert_record(processed_data, db)
            
            # 3. 应用告警规则
            matched_rules = self._match_alert_rules(alert, db)
            
            # 4. 发送通知
            if self._should_send_notification(alert, matched_rules):
                await self._send_notifications(alert, matched_rules, db)
            
            # 5. 触发自动处置
            if self._should_trigger_auto_action(alert, matched_rules):
                await self._trigger_auto_actions(alert, matched_rules, db)
            
            # 6. 更新告警状态
            alert.status = "open"
            db.commit()
            
            logger.info(f"Alert processed successfully: {alert.alert_id}")
            return alert
            
        except Exception as e:
            logger.error(f"Error processing alert: {str(e)}")
            db.rollback()
            raise
    
    def _preprocess_alert_data(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        预处理告警数据
        """
        processed = alert_data.copy()
        
        # 生成告警ID
        if 'alert_id' not in processed:
            processed['alert_id'] = f"ALT-{datetime.utcnow().strftime('%Y%m%d%H%M%S')}-{str(uuid.uuid4())[:8]}"
        
        # 设置默认值
        processed.setdefault('priority', 3)
        processed.setdefault('status', 'pending')
        processed.setdefault('notification_sent', False)
        processed.setdefault('notification_channels', {})
        
        # 标准化严重级别
        if 'severity' in processed:
            processed['severity'] = processed['severity'].lower()
            if processed['severity'] not in self.severity_mapping:
                processed['severity'] = 'medium'
        
        return processed
    
    def _create_alert_record(self, alert_data: Dict[str, Any], db: Session) -> Alert:
        """
        创建告警记录
        """
        alert = Alert(
            alert_id=alert_data['alert_id'],
            source_module=alert_data['source_module'],
            source_ip=alert_data.get('source_ip'),
            target_url=alert_data.get('target_url'),
            domain=alert_data.get('domain'),
            alert_type=alert_data['alert_type'],
            severity=alert_data['severity'],
            title=alert_data['title'],
            description=alert_data.get('description'),
            evidence=alert_data.get('evidence'),
            status=alert_data['status'],
            priority=alert_data['priority'],
            notification_sent=alert_data['notification_sent'],
            notification_channels=alert_data['notification_channels'],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(alert)
        db.flush()  # 获取ID但不提交
        
        return alert
    
    def _match_alert_rules(self, alert: Alert, db: Session) -> List[AlertRule]:
        """
        匹配告警规则
        """
        try:
            # 查询所有激活的告警规则
            rules = db.query(AlertRule).filter(
                AlertRule.is_active == True
            ).all()
            
            matched_rules = []
            
            for rule in rules:
                if self._rule_matches_alert(rule, alert):
                    matched_rules.append(rule)
                    logger.info(f"Alert {alert.alert_id} matched rule: {rule.name}")
            
            return matched_rules
            
        except Exception as e:
            logger.error(f"Error matching alert rules: {str(e)}")
            return []
    
    def _rule_matches_alert(self, rule: AlertRule, alert: Alert) -> bool:
        """
        检查规则是否匹配告警
        """
        try:
            conditions = rule.conditions or {}
            
            # 检查严重级别
            if 'severity' in conditions:
                required_severities = conditions['severity']
                if isinstance(required_severities, str):
                    required_severities = [required_severities]
                if alert.severity not in required_severities:
                    return False
            
            # 检查告警类型
            if 'alert_type' in conditions:
                required_types = conditions['alert_type']
                if isinstance(required_types, str):
                    required_types = [required_types]
                if alert.alert_type not in required_types:
                    return False
            
            # 检查来源模块
            if 'source_module' in conditions:
                required_modules = conditions['source_module']
                if isinstance(required_modules, str):
                    required_modules = [required_modules]
                if alert.source_module not in required_modules:
                    return False
            
            # 检查域名
            if 'domain' in conditions and alert.domain:
                required_domains = conditions['domain']
                if isinstance(required_domains, str):
                    required_domains = [required_domains]
                if alert.domain not in required_domains:
                    return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error checking rule match: {str(e)}")
            return False
    
    def _should_send_notification(self, alert: Alert, matched_rules: List[AlertRule]) -> bool:
        """
        判断是否应该发送通知
        """
        # 如果有匹配的规则且规则要求发送通知
        for rule in matched_rules:
            if rule.actions and rule.actions.get('send_notification', False):
                return True
        
        # 默认规则：高危和严重告警发送通知
        return alert.severity in ['high', 'critical']
    
    async def _send_notifications(self, alert: Alert, matched_rules: List[AlertRule], db: Session):
        """
        发送通知
        """
        try:
            notification_channels = []
            
            # 从规则中获取通知配置
            for rule in matched_rules:
                if rule.actions and 'notification_channels' in rule.actions:
                    channels = rule.actions['notification_channels']
                    if isinstance(channels, list):
                        notification_channels.extend(channels)
                    else:
                        notification_channels.append(channels)
            
            # 如果没有规则指定，使用默认通知渠道
            if not notification_channels:
                notification_channels = ['email']  # 默认邮件通知
            
            # 去重
            notification_channels = list(set(notification_channels))
            
            # 发送通知
            notification_results = {}
            
            for channel in notification_channels:
                try:
                    if channel == 'email':
                        result = await self._send_email_notification(alert)
                        notification_results['email'] = result
                    elif channel == 'sms':
                        result = await self._send_sms_notification(alert)
                        notification_results['sms'] = result
                    elif channel == 'webhook':
                        result = await self._send_webhook_notification(alert)
                        notification_results['webhook'] = result
                    
                    # 记录通知日志
                    self._log_notification(alert.id, channel, result, db)
                    
                except Exception as e:
                    logger.error(f"Error sending {channel} notification: {str(e)}")
                    notification_results[channel] = {'success': False, 'error': str(e)}
            
            # 更新告警通知状态
            alert.notification_sent = any(r.get('success', False) for r in notification_results.values())
            alert.notification_channels = notification_results
            
        except Exception as e:
            logger.error(f"Error sending notifications: {str(e)}")
    
    async def _send_email_notification(self, alert: Alert) -> Dict[str, Any]:
        """
        发送邮件通知
        """
        try:
            # 渲染邮件模板
            template = self.template_env.get_template('email_alert.html')
            email_body = template.render(alert=alert.to_dict())
            
            # 发送邮件
            result = await self.notification_service.send_email(
                to_email='admin@example.com',  # 应从配置获取
                subject=f"【{alert.severity.upper()}】告警：{alert.title}",
                message=email_body
            )
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            logger.error(f"Error sending email notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _send_sms_notification(self, alert: Alert) -> Dict[str, Any]:
        """
        发送短信通知
        """
        try:
            # 渲染短信模板
            template = self.template_env.get_template('sms_alert.txt')
            sms_body = template.render(alert=alert.to_dict())
            
            # 发送短信
            result = await self.notification_service.send_sms(
                to_phone='+1234567890',  # 应从配置获取
                message=sms_body
            )
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            logger.error(f"Error sending SMS notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    async def _send_webhook_notification(self, alert: Alert) -> Dict[str, Any]:
        """
        发送Webhook通知
        """
        try:
            # 发送Webhook
            result = await self.notification_service.send_webhook(
                url='https://example.com/webhook',  # 应从配置获取
                data=alert.to_dict()
            )
            
            return {'success': True, 'result': result}
            
        except Exception as e:
            logger.error(f"Error sending webhook notification: {str(e)}")
            return {'success': False, 'error': str(e)}
    
    def _log_notification(self, alert_id: str, channel: str, result: Dict[str, Any], db: Session):
        """
        记录通知日志
        """
        try:
            log = NotificationLog(
                alert_id=alert_id,
                channel=channel,
                status='success' if result.get('success') else 'failed',
                message=json.dumps(result),
                sent_at=datetime.utcnow()
            )
            
            db.add(log)
            
        except Exception as e:
            logger.error(f"Error logging notification: {str(e)}")
    
    def _should_trigger_auto_action(self, alert: Alert, matched_rules: List[AlertRule]) -> bool:
        """
        判断是否应该触发自动处置
        """
        for rule in matched_rules:
            if rule.actions and rule.actions.get('auto_action', False):
                return True
        
        # 默认规则：严重告警触发自动处置
        return alert.severity == 'critical'
    
    async def _trigger_auto_actions(self, alert: Alert, matched_rules: List[AlertRule], db: Session):
        """
        触发自动处置
        """
        try:
            for rule in matched_rules:
                if rule.actions and 'auto_actions' in rule.actions:
                    actions = rule.actions['auto_actions']
                    if isinstance(actions, list):
                        for action in actions:
                            await self.auto_action_service.execute_action(
                                action['template_id'],
                                alert.id,
                                action.get('parameters', {}),
                                db
                            )
                    else:
                        await self.auto_action_service.execute_action(
                            actions['template_id'],
                            alert.id,
                            actions.get('parameters', {}),
                            db
                        )
            
        except Exception as e:
            logger.error(f"Error triggering auto actions: {str(e)}")