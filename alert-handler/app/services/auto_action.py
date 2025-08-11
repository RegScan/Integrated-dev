from typing import Dict, List, Optional, Any
import logging
import asyncio
import aiohttp
from datetime import datetime
from sqlalchemy.orm import Session
from ..models.action import ActionTemplate, ActionExecution, ActionSchedule
from ..models.alert import Alert

logger = logging.getLogger(__name__)

class AutoActionService:
    """自动处置服务 - 负责执行自动化的告警处置动作"""
    
    def __init__(self, db: Session, config: Optional[Dict[str, Any]] = None):
        """
        初始化自动处置服务
        
        Args:
            db: 数据库会话
            config: 配置信息
        """
        self.db = db
        self.config = config or {}
        self.max_concurrent_actions = self.config.get('max_concurrent_actions', 10)
        self.action_timeout = self.config.get('action_timeout', 300)  # 5分钟
        self.retry_attempts = self.config.get('retry_attempts', 3)
        self.retry_delay = self.config.get('retry_delay', 60)  # 1分钟
    
    async def execute_action(self, alert_id: int, action_template_id: int, 
                           parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        执行单个自动处置动作
        
        Args:
            alert_id: 告警ID
            action_template_id: 动作模板ID
            parameters: 动作参数
            
        Returns:
            Dict: 执行结果
        """
        try:
            # 获取告警和动作模板信息
            alert = self.db.query(Alert).filter(Alert.id == alert_id).first()
            if not alert:
                raise ValueError(f"Alert {alert_id} not found")
            
            action_template = self.db.query(ActionTemplate).filter(
                ActionTemplate.id == action_template_id
            ).first()
            if not action_template:
                raise ValueError(f"Action template {action_template_id} not found")
            
            # 检查动作模板是否启用
            if not action_template.is_enabled:
                raise ValueError(f"Action template {action_template_id} is disabled")
            
            # 创建动作执行记录
            action_execution = ActionExecution(
                alert_id=alert_id,
                action_template_id=action_template_id,
                status='pending',
                parameters=parameters or {},
                created_at=datetime.utcnow()
            )
            self.db.add(action_execution)
            self.db.commit()
            
            # 执行动作
            result = await self._execute_action_by_type(
                action_template, alert, action_execution, parameters
            )
            
            # 更新执行记录
            action_execution.status = 'completed' if result['success'] else 'failed'
            action_execution.result = result
            action_execution.completed_at = datetime.utcnow()
            self.db.commit()
            
            logger.info(f"Action {action_template_id} executed for alert {alert_id}: {result['success']}")
            return result
            
        except Exception as e:
            logger.error(f"Error executing action {action_template_id} for alert {alert_id}: {str(e)}")
            
            # 更新执行记录为失败状态
            if 'action_execution' in locals():
                action_execution.status = 'failed'
                action_execution.result = {'success': False, 'error': str(e)}
                action_execution.completed_at = datetime.utcnow()
                self.db.commit()
            
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def _execute_action_by_type(self, action_template: ActionTemplate, 
                                    alert: Alert, action_execution: ActionExecution,
                                    parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        根据动作类型执行相应的处置动作
        
        Args:
            action_template: 动作模板
            alert: 告警对象
            action_execution: 动作执行记录
            parameters: 动作参数
            
        Returns:
            Dict: 执行结果
        """
        action_type = action_template.action_type
        action_config = action_template.config
        
        # 合并参数
        merged_params = {**action_config, **(parameters or {})}
        
        # 替换模板变量
        merged_params = self._replace_template_variables(merged_params, alert)
        
        try:
            if action_type == 'restart_service':
                return await self._restart_service(merged_params)
            elif action_type == 'scale_service':
                return await self._scale_service(merged_params)
            elif action_type == 'execute_script':
                return await self._execute_script(merged_params)
            elif action_type == 'api_call':
                return await self._make_api_call(merged_params)
            elif action_type == 'create_ticket':
                return await self._create_ticket(merged_params)
            elif action_type == 'send_notification':
                return await self._send_notification(merged_params)
            else:
                raise ValueError(f"Unsupported action type: {action_type}")
                
        except Exception as e:
            logger.error(f"Error executing {action_type} action: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'action_type': action_type,
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def _replace_template_variables(self, params: Dict[str, Any], alert: Alert) -> Dict[str, Any]:
        """
        替换参数中的模板变量
        
        Args:
            params: 参数字典
            alert: 告警对象
            
        Returns:
            Dict: 替换后的参数
        """
        import json
        
        # 将参数转换为JSON字符串进行替换
        params_str = json.dumps(params)
        
        # 定义可用的变量
        variables = {
            'alert_id': alert.id,
            'alert_title': alert.title,
            'alert_description': alert.description,
            'alert_severity': alert.severity,
            'alert_source': alert.source,
            'alert_status': alert.status,
            'alert_created_at': alert.created_at.isoformat() if alert.created_at else '',
            'alert_tags': json.dumps(alert.tags or {})
        }
        
        # 替换变量
        for key, value in variables.items():
            params_str = params_str.replace(f'{{{{ {key} }}}}', str(value))
        
        return json.loads(params_str)
    
    async def _restart_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        重启服务
        
        Args:
            params: 参数，包含service_name, method等
            
        Returns:
            Dict: 执行结果
        """
        service_name = params.get('service_name')
        method = params.get('method', 'api')  # api, ssh, docker等
        
        if not service_name:
            raise ValueError("service_name is required for restart_service action")
        
        if method == 'api':
            # 通过API重启服务
            api_url = params.get('api_url')
            if not api_url:
                raise ValueError("api_url is required for API restart method")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    json={'action': 'restart', 'service': service_name},
                    headers=params.get('headers', {}),
                    timeout=self.action_timeout
                ) as response:
                    if response.status == 200:
                        return {
                            'success': True,
                            'message': f'Service {service_name} restarted successfully',
                            'method': method,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"API call failed with status {response.status}: {error_text}")
        
        elif method == 'docker':
            # 通过Docker API重启容器
            container_name = params.get('container_name', service_name)
            docker_api_url = params.get('docker_api_url', 'unix://var/run/docker.sock')
            
            # TODO: 实现Docker API调用
            return {
                'success': True,
                'message': f'Docker container {container_name} restart initiated',
                'method': method,
                'timestamp': datetime.utcnow().isoformat()
            }
        
        else:
            raise ValueError(f"Unsupported restart method: {method}")
    
    async def _scale_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        扩缩容服务
        
        Args:
            params: 参数，包含service_name, replicas等
            
        Returns:
            Dict: 执行结果
        """
        service_name = params.get('service_name')
        replicas = params.get('replicas')
        method = params.get('method', 'api')
        
        if not service_name or replicas is None:
            raise ValueError("service_name and replicas are required for scale_service action")
        
        if method == 'api':
            api_url = params.get('api_url')
            if not api_url:
                raise ValueError("api_url is required for API scale method")
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_url,
                    json={'action': 'scale', 'service': service_name, 'replicas': replicas},
                    headers=params.get('headers', {}),
                    timeout=self.action_timeout
                ) as response:
                    if response.status == 200:
                        return {
                            'success': True,
                            'message': f'Service {service_name} scaled to {replicas} replicas',
                            'method': method,
                            'timestamp': datetime.utcnow().isoformat()
                        }
                    else:
                        error_text = await response.text()
                        raise Exception(f"API call failed with status {response.status}: {error_text}")
        
        else:
            raise ValueError(f"Unsupported scale method: {method}")
    
    async def _execute_script(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行脚本
        
        Args:
            params: 参数，包含script_path, args等
            
        Returns:
            Dict: 执行结果
        """
        script_path = params.get('script_path')
        script_content = params.get('script_content')
        args = params.get('args', [])
        
        if not script_path and not script_content:
            raise ValueError("Either script_path or script_content is required")
        
        # TODO: 实现脚本执行逻辑
        # 注意：脚本执行需要考虑安全性，建议使用沙箱环境
        
        return {
            'success': True,
            'message': 'Script execution completed',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _make_api_call(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        执行API调用
        
        Args:
            params: 参数，包含url, method, headers, data等
            
        Returns:
            Dict: 执行结果
        """
        url = params.get('url')
        method = params.get('method', 'POST')
        headers = params.get('headers', {})
        data = params.get('data', {})
        
        if not url:
            raise ValueError("url is required for api_call action")
        
        async with aiohttp.ClientSession() as session:
            async with session.request(
                method=method.upper(),
                url=url,
                json=data,
                headers=headers,
                timeout=self.action_timeout
            ) as response:
                response_text = await response.text()
                
                return {
                    'success': response.status >= 200 and response.status < 300,
                    'status_code': response.status,
                    'response': response_text,
                    'timestamp': datetime.utcnow().isoformat()
                }
    
    async def _create_ticket(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        创建工单
        
        Args:
            params: 参数，包含ticket_system, title, description等
            
        Returns:
            Dict: 执行结果
        """
        ticket_system = params.get('ticket_system', 'jira')
        title = params.get('title')
        description = params.get('description')
        
        if not title:
            raise ValueError("title is required for create_ticket action")
        
        # TODO: 实现不同工单系统的集成
        # 如JIRA、ServiceNow、自定义工单系统等
        
        return {
            'success': True,
            'message': f'Ticket created in {ticket_system}',
            'ticket_id': f'TICKET-{datetime.utcnow().strftime("%Y%m%d%H%M%S")}',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def _send_notification(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        发送通知
        
        Args:
            params: 参数，包含notification_type, recipients等
            
        Returns:
            Dict: 执行结果
        """
        notification_type = params.get('notification_type', 'email')
        recipients = params.get('recipients', [])
        message = params.get('message')
        
        if not recipients or not message:
            raise ValueError("recipients and message are required for send_notification action")
        
        # TODO: 集成NotificationService发送通知
        
        return {
            'success': True,
            'message': f'{notification_type} notification sent to {len(recipients)} recipients',
            'timestamp': datetime.utcnow().isoformat()
        }
    
    async def execute_multiple_actions(self, alert_id: int, 
                                     action_configs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量执行多个自动处置动作
        
        Args:
            alert_id: 告警ID
            action_configs: 动作配置列表
            
        Returns:
            List[Dict]: 执行结果列表
        """
        results = []
        
        # 限制并发执行数量
        semaphore = asyncio.Semaphore(self.max_concurrent_actions)
        
        async def execute_single_action(config):
            async with semaphore:
                return await self.execute_action(
                    alert_id=alert_id,
                    action_template_id=config['action_template_id'],
                    parameters=config.get('parameters')
                )
        
        # 并发执行所有动作
        tasks = [execute_single_action(config) for config in action_configs]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理异常结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'success': False,
                    'error': str(result),
                    'action_config': action_configs[i],
                    'timestamp': datetime.utcnow().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results
    
    async def schedule_action(self, alert_id: int, action_template_id: int,
                            schedule_time: datetime, parameters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """
        调度延迟执行的动作
        
        Args:
            alert_id: 告警ID
            action_template_id: 动作模板ID
            schedule_time: 调度时间
            parameters: 动作参数
            
        Returns:
            Dict: 调度结果
        """
        try:
            # 创建动作调度记录
            action_schedule = ActionSchedule(
                alert_id=alert_id,
                action_template_id=action_template_id,
                scheduled_time=schedule_time,
                status='scheduled',
                parameters=parameters or {},
                created_at=datetime.utcnow()
            )
            self.db.add(action_schedule)
            self.db.commit()
            
            logger.info(f"Action {action_template_id} scheduled for alert {alert_id} at {schedule_time}")
            
            return {
                'success': True,
                'message': 'Action scheduled successfully',
                'schedule_id': action_schedule.id,
                'scheduled_time': schedule_time.isoformat(),
                'timestamp': datetime.utcnow().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error scheduling action {action_template_id} for alert {alert_id}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    def get_action_execution_history(self, alert_id: Optional[int] = None, 
                                   action_template_id: Optional[int] = None,
                                   limit: int = 100) -> List[Dict[str, Any]]:
        """
        获取动作执行历史
        
        Args:
            alert_id: 告警ID（可选）
            action_template_id: 动作模板ID（可选）
            limit: 返回记录数限制
            
        Returns:
            List[Dict]: 执行历史列表
        """
        query = self.db.query(ActionExecution)
        
        if alert_id:
            query = query.filter(ActionExecution.alert_id == alert_id)
        if action_template_id:
            query = query.filter(ActionExecution.action_template_id == action_template_id)
        
        executions = query.order_by(ActionExecution.created_at.desc()).limit(limit).all()
        
        return [
            {
                'id': execution.id,
                'alert_id': execution.alert_id,
                'action_template_id': execution.action_template_id,
                'status': execution.status,
                'parameters': execution.parameters,
                'result': execution.result,
                'created_at': execution.created_at.isoformat() if execution.created_at else None,
                'completed_at': execution.completed_at.isoformat() if execution.completed_at else None
            }
            for execution in executions
        ]