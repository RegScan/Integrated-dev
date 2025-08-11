import pytest
import asyncio
from unittest.mock import Mock, patch
import os
from datetime import datetime

# 设置测试环境变量
os.environ['TESTING'] = 'true'
os.environ['DATABASE_URL'] = 'sqlite:///:memory:'
os.environ['REDIS_URL'] = 'redis://localhost:6379/1'

@pytest.fixture
def test_settings():
    """测试设置"""
    return {
        'database_url': 'sqlite:///:memory:',
        'redis_url': 'redis://localhost:6379/1',
        'debug': True,
        'testing': True
    }

@pytest.fixture
def sample_alert_data():
    """示例告警数据"""
    return {
        'id': 'alert-001',
        'title': 'High CPU Usage',
        'description': 'CPU usage exceeded 90% for 5 minutes',
        'severity': 'critical',
        'source': 'monitoring-system',
        'timestamp': datetime.utcnow().isoformat(),
        'tags': ['cpu', 'performance'],
        'metadata': {
            'host': 'web-server-01',
            'cpu_usage': 95.5,
            'threshold': 90.0
        }
    }

@pytest.fixture
def sample_notification_config():
    """示例通知配置"""
    return {
        'email': {
            'smtp_server': 'smtp.example.com',
            'smtp_port': 587,
            'username': 'alerts@example.com',
            'password': 'password123',
            'sender': 'alerts@example.com',
            'use_tls': True
        },
        'sms': {
            'provider': 'twilio',
            'account_sid': 'test_account_sid',
            'auth_token': 'test_auth_token',
            'from_phone': '+1234567890'
        },
        'webhook': {
            'url': 'https://example.com/webhook',
            'timeout': 30,
            'retry_count': 3
        }
    }

@pytest.fixture
def sample_ticket_data():
    """示例工单数据"""
    return {
        'title': 'Critical Alert: High CPU Usage',
        'description': 'Automated ticket created for critical alert',
        'priority': 'High',
        'assignee': 'ops-team',
        'labels': ['alert', 'cpu', 'critical'],
        'alert_id': 'alert-001'
    }

@pytest.fixture
def mock_smtp_server():
    """模拟SMTP服务器"""
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = Mock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        yield mock_server

@pytest.fixture
def mock_twilio_client():
    """模拟Twilio客户端"""
    # 创建一个简单的Mock对象，避免导入twilio
    mock_instance = Mock()
    mock_instance.messages.create.return_value.sid = 'test_message_sid'
    yield mock_instance

@pytest.fixture
def mock_aiohttp_session():
    """模拟aiohttp会话"""
    with patch('aiohttp.ClientSession') as mock_session:
        yield mock_session

@pytest.fixture
def mock_jira_client():
    """模拟JIRA客户端"""
    with patch('jira.JIRA') as mock_jira:
        mock_instance = Mock()
        mock_jira.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_redis_client():
    """模拟Redis客户端"""
    with patch('redis.Redis') as mock_redis:
        mock_instance = Mock()
        mock_redis.return_value = mock_instance
        yield mock_instance

@pytest.fixture
def mock_celery_task():
    """模拟Celery任务"""
    with patch('celery.Celery') as mock_celery:
        mock_instance = Mock()
        mock_celery.return_value = mock_instance
        yield mock_instance

# 自定义pytest标记
pytest_main_markers = [
    "unit: 单元测试",
    "integration: 集成测试",
    "notification: 通知相关测试",
    "alert: 告警处理测试",
    "ticket: 工单系统测试",
    "slow: 慢速测试",
    "external: 需要外部服务的测试"
]

# 配置asyncio事件循环
@pytest.fixture(scope="session")
def event_loop():
    """创建事件循环用于异步测试"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()

# 测试数据清理
@pytest.fixture(autouse=True)
def cleanup_test_data():
    """自动清理测试数据"""
    yield
    # 测试后清理逻辑
    pass