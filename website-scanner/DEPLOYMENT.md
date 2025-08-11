# Website Scanner 部署指南

## 🚀 快速开始

### 1. 环境要求

- **Python**: 3.8+
- **Docker**: 20.10+ (推荐)
- **内存**: 最少2GB，推荐4GB+
- **磁盘**: 最少10GB可用空间

### 2. 一键启动

```bash
# 克隆项目
git clone <your-repo-url>
cd website-scanner

# 运行快速启动脚本
python quick_start.py
```

## 🔧 手动部署

### 1. 安装依赖

```bash
# 安装Python依赖
pip install -r requirements.txt

# 安装Playwright浏览器
playwright install chromium
```

### 2. 配置环境变量

```bash
# 复制环境变量模板
cp env.example .env

# 编辑配置文件，填入实际的API密钥
nano .env
```

**必需的配置项:**

```bash
# 百度AI内容审核API (必需)
BAIDU_API_KEY=your_actual_baidu_api_key
BAIDU_SECRET_KEY=your_actual_baidu_secret_key

# 阿里云内容安全API (可选)
ALIYUN_ACCESS_KEY=your_aliyun_access_key
ALIYUN_SECRET_KEY=your_aliyun_secret_key

# 数据库配置
MONGODB_URL=mongodb://localhost:27017/website_scanner
REDIS_URL=redis://localhost:6379/1
```

### 3. 启动数据库服务

```bash
# 使用Docker启动MongoDB和Redis
docker-compose up -d mongodb redis

# 或者手动启动
# MongoDB
mongod --dbpath /data/db

# Redis
redis-server
```

### 4. 启动应用服务

```bash
# 启动Website Scanner服务
uvicorn app.main:app --host 0.0.0.0 --port 8001 --reload
```

## 🐳 Docker部署

### 1. 使用Docker Compose (推荐)

```bash
# 启动所有服务
docker-compose up -d

# 查看服务状态
docker-compose ps

# 查看日志
docker-compose logs -f website-scanner
```

### 2. 单独构建镜像

```bash
# 构建镜像
docker build -t website-scanner:latest .

# 运行容器
docker run -d \
  --name website-scanner \
  -p 8001:8001 \
  -e MONGODB_URL=mongodb://host.docker.internal:27017/website_scanner \
  -e REDIS_URL=redis://host.docker.internal:6379/1 \
  website-scanner:latest
```

## 🔑 API密钥获取

### 百度AI内容审核API

1. 访问 [百度AI开放平台](https://ai.baidu.com/)
2. 注册账号并创建应用
3. 选择"内容审核"产品
4. 获取API Key和Secret Key

### 阿里云内容安全API

1. 访问 [阿里云内容安全](https://www.aliyun.com/product/saf/)
2. 开通服务并创建AccessKey
3. 获取AccessKey ID和Secret

## 📊 监控和日志

### 1. 服务状态检查

```bash
# 健康检查
curl http://localhost:8001/health

# 服务信息
curl http://localhost:8001/info
```

### 2. 监控面板

- **Grafana**: http://localhost:3000 (admin/admin)
- **Prometheus**: http://localhost:9090

### 3. 日志查看

```bash
# 应用日志
tail -f logs/website_scanner.log

# Docker日志
docker-compose logs -f website-scanner
```

## 🧪 测试验证

### 1. 运行测试套件

```bash
# 运行所有测试
python -m pytest tests/ -v

# 运行特定测试
python -m pytest tests/test_real_websites.py -v

# 生成覆盖率报告
python -m pytest tests/ --cov=app --cov-report=html
```

### 2. 手动测试

```bash
# 测试扫描接口
curl -X POST "http://localhost:8001/scan" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com"}'

# 测试结果查询
curl "http://localhost:8001/results?url=https://example.com"
```

## 🔒 安全配置

### 1. 生产环境安全

```bash
# 禁用调试模式
DEBUG=false

# 设置强密码
GRAFANA_ADMIN_PASSWORD=your_strong_password

# 限制访问IP
ALLOWED_HOSTS=["your-domain.com", "your-ip"]
```

### 2. 防火墙配置

```bash
# 只开放必要端口
ufw allow 8001/tcp  # Website Scanner
ufw allow 27017/tcp # MongoDB (内网)
ufw allow 6379/tcp  # Redis (内网)
ufw allow 3000/tcp  # Grafana (可选)
ufw allow 9090/tcp  # Prometheus (可选)
```

## 🚨 故障排除

### 1. 常见问题

**服务无法启动:**
```bash
# 检查端口占用
netstat -tulpn | grep 8001

# 检查日志
tail -f logs/website_scanner.log
```

**数据库连接失败:**
```bash
# 检查MongoDB状态
docker-compose ps mongodb

# 检查网络连接
docker-compose exec website-scanner ping mongodb
```

**内存不足:**
```bash
# 调整内存限制
docker-compose down
docker-compose up -d --scale website-scanner=1
```

### 2. 性能优化

```bash
# 调整并发数
MAX_CONCURRENT_SCANS=3

# 启用缓存
CACHE_ENABLED=true

# 限制浏览器内存
BROWSER_MAX_MEMORY_MB=256
```

## 📈 扩展部署

### 1. 负载均衡

```yaml
# nginx配置示例
upstream website_scanner {
    server 127.0.0.1:8001;
    server 127.0.0.1:8002;
    server 127.0.0.1:8003;
}
```

### 2. 集群部署

```bash
# 启动多个实例
docker-compose up -d --scale website-scanner=3

# 使用Redis集群
docker-compose up -d redis-cluster
```

## 📞 技术支持

- **文档**: 查看项目README.md
- **问题反馈**: 提交GitHub Issue
- **配置帮助**: 参考env.example文件

---

**部署完成!** 🎉

您的Website Scanner服务现在应该可以正常工作了。访问 http://localhost:8001 查看API文档。
