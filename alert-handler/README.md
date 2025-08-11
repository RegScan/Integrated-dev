# 智能告警处理系统 (Alert Handler)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.104+-green.svg)](https://fastapi.tiangolo.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 📋 项目简介

智能告警处理系统是一个现代化的告警管理平台，专为企业级环境设计。系统能够接收、处理、分析各种告警事件，并通过多种渠道进行智能通知和自动化处置。

### 🎯 核心特性

- **🔄 智能告警处理**: 自动接收、分析和处理各类告警事件
- **📢 多渠道通知**: 支持邮件、短信、Slack、钉钉、企业微信等多种通知方式
- **🤖 自动化处置**: 支持自动重启服务、扩缩容、执行脚本等自动化操作
- **🎫 工单集成**: 集成JIRA、ServiceNow等工单系统
- **📊 实时监控**: 提供告警处理状态的实时监控和统计
- **🔧 规则引擎**: 灵活的告警规则配置和匹配机制
- **📈 可扩展架构**: 基于微服务架构，支持水平扩展

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   告警源系统     │───▶│   告警处理API    │───▶│   通知服务       │
│  (监控系统等)    │    │   (FastAPI)     │    │ (邮件/短信/IM)   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   工单系统      │◀───│   规则引擎       │───▶│   自动化处置     │
│ (JIRA/ServiceNow)│    │  (告警分析)      │    │  (脚本/API)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                              │
                              ▼
                    ┌─────────────────┐
                    │   数据存储       │
                    │ (PostgreSQL)    │
                    └─────────────────┘
```

## 🚀 技术栈

### 后端技术
- **Web框架**: FastAPI 0.104+
- **异步任务**: Celery + Redis
- **数据库**: PostgreSQL / MySQL / SQLite
- **ORM**: SQLAlchemy 2.0
- **模板引擎**: Jinja2
- **HTTP客户端**: aiohttp, requests

### 通知服务
- **邮件**: SMTP
- **短信**: Twilio, 阿里云短信
- **即时通讯**: Slack, 钉钉, 企业微信

### 工单系统
- **JIRA**: Atlassian JIRA Cloud/Server
- **ServiceNow**: ServiceNow Platform

### 部署运维
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **监控**: Celery Flower
- **日志**: Loguru

## 📁 目录结构

```
alert-handler/
├── app/                    # 应用核心代码
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库配置
│   ├── api/               # API路由
│   │   ├── __init__.py
│   │   ├── alerts.py      # 告警API
│   │   └── actions.py     # 处置动作API
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── alert.py       # 告警模型
│   │   ├── action.py      # 处置动作模型
│   │   └── notification.py # 通知模型
│   ├── services/          # 业务服务
│   │   ├── __init__.py
│   │   ├── alert_processor.py    # 告警处理服务
│   │   ├── notification.py       # 通知服务
│   │   ├── auto_action.py        # 自动处置服务
│   │   └── ticket_system.py      # 工单系统服务
│   └── tasks/             # 异步任务
│       ├── __init__.py
│       └── alert_tasks.py # 告警相关任务
├── templates/             # 通知模板
│   ├── email/
│   ├── sms/
│   └── webhook/
├── tests/                 # 测试代码
├── docker-compose.yml     # Docker编排
├── Dockerfile            # Docker镜像
├── nginx.conf            # Nginx配置
├── requirements.txt      # Python依赖
├── .env.example         # 环境变量模板
└── README.md            # 项目文档
```

## 🛠️ 快速开始

### 环境要求

- Python 3.11+
- Docker & Docker Compose
- PostgreSQL 15+ (可选，默认使用SQLite)
- Redis 7+ (用于Celery)

### 1. 克隆项目

```bash
git clone <repository-url>
cd alert-handler
```

### 2. 环境配置

```bash
# 复制环境变量模板
cp .env.example .env

# 编辑配置文件
vim .env
```

### 3. 使用Docker Compose启动

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f alert-handler
```

### 4. 本地开发环境

```bash
# 安装依赖
pip install -r requirements.txt

# 启动Redis (用于Celery)
docker run -d -p 6379:6379 redis:7-alpine

# 启动Celery Worker
celery -A app.tasks.alert_tasks worker --loglevel=info

# 启动Celery Beat (另一个终端)
celery -A app.tasks.alert_tasks beat --loglevel=info

# 启动API服务
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## 📚 API 文档

启动服务后，访问以下地址查看API文档：

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **Celery Flower**: http://localhost:5555 (监控异步任务)

### 核心API端点

#### 告警管理

```http
# 创建告警
POST /api/v1/alerts
Content-Type: application/json

{
  "source": "monitoring-system",
  "severity": "critical",
  "title": "服务器CPU使用率过高",
  "description": "服务器CPU使用率达到95%",
  "tags": ["cpu", "performance"],
  "metadata": {
    "server": "web-01",
    "cpu_usage": 95.2
  }
}
```

```http
# 获取告警列表
GET /api/v1/alerts?status=active&severity=critical
```

```http
# 更新告警状态
PUT /api/v1/alerts/{alert_id}/status
Content-Type: application/json

{
  "status": "resolved",
  "resolution_note": "问题已修复"
}
```

#### 自动处置

```http
# 执行自动处置动作
POST /api/v1/actions/execute
Content-Type: application/json

{
  "alert_id": "alert-123",
  "action_type": "restart_service",
  "parameters": {
    "service_name": "nginx",
    "server": "web-01"
  }
}
```

## ⚙️ 配置说明

### 数据库配置

```env
# SQLite (默认)
DATABASE_URL=sqlite:///./alert_handler.db

# PostgreSQL
DATABASE_URL=postgresql://user:password@localhost:5432/alert_handler

# MySQL
DATABASE_URL=mysql+pymysql://user:password@localhost:3306/alert_handler
```

### 通知服务配置

```env
# 邮件配置
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password

# Slack配置
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token

# 钉钉配置
DINGTALK_WEBHOOK_URL=https://oapi.dingtalk.com/robot/send?access_token=YOUR_TOKEN
```

## 🔧 开发指南

### 添加新的通知渠道

1. 在 `app/services/notification.py` 中添加新的通知方法
2. 在 `templates/` 目录下创建对应的模板文件
3. 更新配置文件添加相关配置项
4. 编写单元测试

### 添加新的自动处置动作

1. 在 `app/services/auto_action.py` 中添加新的动作方法
2. 更新 `ActionType` 枚举
3. 添加相应的参数验证
4. 编写单元测试

### 代码规范

```bash
# 代码格式化
black app/ tests/

# 代码检查
flake8 app/ tests/

# 类型检查
mypy app/

# 运行测试
pytest tests/ -v
```

## 📊 监控和运维

### 健康检查

```bash
# API健康检查
curl http://localhost:8000/health

# 数据库连接检查
curl http://localhost:8000/health/db

# Redis连接检查
curl http://localhost:8000/health/redis
```

### 日志管理

```bash
# 查看应用日志
docker-compose logs -f alert-handler

# 查看Celery日志
docker-compose logs -f celery-worker

# 查看Nginx日志
docker-compose logs -f nginx
```

### 性能监控

- **Celery Flower**: http://localhost:5555 - 监控异步任务执行情况
- **API Metrics**: http://localhost:8000/metrics - Prometheus格式的指标

## 🤝 贡献指南

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开 Pull Request

## 📄 许可证

本项目采用 MIT 许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 🆘 支持

如果您遇到问题或有疑问，请：

1. 查看 [FAQ](docs/FAQ.md)
2. 搜索 [Issues](../../issues)
3. 创建新的 [Issue](../../issues/new)

## 🗺️ 路线图

- [ ] 支持更多通知渠道 (Teams, Telegram)
- [ ] 告警聚合和去重功能
- [ ] 可视化告警仪表板
- [ ] 机器学习驱动的智能告警分析
- [ ] 多租户支持
- [ ] 告警模板市场