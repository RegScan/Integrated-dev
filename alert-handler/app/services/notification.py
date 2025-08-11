import smtplib
import ssl
import aiohttp
import asyncio
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from typing import Dict, List, Optional, Any
import logging
import json
from datetime import datetime

logger = logging.getLogger(__name__)

class NotificationService:
    """通知服务 - 支持邮件、短信、Webhook等多种通知方式"""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化通知服务
        
        Args:
            config: 通知配置，包含各种通知渠道的配置信息
        """
        self.config = config or {}
        self.mail_config = self.config.get('email', {})
        self.sms_config = self.config.get('sms', {})
        self.webhook_config = self.config.get('webhook', {})
        
        # 初始化短信客户端（如果配置了）
        self.sms_client = None
        if self.sms_config.get('provider') == 'twilio':
            try:
                from twilio.rest import Client
                self.sms_client = Client(
                    self.sms_config.get('account_sid'),
                    self.sms_config.get('auth_token')
                )
            except ImportError:
                logger.warning("Twilio library not installed, SMS notifications will be disabled")
            except Exception as e:
                logger.error(f"Error initializing Twilio client: {str(e)}")
    
    async def send_email(self, to_email: str, subject: str, message: str, 
                        message_type: str = 'html', attachments: Optional[List] = None) -> Dict[str, Any]:
        """
        发送邮件通知
        
        Args:
            to_email: 收件人邮箱
            subject: 邮件主题
            message: 邮件内容
            message_type: 邮件类型 ('html' 或 'plain')
            attachments: 附件列表
            
        Returns:
            Dict: 发送结果
        """
        try:
            if not self.mail_config:
                raise ValueError("Email configuration not provided")
            
            # 创建邮件消息
            if attachments:
                msg = MIMEMultipart()
                msg.attach(MIMEText(message, message_type))
                # TODO: 处理附件
            else:
                msg = MIMEText(message, message_type)
            
            msg['Subject'] = subject
            msg['From'] = self.mail_config.get('sender', 'noreply@example.com')
            msg['To'] = to_email
            
            # 发送邮件
            smtp_server = self.mail_config.get('smtp_server', 'localhost')
            smtp_port = self.mail_config.get('smtp_port', 587)
            username = self.mail_config.get('username')
            password = self.mail_config.get('password')
            use_tls = self.mail_config.get('use_tls', True)
            
            # 使用异步方式发送邮件
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None, 
                self._send_email_sync, 
                msg, smtp_server, smtp_port, username, password, use_tls
            )
            
            logger.info(f"Email sent successfully to {to_email}")
            return {
                'success': True,
                'message': 'Email sent successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'recipient': to_email
            }
            
        except Exception as e:
            logger.error(f"Error sending email to {to_email}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'recipient': to_email
            }
    
    def _send_email_sync(self, msg, smtp_server: str, smtp_port: int, 
                        username: Optional[str], password: Optional[str], use_tls: bool):
        """
        同步发送邮件的辅助方法
        """
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls(context=context)
            
            if username and password:
                server.login(username, password)
            
            server.send_message(msg)
    
    async def send_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        发送短信通知
        
        Args:
            to_phone: 收件人手机号
            message: 短信内容
            
        Returns:
            Dict: 发送结果
        """
        try:
            if not self.sms_config:
                raise ValueError("SMS configuration not provided")
            
            provider = self.sms_config.get('provider', 'twilio')
            
            if provider == 'twilio':
                result = await self._send_twilio_sms(to_phone, message)
            elif provider == 'aliyun':
                result = await self._send_aliyun_sms(to_phone, message)
            else:
                raise ValueError(f"Unsupported SMS provider: {provider}")
            
            logger.info(f"SMS sent successfully to {to_phone}")
            return result
            
        except Exception as e:
            logger.error(f"Error sending SMS to {to_phone}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'recipient': to_phone
            }
    
    async def _send_twilio_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        使用Twilio发送短信
        """
        if not self.sms_client:
            raise ValueError("Twilio client not initialized")
        
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            self._send_twilio_sms_sync,
            to_phone, message
        )
        
        return {
            'success': True,
            'message': 'SMS sent successfully via Twilio',
            'timestamp': datetime.utcnow().isoformat(),
            'recipient': to_phone,
            'provider': 'twilio',
            'message_sid': result.sid if hasattr(result, 'sid') else None
        }
    
    def _send_twilio_sms_sync(self, to_phone: str, message: str):
        """
        同步发送Twilio短信的辅助方法
        """
        return self.sms_client.messages.create(
            body=message,
            from_=self.sms_config.get('from_phone'),
            to=to_phone
        )
    
    async def _send_aliyun_sms(self, to_phone: str, message: str) -> Dict[str, Any]:
        """
        使用阿里云发送短信
        """
        # TODO: 实现阿里云短信发送
        raise NotImplementedError("Aliyun SMS provider not implemented yet")
    
    async def send_webhook(self, url: str, data: Dict[str, Any], 
                          method: str = 'POST', headers: Optional[Dict[str, str]] = None,
                          timeout: int = 30) -> Dict[str, Any]:
        """
        发送Webhook通知
        
        Args:
            url: Webhook URL
            data: 要发送的数据
            method: HTTP方法
            headers: 请求头
            timeout: 超时时间（秒）
            
        Returns:
            Dict: 发送结果
        """
        try:
            # 默认请求头
            default_headers = {
                'Content-Type': 'application/json',
                'User-Agent': 'AlertHandler/1.0'
            }
            
            if headers:
                default_headers.update(headers)
            
            # 添加Webhook配置中的认证信息
            if self.webhook_config.get('auth_token'):
                default_headers['Authorization'] = f"Bearer {self.webhook_config['auth_token']}"
            
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=timeout)) as session:
                async with session.request(
                    method=method.upper(),
                    url=url,
                    json=data,
                    headers=default_headers
                ) as response:
                    response_text = await response.text()
                    
                    if response.status >= 200 and response.status < 300:
                        logger.info(f"Webhook sent successfully to {url}")
                        return {
                            'success': True,
                            'message': 'Webhook sent successfully',
                            'timestamp': datetime.utcnow().isoformat(),
                            'url': url,
                            'status_code': response.status,
                            'response': response_text
                        }
                    else:
                        logger.warning(f"Webhook failed with status {response.status}: {response_text}")
                        return {
                            'success': False,
                            'error': f"HTTP {response.status}: {response_text}",
                            'timestamp': datetime.utcnow().isoformat(),
                            'url': url,
                            'status_code': response.status
                        }
                        
        except asyncio.TimeoutError:
            logger.error(f"Webhook timeout for {url}")
            return {
                'success': False,
                'error': 'Request timeout',
                'timestamp': datetime.utcnow().isoformat(),
                'url': url
            }
        except Exception as e:
            logger.error(f"Error sending webhook to {url}: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'url': url
            }
    
    async def send_slack(self, webhook_url: str, message: str, 
                        channel: Optional[str] = None, username: Optional[str] = None) -> Dict[str, Any]:
        """
        发送Slack通知
        
        Args:
            webhook_url: Slack Webhook URL
            message: 消息内容
            channel: 频道名称
            username: 用户名
            
        Returns:
            Dict: 发送结果
        """
        try:
            payload = {
                'text': message
            }
            
            if channel:
                payload['channel'] = channel
            if username:
                payload['username'] = username
            
            return await self.send_webhook(webhook_url, payload)
            
        except Exception as e:
            logger.error(f"Error sending Slack notification: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def send_dingtalk(self, webhook_url: str, message: str, 
                           at_mobiles: Optional[List[str]] = None, 
                           at_all: bool = False) -> Dict[str, Any]:
        """
        发送钉钉通知
        
        Args:
            webhook_url: 钉钉Webhook URL
            message: 消息内容
            at_mobiles: @的手机号列表
            at_all: 是否@所有人
            
        Returns:
            Dict: 发送结果
        """
        try:
            payload = {
                'msgtype': 'text',
                'text': {
                    'content': message
                },
                'at': {
                    'atMobiles': at_mobiles or [],
                    'isAtAll': at_all
                }
            }
            
            return await self.send_webhook(webhook_url, payload)
            
        except Exception as e:
            logger.error(f"Error sending DingTalk notification: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def send_wechat_work(self, webhook_url: str, message: str, 
                              mentioned_list: Optional[List[str]] = None,
                              mentioned_mobile_list: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        发送企业微信通知
        
        Args:
            webhook_url: 企业微信Webhook URL
            message: 消息内容
            mentioned_list: @的用户ID列表
            mentioned_mobile_list: @的手机号列表
            
        Returns:
            Dict: 发送结果
        """
        try:
            payload = {
                'msgtype': 'text',
                'text': {
                    'content': message,
                    'mentioned_list': mentioned_list or [],
                    'mentioned_mobile_list': mentioned_mobile_list or []
                }
            }
            
            return await self.send_webhook(webhook_url, payload)
            
        except Exception as e:
            logger.error(f"Error sending WeChat Work notification: {str(e)}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }
    
    async def send_multiple(self, notifications: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        批量发送多种类型的通知
        
        Args:
            notifications: 通知列表，每个元素包含type和相应的参数
            
        Returns:
            List[Dict]: 发送结果列表
        """
        results = []
        
        for notification in notifications:
            try:
                notification_type = notification.get('type')
                
                if notification_type == 'email':
                    result = await self.send_email(**notification.get('params', {}))
                elif notification_type == 'sms':
                    result = await self.send_sms(**notification.get('params', {}))
                elif notification_type == 'webhook':
                    result = await self.send_webhook(**notification.get('params', {}))
                elif notification_type == 'slack':
                    result = await self.send_slack(**notification.get('params', {}))
                elif notification_type == 'dingtalk':
                    result = await self.send_dingtalk(**notification.get('params', {}))
                elif notification_type == 'wechat_work':
                    result = await self.send_wechat_work(**notification.get('params', {}))
                else:
                    result = {
                        'success': False,
                        'error': f"Unsupported notification type: {notification_type}",
                        'timestamp': datetime.utcnow().isoformat()
                    }
                
                result['type'] = notification_type
                results.append(result)
                
            except Exception as e:
                logger.error(f"Error sending notification {notification}: {str(e)}")
                results.append({
                    'success': False,
                    'error': str(e),
                    'type': notification.get('type', 'unknown'),
                    'timestamp': datetime.utcnow().isoformat()
                })
        
        return results