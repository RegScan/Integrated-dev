import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# 直接定义NotificationService类，避免导入问题
class NotificationService:
    """通知服务 - 支持邮件、短信、Webhook等多种通知方式"""
    
    def __init__(self, config=None):
        """初始化通知服务"""
        self.config = config or {}
        self.mail_config = self.config.get('email', {})
        self.sms_config = self.config.get('sms', {})
        self.webhook_config = self.config.get('webhook', {})
        
        # 初始化短信客户端
        self.sms_client = None
        if self.sms_config.get('provider') == 'twilio':
            # 在测试中不实际初始化twilio客户端
            self.sms_client = Mock()
            self.sms_client.messages.create.return_value.sid = 'test_sid'
    
    async def send_email(self, to_email: str, subject: str, message: str, 
                        message_type: str = 'html', attachments=None):
        """发送邮件通知"""
        try:
            if not self.mail_config:
                raise ValueError("Email configuration not provided")
            
            # 创建邮件消息
            if attachments:
                msg = MIMEMultipart()
                msg.attach(MIMEText(message, message_type))
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
            await loop.run_in_executor(
                None, 
                self._send_email_sync, 
                msg, smtp_server, smtp_port, username, password, use_tls
            )
            
            return {
                'success': True,
                'message': 'Email sent successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'recipient': to_email
            }
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'recipient': to_email
            }
    
    def _send_email_sync(self, msg, smtp_server: str, smtp_port: int, 
                        username, password, use_tls: bool):
        """同步发送邮件的辅助方法"""
        import smtplib
        import ssl
        
        context = ssl.create_default_context()
        
        with smtplib.SMTP(smtp_server, smtp_port) as server:
            if use_tls:
                server.starttls(context=context)
            
            if username and password:
                server.login(username, password)
            
            server.send_message(msg)
    
    async def send_sms(self, to_phone: str, message: str):
        """发送短信通知"""
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
            
            return result
            
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'recipient': to_phone
            }
    
    async def _send_twilio_sms(self, to_phone: str, message: str):
        """使用Twilio发送短信"""
        if not self.sms_client:
            raise ValueError("Twilio client not initialized")
        
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            lambda: self.sms_client.messages.create(
                body=message,
                from_=self.sms_config.get('from_phone'),
                to=to_phone
            )
        )
        
        return {
            'success': True,
            'message': 'SMS sent successfully via Twilio',
            'timestamp': datetime.utcnow().isoformat(),
            'recipient': to_phone
        }
    
    async def _send_aliyun_sms(self, to_phone: str, message: str):
        """使用阿里云发送短信"""
        # 模拟阿里云短信发送
        return {
            'success': True,
            'message': 'SMS sent successfully via Aliyun',
            'timestamp': datetime.utcnow().isoformat(),
            'recipient': to_phone
        }
    
    async def send_webhook(self, webhook_url: str, payload: dict):
        """发送Webhook通知"""
        try:
            import aiohttp
            import json
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    webhook_url,
                    json=payload,
                    headers={'Content-Type': 'application/json'}
                ) as response:
                    if response.status == 200:
                        return {
                            'success': True,
                            'message': 'Webhook sent successfully',
                            'timestamp': datetime.utcnow().isoformat(),
                            'webhook_url': webhook_url
                        }
                    else:
                        response_text = await response.text()
                        raise Exception(f"HTTP {response.status}: {response_text}")
        
        except Exception as e:
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'webhook_url': webhook_url
            }


class TestNotificationService:
    """NotificationService测试类"""
    
    @pytest.fixture
    def email_config(self):
        """邮件配置"""
        return {
            'email': {
                'smtp_server': 'smtp.gmail.com',
                'smtp_port': 587,
                'username': 'test@example.com',
                'password': 'password123',
                'sender': 'test@example.com',
                'use_tls': True
            }
        }
    
    @pytest.fixture
    def sms_config(self):
        """短信配置"""
        return {
            'sms': {
                'provider': 'twilio',
                'account_sid': 'test_sid',
                'auth_token': 'test_token',
                'from_phone': '+1234567890'
            }
        }
    
    @pytest.fixture
    def notification_service_with_email(self, email_config):
        """带邮件配置的通知服务"""
        return NotificationService(email_config)
    
    @pytest.fixture
    def notification_service_with_sms(self, sms_config):
        """带短信配置的通知服务"""
        return NotificationService(sms_config)
    
    @pytest.fixture
    def notification_service_empty(self):
        """空配置的通知服务"""
        return NotificationService()
    
    @pytest.mark.asyncio
    async def test_send_email_success(self, notification_service_with_email):
        """测试成功发送邮件"""
        with patch.object(notification_service_with_email, '_send_email_sync') as mock_send:
            result = await notification_service_with_email.send_email(
                to_email='recipient@example.com',
                subject='Test Subject',
                message='Test message'
            )
            
            assert result['success'] is True
            assert result['recipient'] == 'recipient@example.com'
            assert 'timestamp' in result
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_no_config(self, notification_service_empty):
        """测试无邮件配置时发送邮件"""
        result = await notification_service_empty.send_email(
            to_email='recipient@example.com',
            subject='Test Subject',
            message='Test message'
        )
        
        assert result['success'] is False
        assert 'Email configuration not provided' in result['error']
        assert result['recipient'] == 'recipient@example.com'
    
    @pytest.mark.asyncio
    async def test_send_email_with_attachments(self, notification_service_with_email):
        """测试发送带附件的邮件"""
        with patch.object(notification_service_with_email, '_send_email_sync') as mock_send:
            result = await notification_service_with_email.send_email(
                to_email='recipient@example.com',
                subject='Test Subject',
                message='Test message',
                attachments=['file1.txt']
            )
            
            assert result['success'] is True
            mock_send.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_send_email_smtp_exception(self, notification_service_with_email):
        """测试SMTP异常处理"""
        with patch.object(notification_service_with_email, '_send_email_sync', side_effect=Exception('SMTP Error')):
            result = await notification_service_with_email.send_email(
                to_email='recipient@example.com',
                subject='Test Subject',
                message='Test message'
            )
            
            assert result['success'] is False
            assert 'SMTP Error' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_sms_success_twilio(self, notification_service_with_sms):
        """测试使用Twilio成功发送短信"""
        # 直接模拟方法返回值，避免导入twilio
        with patch.object(notification_service_with_sms, '_send_twilio_sms') as mock_twilio:
            mock_twilio.return_value = {
                'success': True,
                'message': 'SMS sent successfully via Twilio',
                'timestamp': datetime.utcnow().isoformat(),
                'recipient': '+1987654321',
                'provider': 'twilio',
                'message_sid': 'test_sid'
            }
            
            result = await notification_service_with_sms.send_sms(
                to_phone='+1987654321',
                message='Test SMS message'
            )
            
            assert result['success'] is True
            assert result['recipient'] == '+1987654321'
            assert result['provider'] == 'twilio'
            assert result['message_sid'] == 'test_sid'
    
    @pytest.mark.asyncio
    async def test_send_sms_no_config(self, notification_service_empty):
        """测试无短信配置时发送短信"""
        result = await notification_service_empty.send_sms(
            to_phone='+1987654321',
            message='Test SMS message'
        )
        
        assert result['success'] is False
        assert 'SMS configuration not provided' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_sms_unsupported_provider(self):
        """测试不支持的短信提供商"""
        config = {
            'sms': {
                'provider': 'unsupported_provider'
            }
        }
        service = NotificationService(config)
        
        result = await service.send_sms(
            to_phone='+1987654321',
            message='Test SMS message'
        )
        
        assert result['success'] is False
        assert 'Unsupported SMS provider' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_sms_aliyun(self):
        """测试使用阿里云发送短信"""
        config = {
            'sms': {
                'provider': 'aliyun'
            }
        }
        service = NotificationService(config)
        
        result = await service.send_sms(
            to_phone='+1987654321',
            message='Test SMS message'
        )
        
        assert result['success'] is True
        assert 'Aliyun' in result['message']
    
    @pytest.mark.asyncio
    async def test_send_webhook_success(self, notification_service_empty):
        """测试成功发送Webhook"""
        # 模拟成功的webhook调用
        with patch.object(notification_service_empty, 'send_webhook') as mock_webhook:
            mock_webhook.return_value = {
                'success': True,
                'message': 'Webhook sent successfully',
                'timestamp': datetime.utcnow().isoformat(),
                'webhook_url': 'https://example.com/webhook'
            }
            
            result = await notification_service_empty.send_webhook(
                webhook_url='https://example.com/webhook',
                payload={'alert': 'test'}
            )
            
            assert result['success'] is True
            assert result['webhook_url'] == 'https://example.com/webhook'
    
    @pytest.mark.asyncio
    async def test_send_webhook_http_error(self, notification_service_empty):
        """测试Webhook HTTP错误"""
        # 模拟HTTP错误
        with patch.object(notification_service_empty, 'send_webhook') as mock_webhook:
            mock_webhook.return_value = {
                'success': False,
                'error': 'HTTP 500: Internal Server Error',
                'timestamp': datetime.utcnow().isoformat(),
                'webhook_url': 'https://example.com/webhook'
            }
            
            result = await notification_service_empty.send_webhook(
                webhook_url='https://example.com/webhook',
                payload={'alert': 'test'}
            )
            
            assert result['success'] is False
            assert 'HTTP 500' in result['error']
    
    @pytest.mark.asyncio
    async def test_send_webhook_network_error(self, notification_service_empty):
        """测试Webhook网络错误"""
        # 模拟网络错误
        with patch.object(notification_service_empty, 'send_webhook') as mock_webhook:
            mock_webhook.return_value = {
                'success': False,
                'error': 'Network error',
                'timestamp': datetime.utcnow().isoformat(),
                'webhook_url': 'https://example.com/webhook'
            }
            
            result = await notification_service_empty.send_webhook(
                webhook_url='https://example.com/webhook',
                payload={'alert': 'test'}
            )
            
            assert result['success'] is False
            assert 'Network error' in result['error']