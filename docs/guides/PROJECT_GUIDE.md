# 7-21-demo 内容合规检测系统 - 总运行指南

## 📋 项目概述

本项目是一个基于微服务架构的内容合规检测系统，包含网站内容检测、告警处理、配置管理、任务调度等核心功能。

### 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────────┐
│                        Web管理界面                               │
│                    (Vue.js + Element Plus)                     │
│                        端口: 3000                              │
└─────────────────────┬───────────────────────────────────────────┘
                      │
┌─────────────────────▼───────────────────────────────────────────┐
│                      API网关                                   │
│                   (Nginx 反向代理)                             │
│                      端口: 8080                               │
└─────────────────────┬───────────────────────────────────────────┘
                      │
      ┌───────────────┼───────────────┬─────────────────┐
      │               │               │                 │
┌─────▼────┐  ┌──────▼────┐  ┌──────▼────┐  ┌────────▼────┐
│配置管理   │  │网站扫描    │  │告警处理    │  │任务调度      │
│8000      │  │8001       │  │8002       │  │8003         │
│          │  │           │  │           │  │             │
│FastAPI   │  │FastAPI    │  │FastAPI    │  │Celery       │
│PostgreSQL│  │MongoDB    │  │PostgreSQL │  │RabbitMQ     │
│Redis     │  │Redis      │  │Redis      │  │Redis        │
└──────────┘  └───────────┘  └───────────┘  └─────────────┘
```

### 🎯 核心功能

- ✅ **配置管理** - 系统配置、用户认证、权限控制
- ✅ **网站扫描** - 内容爬取、合规检测、结果存储  
- ✅ **告警处理** - 告警通知、自动处置、工单管理
- ✅ **任务调度** - 分布式任务、定时调度、状态监控
- ✅ **Web管理** - 统一管理界面、数据可视化

### 📊 技术栈

| 组件           | 技术栈                          | 端口  |
|---------------|---------------------------------|-------|
| **前端**       | Vue.js 3 + Element Plus + Vite | 3000  |
| **API网关**    | Nginx                          | 8080  |
| **配置管理**   | FastAPI + PostgreSQL + Redis  | 8000  |
| **网站扫描**   | FastAPI + MongoDB + Redis     | 8001  |
| **告警处理**   | FastAPI + PostgreSQL + Redis  | 8002  |
| **任务调度**   | Celery + RabbitMQ + Redis     | 8003  |

## 🚀 快速启动

### 方式一：Docker Compose（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd 7-21-demo

# 2. 启动所有服务
docker-compose up -d

# 3. 查看服务状态
docker-compose ps

# 4. 查看日志
docker-compose logs -f
```

### 方式二：本地开发

```bash
# 1. 启动基础服务（数据库）
.\start-basic-services.ps1

# 2. 启动后端服务（分别在新窗口运行）
.\start-config-manager.ps1
.\start-website-scanner.ps1  
.\start-alert-handler.ps1
.\start-task-scheduler.ps1

# 3. 启动前端服务
.\start-web-admin.ps1

# 4. 健康检查
python quick-test.py
```

### 方式三：健壮修复启动

```bash
# 自动修复依赖和配置问题
.\robust-fix.ps1

# 然后按方式二启动服务
```

## 🔧 服务配置

### 环境变量配置

```bash
# 数据库配置
DATABASE_URL=postgresql://postgres:password@localhost:5432/config_manager
MONGODB_URL=mongodb://localhost:27017/website_scanner
REDIS_URL=redis://localhost:6379/0

# API密钥
SECRET_KEY=your-secret-key-here
CONTENT_API_KEY=your-content-api-key
BAIDU_API_KEY=your-baidu-api-key

# 服务配置
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### 端口分配

| 服务           | 端口  | 协议 | 用途                    |
|---------------|-------|------|------------------------|
| Web前端        | 3000  | HTTP | 管理界面                |
| API网关        | 8080  | HTTP | 统一入口                |
| 配置管理       | 8000  | HTTP | 配置API                |
| 网站扫描       | 8001  | HTTP | 扫描API                |
| 告警处理       | 8002  | HTTP | 告警API                |
| 任务调度       | 8003  | HTTP | 任务API                |
| PostgreSQL    | 5432  | TCP  | 关系数据库              |
| MongoDB       | 27017 | TCP  | 文档数据库              |
| Redis         | 6379  | TCP  | 缓存数据库              |
| RabbitMQ      | 5672  | TCP  | 消息队列                |

## 📚 API使用指南

### 统一访问地址

所有API通过网关统一访问：`http://localhost:8080/api/`

### 主要API端点

```bash
# 用户认证
POST /api/auth/login          # 用户登录
POST /api/auth/logout         # 用户退出
GET  /api/auth/user-info      # 获取用户信息

# 网站扫描
POST /api/scan/scan           # 扫描网站
GET  /api/scan/status/{id}    # 查看扫描状态
GET  /api/results/results     # 获取扫描结果

# 告警管理
GET  /api/alerts/alerts       # 获取告警列表
POST /api/alerts/alerts       # 创建告警
PUT  /api/alerts/alerts/{id}  # 处理告警

# 配置管理
GET  /api/config/system       # 获取系统配置
PUT  /api/config/system       # 更新系统配置
GET  /api/users/users         # 获取用户列表
```

### API认证

```bash
# 1. 登录获取token
curl -X POST "http://localhost:8080/api/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "password"}'

# 2. 使用token访问API
curl -X GET "http://localhost:8080/api/scan/results" \
  -H "Authorization: Bearer <your-token>"
```

## 🔍 功能验证

### 1. Web界面验证

```bash
# 访问管理界面
http://localhost:3000

# 默认登录账号
用户名: admin
密码: password123
```

### 2. API验证

```bash
# 健康检查
curl http://localhost:8080/api/health/config
curl http://localhost:8080/api/health/scanner  
curl http://localhost:8080/api/health/alert

# 扫描测试
curl -X POST "http://localhost:8080/api/scan/scan" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token>" \
  -d '{"domain": "example.com", "scan_type": "full"}'
```

### 3. 数据库验证

```bash
# PostgreSQL
psql -h localhost -U postgres -d config_manager -c "SELECT COUNT(*) FROM users;"

# MongoDB  
mongosh --host localhost:27017 --eval "db.scan_results.countDocuments()"

# Redis
redis-cli ping
redis-cli info memory
```

## 🛠️ 故障排除

### 常见问题

1. **服务启动失败**
   ```bash
   # 检查端口占用
   netstat -tulpn | grep :8000
   
   # 检查日志
   docker-compose logs config-manager
   ```

2. **依赖安装失败**  
   ```bash
   # 运行修复脚本
   .\robust-fix.ps1
   
   # 手动安装依赖
   .\install-dependencies.ps1
   ```

3. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker-compose ps postgres redis mongodb
   
   # 重启数据库服务
   docker-compose restart postgres redis mongodb
   ```

4. **前端无法访问后端**
   ```bash
   # 检查API网关配置
   curl http://localhost:8080/health
   
   # 检查服务路由
   curl http://localhost:8080/api/config/health
   ```

### 调试工具

```bash
# 查看所有服务状态
python test-services.py

# 检查内存使用
python quick-test.py

# 查看详细日志
docker-compose logs -f --tail=100 <service-name>
```

## 📈 性能监控

### 系统指标

- **响应时间**: < 2秒
- **并发处理**: 100+ 请求/秒  
- **内存使用**: < 80%
- **存储空间**: 监控数据库大小

### 监控端点

```bash
# Prometheus指标
http://localhost:8000/metrics  # 配置管理
http://localhost:8001/metrics  # 网站扫描
http://localhost:8002/metrics  # 告警处理

# 健康检查
http://localhost:8080/health   # 总体状态
```

## 🔐 安全配置

### 生产环境安全

1. **环境变量**
   ```bash
   # 生产环境必须配置
   SECRET_KEY=<strong-random-key>
   DATABASE_URL=<production-db-url>
   REDIS_URL=<production-redis-url>
   ```

2. **网络安全**
   - 防火墙规则配置
   - SSL证书部署
   - API访问限制

3. **数据安全**  
   - 数据库加密
   - 敏感信息脱敏
   - 访问日志审计

## 📋 维护指南

### 日常维护

```bash
# 备份数据库
docker exec postgres pg_dump -U postgres config_manager > backup.sql
docker exec mongodb mongodump --archive=backup.archive

# 清理日志
docker system prune -f
find ./logs -name "*.log" -mtime +7 -delete

# 更新服务
docker-compose pull
docker-compose up -d
```

### 性能优化

```bash
# 清理Redis缓存
redis-cli FLUSHDB

# 优化数据库
docker exec postgres psql -U postgres -c "VACUUM ANALYZE;"

# 重启服务
docker-compose restart
```

## 🤝 开发指南

### 代码规范

- **Python**: 遵循PEP 8规范
- **JavaScript**: 遵循ESLint标准  
- **Git**: 使用conventionalcommits规范

### 开发环境

```bash
# Python环境
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Node.js环境  
cd web-admin
npm install
npm run dev
```

### 测试流程

```bash
# 运行单元测试
pytest tests/

# 运行集成测试
python run_tests.py --type integration

# 性能测试
python run_tests.py --type performance
```

## 📞 技术支持

### 问题反馈

- **GitHub Issues**: 创建Issue描述问题
- **文档Wiki**: 查看详细文档
- **日志分析**: 提供相关日志信息

### 版本信息

- **当前版本**: v1.0.0
- **Python版本**: 3.11+
- **Node.js版本**: 18+
- **Docker版本**: 20.10+

---

**最后更新**: 2025年1月
**维护者**: 7-21-demo开发团队
