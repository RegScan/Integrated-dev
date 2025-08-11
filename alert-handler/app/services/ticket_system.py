from typing import Dict, List, Optional, Any
import logging
import aiohttp
import asyncio
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.alert import Alert

logger = logging.getLogger(__name__)

class TicketSystemService:
    """工单系统集成服务 - 负责与各种工单系统的集成"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化工单系统服务
        
        Args:
            config: 工单系统配置
        """
        self.config = config or {}
        self.default_system = self.config.get('default_system', 'jira')
        self.timeout = self.config.get('timeout', 30)
        
        # 各种工单系统的配置
        self.jira_config = self.config.get('jira', {})
        self.servicenow_config = self.config.get('servicenow', {})
        self.custom_config = self.config.get('custom', {})
    
    async def create_ticket(self, alert: Alert, ticket_system: Optional[str] = None,
                          additional_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建工单
        
        Args:
            alert: 告警对象
            ticket_system: 工单系统类型
            additional_fields: 额外字段
            
        Returns:
            Dict: 创建结果
        """
        try:
            system = ticket_system or self.default_system
            
            if system == 'jira':
                return await self._create_jira_ticket(alert, additional_fields)
            elif system == 'servicenow':
                return await self._create_servicenow_ticket(alert, additional_fields)
            elif system == 'custom':
                return await self._create_custom_ticket(alert, additional_fields)
            else:
                raise ValueError(f"Unsupported ticket system: {system}")
                
        except Exception as e:
            logger.error(f"Error creating ticket for alert {alert.id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _create_jira_ticket(self, alert: Alert, additional_fields: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        创建JIRA工单
        
        Args:
            alert: 告警对象
            additional_fields: 额外字段
            
        Returns:
            Dict: 创建结果
        """
        if not self.jira_config:
            raise ValueError("JIRA configuration not provided")
        
        # JIRA API配置
        base_url = self.jira_config.get('base_url')
        username = self.jira_config.get('username')
        api_token = self.jira_config.get('api_token')
        project_key = self.jira_config.get('project_key')
        issue_type = self.jira_config.get('issue_type', 'Bug')
        
        if not all([base_url, username, api_token, project_key]):
            raise ValueError("Missing required JIRA configuration")
        
        # 构建工单数据
        ticket_data = {
            'fields': {
                'project': {'key': project_key},
                'summary': f"[告警] {alert.title}",
                'description': self._format_alert_description(alert),
                'issuetype': {'name': issue_type},
                'priority': {'name': self._map_severity_to_jira_priority(alert.severity)},
                'labels': ['alert', f'severity-{alert.severity}', f'source-{alert.source}']
            }
        }
        
        # 添加额外字段
        if additional_fields:
            ticket_data['fields'].update(additional_fields)
        
        # 发送请求
        auth = aiohttp.BasicAuth(username, api_token)
        headers = {'Content-Type': 'application/json'}
        
        async with aiohttp.ClientSession(auth=auth, timeout=aiohttp.ClientTimeout(total=self.timeout)) as session:
            async with session.post(
                f"{base_url}/rest/api/2/issue",
                json=ticket_data,
                headers=headers
            ) as response:
                if response.status == 201:
                    result = await response.json()
                    ticket_id = result.get('key')
                    ticket_url = f"{base_url}/browse/{ticket_id}"
                    
                    logger.info(f"JIRA ticket {ticket_id} created for alert {alert.id}")
                    
                    return {
                        'success': True,
                        'ticket_id': ticket_id,
                        'ticket_url': ticket_url,
                        'system': 'jira',
                        'timestamp': datetime.utcnow().isoformat()
                    }
                else:
                    error_text = await response.text()
                    raise Exception(f"JIRA API error {response.status}: {error_text}")
    
    def _format_alert_description(self, alert: Alert) -> str:
        """
        格式化告警描述
        
        Args:
            alert: 告警对象
            
        Returns:
            str: 格式化后的描述
        """
        description_parts = [
            f"告警ID: {alert.id}",
            f"告警标题: {alert.title}",
            f"告警级别: {alert.severity}",
            f"告警来源: {alert.source}",
            f"告警状态: {alert.status}",
            f"创建时间: {alert.created_at.isoformat() if alert.created_at else 'N/A'}",
            "",
            "告警详情:",
            alert.description or "无详细描述"
        ]
        
        if alert.tags:
            description_parts.extend([
                "",
                "标签信息:",
                str(alert.tags)
            ])
        
        return "\n".join(description_parts)
    
    def _map_severity_to_jira_priority(self, severity: str) -> str:
        """
        将告警级别映射到JIRA优先级
        
        Args:
            severity: 告警级别
            
        Returns:
            str: JIRA优先级
        """
        mapping = {
            'critical': 'Highest',
            'high': 'High',
            'medium': 'Medium',
            'low': 'Low',
            'info': 'Lowest'
        }
        return mapping.get(severity.lower(), 'Medium')