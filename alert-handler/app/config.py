"""告警处理模块配置文件"""

import os
from typing import Dict, Any, Optional
from pydantic import BaseSettings, Field

class Settings(BaseSettings):
    """应用配置类"""
    
    # 应用基础配置
    app_name: str = Field(default="Alert Handler", description="应用名称")
    app_version: str = Field(default="1.0.0", description="应用版本")
    debug: bool = Field(default=False, description="调试模式")
    
    # 服务器配置
    host: str = Field(default="0.0.0.0", description="服务器主机")
    port: int = Field(default=8002, description="服务器端口")
    
    # 数据库配置
    database_url: str = Field(
        default="sqlite:///./alert_handler.db",
        description="数据库连接URL"
    )
    
    # Redis配置（用于Celery）
    redis_url: str = Field(
        default="redis://localhost:6379/0",
        description="Redis连接URL"
    )
    
    # 邮件配置
    smtp_server: str = Field(default="smtp.gmail.com", description="SMTP服务器")
    smtp_port: int = Field(default=587, description="SMTP端口")
    smtp_username: str = Field(default="", description="SMTP用户名")
    smtp_password: str = Field(default="", description="SMTP密码")
    smtp_use_tls: bool = Field(default=True, description="是否使用TLS")
    
    # 短信配置
    sms_provider: str = Field(default="twilio", description="短信服务提供商")
    twilio_account_sid: str = Field(default="", description="Twilio账户SID")
    twilio_auth_token: str = Field(default="", description="Twilio认证令牌")
    twilio_phone_number: str = Field(default="", description="Twilio电话号码")
    
    # 阿里云短信配置
    aliyun_access_key_id: str = Field(default="", description="阿里云AccessKey ID")
    aliyun_access_key_secret: str = Field(default="", description="阿里云AccessKey Secret")
    aliyun_sms_sign_name: str = Field(default="", description="阿里云短信签名")
    aliyun_sms_template_code: str = Field(default="", description="阿里云短信模板代码")
    
    # Slack配置
    slack_webhook_url: str = Field(default="", description="Slack Webhook URL")
    slack_bot_token: str = Field(default="", description="Slack Bot Token")
    
    # 钉钉配置
    dingtalk_webhook_url: str = Field(default="", description="钉钉Webhook URL")
    dingtalk_secret: str = Field(default="", description="钉钉密钥")
    
    # 企业微信配置
    wechat_webhook_url: str = Field(default="", description="企业微信Webhook URL")
    
    # JIRA配置
    jira_base_url: str = Field(default="", description="JIRA基础URL")
    jira_username: str = Field(default="", description="JIRA用户名")
    jira_api_token: str = Field(default="", description="JIRA API令牌")
    jira_project_key: str = Field(default="", description="JIRA项目键")
    
    # ServiceNow配置
    servicenow_instance_url: str = Field(default="", description="ServiceNow实例URL")
    servicenow_username: str = Field(default="", description="ServiceNow用户名")
    servicenow_password: str = Field(default="", description="ServiceNow密码")
    
    # 日志配置
    log_level: str = Field(default="INFO", description="日志级别")
    log_file: str = Field(default="alert_handler.log", description="日志文件")
    
    # 安全配置
    secret_key: str = Field(
        default="your-secret-key-here",
        description="应用密钥"
    )
    
    # 告警处理配置
    max_retry_attempts: int = Field(default=3, description="最大重试次数")
    retry_delay: int = Field(default=60, description="重试延迟（秒）")
    alert_timeout: int = Field(default=300, description="告警处理超时时间（秒）")
    
    # 自动处置配置
    auto_action_enabled: bool = Field(default=True, description="是否启用自动处置")
    auto_action_timeout: int = Field(default=600, description="自动处置超时时间（秒）")
    
    # 通知配置
    notification_timeout: int = Field(default=30, description="通知发送超时时间（秒）")
    max_notification_retries: int = Field(default=3, description="通知最大重试次数")
    
    # 数据清理配置
    data_retention_days: int = Field(default=30, description="数据保留天数")
    cleanup_enabled: bool = Field(default=True, description="是否启用数据清理")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# 创建设置实例
settings = Settings()

def get_notification_config() -> Dict[str, Any]:
    """获取通知服务配置"""
    return {
        'email': {
            'smtp_server': settings.smtp_server,
            'smtp_port': settings.smtp_port,
            'username': settings.smtp_username,
            'password': settings.smtp_password,
            'use_tls': settings.smtp_use_tls,
            'timeout': settings.notification_timeout
        },
        'sms': {
            'provider': settings.sms_provider,
            'twilio': {
                'account_sid': settings.twilio_account_sid,
                'auth_token': settings.twilio_auth_token,
                'phone_number': settings.twilio_phone_number
            },
            'aliyun': {
                'access_key_id': settings.aliyun_access_key_id,
                'access_key_secret': settings.aliyun_access_key_secret,
                'sign_name': settings.aliyun_sms_sign_name,
                'template_code': settings.aliyun_sms_template_code
            },
            'timeout': settings.notification_timeout
        },
        'slack': {
            'webhook_url': settings.slack_webhook_url,
            'bot_token': settings.slack_bot_token,
            'timeout': settings.notification_timeout
        },
        'dingtalk': {
            'webhook_url': settings.dingtalk_webhook_url,
            'secret': settings.dingtalk_secret,
            'timeout': settings.notification_timeout
        },
        'wechat': {
            'webhook_url': settings.wechat_webhook_url,
            'timeout': settings.notification_timeout
        }
    }

def get_ticket_system_config() -> Dict[str, Any]:
    """获取工单系统配置"""
    return {
        'default_system': 'jira',
        'timeout': 30,
        'jira': {
            'base_url': settings.jira_base_url,
            'username': settings.jira_username,
            'api_token': settings.jira_api_token,
            'project_key': settings.jira_project_key,
            'issue_type': 'Bug'
        },
        'servicenow': {
            'instance_url': settings.servicenow_instance_url,
            'username': settings.servicenow_username,
            'password': settings.servicenow_password,
            'table': 'incident'
        },
        'custom': {
            'api_url': '',
            'api_key': '',
            'headers': {}
        }
    }

def get_auto_action_config() -> Dict[str, Any]:
    """获取自动处置配置"""
    return {
        'enabled': settings.auto_action_enabled,
        'timeout': settings.auto_action_timeout,
        'max_retries': settings.max_retry_attempts,
        'retry_delay': settings.retry_delay
    }

def get_celery_config() -> Dict[str, Any]:
    """获取Celery配置"""
    return {
        'broker_url': settings.redis_url,
        'result_backend': settings.redis_url,
        'task_serializer': 'json',
        'accept_content': ['json'],
        'result_serializer': 'json',
        'timezone': 'UTC',
        'enable_utc': True,
        'task_routes': {
            'alert_handler.tasks.*': {'queue': 'alerts'}
        },
        'beat_schedule': {
            'cleanup-old-alerts': {
                'task': 'alert_handler.tasks.alert_tasks.cleanup_old_alerts_task',
                'schedule': 86400.0,  # 每天执行一次
            },
            'health-check': {
                'task': 'alert_handler.tasks.alert_tasks.health_check_task',
                'schedule': 300.0,  # 每5分钟执行一次
            },
        }
    }

def get_database_config() -> Dict[str, Any]:
    """获取数据库配置"""
    return {
        'url': settings.database_url,
        'pool_size': 20,
        'max_overflow': 30,
        'pool_pre_ping': True,
        'pool_recycle': 3600,
        'echo': settings.debug
    }

def get_logging_config() -> Dict[str, Any]:
    """获取日志配置"""
    return {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            },
            'detailed': {
                'format': '%(asctime)s - %(name)s - %(levelname)s - %(filename)s:%(lineno)d - %(funcName)s - %(message)s',
                'datefmt': '%Y-%m-%d %H:%M:%S'
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': settings.log_level,
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.handlers.RotatingFileHandler',
                'level': settings.log_level,
                'formatter': 'detailed',
                'filename': settings.log_file,
                'maxBytes': 10485760,  # 10MB
                'backupCount': 5
            }
        },
        'loggers': {
            'alert_handler': {
                'level': settings.log_level,
                'handlers': ['console', 'file'],
                'propagate': False
            },
            'uvicorn': {
                'level': 'INFO',
                'handlers': ['console'],
                'propagate': False
            },
            'sqlalchemy': {
                'level': 'WARNING',
                'handlers': ['console', 'file'],
                'propagate': False
            }
        },
        'root': {
            'level': settings.log_level,
            'handlers': ['console', 'file']
        }
    }