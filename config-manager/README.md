# 配置管理模块 (config-manager)

**功能职责：**

本模块是整个系统的中央配置中心。它负责存储、管理和提供所有其他服务所需的配置信息，实现了配置与代码的分离。其他服务（如`website-scanner`, `alert-handler`）通过API从本模块获取其所需的配置。

## 🎯 核心特性

- **🔧 统一配置管理**: 集中管理所有服务的配置信息
- **🔐 安全加密**: 支持敏感配置的加密存储
- **📊 版本控制**: 完整的配置变更历史和版本管理
- **👥 用户权限**: 基于角色的访问控制和权限管理
- **📈 统计分析**: 配置使用情况和访问统计
- **🔄 导入导出**: 支持配置的批量导入和导出
- **🌍 多环境支持**: 开发、测试、生产环境配置分离
- **📝 审计日志**: 完整的配置访问和变更日志

## 🏗️ 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   配置管理API    │───▶│   数据库存储     │───▶│   配置分发       │
│   (FastAPI)     │    │  (PostgreSQL)   │    │  (Redis缓存)    │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         ▼                       ▼                       ▼
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   用户认证       │    │   版本控制       │    │   加密存储       │
│  (JWT)          │    │  (历史记录)      │    │  (Fernet)       │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🚀 技术栈

### 后端技术
- **Web框架**: FastAPI 0.104+
- **数据库**: PostgreSQL / SQLite
- **ORM**: SQLAlchemy 2.0
- **数据验证**: Pydantic 2.5+
- **认证**: JWT (python-jose)
- **加密**: Fernet (cryptography)

### 配置管理
- **配置文件**: YAML格式
- **环境变量**: python-dotenv
- **缓存**: Redis
- **日志**: Loguru

### 部署运维
- **容器化**: Docker + Docker Compose
- **反向代理**: Nginx
- **进程管理**: Gunicorn
- **健康检查**: 内置健康检查接口

## 📁 目录结构

```
config-manager/
├── app/                    # 应用核心代码
│   ├── __init__.py
│   ├── main.py            # FastAPI应用入口
│   ├── config.py          # 配置管理
│   ├── database.py        # 数据库配置
│   ├── api/               # API路由
│   │   ├── __init__.py
│   │   ├── config.py      # 配置API
│   │   ├── auth.py        # 认证API
│   │   └── users.py       # 用户API
│   ├── models/            # 数据模型
│   │   ├── __init__.py
│   │   ├── config.py      # 配置模型
│   │   └── user.py        # 用户模型
│   ├── schemas/           # Pydantic模型
│   │   ├── __init__.py
│   │   ├── config_schema.py # 配置Schema
│   │   └── user_schema.py   # 用户Schema
│   └── services/          # 业务服务
│       ├── __init__.py
│       ├── config_service.py # 配置服务
│       └── user_service.py   # 用户服务
├── configs/               # 配置文件
│   ├── default.yaml       # 默认配置
│   ├── development.yaml   # 开发环境配置
│   └── production.yaml    # 生产环境配置
├── data/                  # 数据目录
├── logs/                  # 日志目录
├── tests/                 # 测试代码
├── docker-compose.yml     # Docker编排
├── Dockerfile            # Docker镜像
└── requirements.txt      # Python依赖
```

## 🔧 快速开始

### 1. 环境准备

```bash
# 克隆项目
git clone <repository-url>
cd config-manager

# 创建虚拟环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 或
venv\Scripts\activate  # Windows

# 安装依赖
pip install -r requirements.txt
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑环境变量
vim .env
```

### 3. 启动服务

#### 使用Docker Compose（推荐）

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f config-manager
```

#### 本地开发

```bash
# 启动开发服务器
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### 4. 访问服务

- **API文档**: http://localhost:8000/docs
- **健康检查**: http://localhost:8000/health
- **系统信息**: http://localhost:8000/info

## 📚 API使用指南

### 配置管理API

#### 获取配置列表
```bash
curl -X GET "http://localhost:8000/api/v1/config/" \
  -H "Authorization: Bearer <token>"
```

#### 创建配置
```bash
curl -X POST "http://localhost:8000/api/v1/config/" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "key": "database.host",
    "value": "localhost",
    "description": "数据库主机地址",
    "category": "database",
    "environment": "development",
    "is_encrypted": false,
    "is_sensitive": false
  }'
```

#### 更新配置
```bash
curl -X PUT "http://localhost:8000/api/v1/config/1" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{
    "value": "new-value",
    "description": "更新的描述"
  }'
```

### 用户认证API

#### 用户登录
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "password123"
  }'
```

#### 用户注册
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "newuser",
    "email": "user@example.com",
    "password": "password123",
    "full_name": "New User"
  }'
```

## 🔐 安全特性

### 配置加密
- 支持敏感配置的自动加密存储
- 使用Fernet对称加密算法
- 密钥通过环境变量管理

### 用户认证
- JWT令牌认证
- 密码哈希存储（bcrypt）
- 令牌过期机制

### 权限控制
- 基于角色的访问控制
- 细粒度的资源权限管理
- 操作审计日志

## 📊 监控和日志

### 健康检查
```bash
curl http://localhost:8000/health
```

### 系统统计
```bash
curl http://localhost:8000/api/v1/config/stats/overview
```

### 日志查看
```bash
# 查看应用日志
tail -f logs/config-manager.log

# 查看Docker日志
docker-compose logs -f config-manager
```

## 🧪 测试

### 运行测试
```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_config_service.py

# 生成覆盖率报告
pytest --cov=app tests/
```

### 测试数据
```bash
# 创建测试用户
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "username": "testuser",
    "email": "test@example.com",
    "password": "TestPass123",
    "full_name": "Test User"
  }'
```

## 🚀 部署

### 生产环境部署

1. **环境变量配置**
```bash
# 生产环境变量
export ENVIRONMENT=production
export SECRET_KEY=your-production-secret-key
export DATABASE_URL=postgresql://user:pass@host:port/db
```

2. **Docker部署**
```bash
# 构建镜像
docker build -t config-manager:latest .

# 运行容器
docker run -d \
  --name config-manager \
  -p 8000:8000 \
  -e DATABASE_URL=postgresql://user:pass@host:port/db \
  -e SECRET_KEY=your-secret-key \
  config-manager:latest
```

3. **Kubernetes部署**
```bash
# 应用Kubernetes配置
kubectl apply -f k8s/
```

## 🔧 配置说明

### 配置文件结构

```yaml
# configs/default.yaml
services:
  config_manager:
    host: "0.0.0.0"
    port: 8000
    debug: false

database:
  mongodb:
    host: "localhost"
    port: 27017
    database: "compliance_db"

api_keys:
  content_check: "your_content_api_key"
  beian_query: "your_beian_api_key"
```

### 环境变量

| 变量名 | 说明 | 默认值 |
|--------|------|--------|
| `DATABASE_URL` | 数据库连接URL | `sqlite:///./data/config.db` |
| `SECRET_KEY` | JWT密钥 | `your-secret-key-here` |
| `ENVIRONMENT` | 运行环境 | `development` |
| `REDIS_URL` | Redis连接URL | `redis://localhost:6379/0` |

## 🤝 贡献指南

1. Fork项目
2. 创建功能分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 打开Pull Request

## 📄 许可证

本项目采用MIT许可证 - 查看 [LICENSE](LICENSE) 文件了解详情。

## 📞 支持

如有问题或建议，请通过以下方式联系：

- 创建Issue
- 发送邮件至: support@example.com
- 项目文档: [Wiki](https://github.com/your-repo/wiki)