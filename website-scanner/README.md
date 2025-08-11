# Website Scanner 微服务

## 概述

Website Scanner 是内容合规检测系统的核心扫描服务，负责网站内容爬取、合规检测和结果存储。该服务采用真实网站测试策略，确保系统在实际环境中的可靠性。**现已全面升级日志系统，提供详细的实时测试进度和结果反馈。**

## 功能特性

### 🔍 网站爬取
- **Playwright 自动化** - 使用 Chromium 浏览器进行真实网站访问
- **内容提取** - 自动提取网页文本内容和图片URL
- **智能过滤** - 过滤相对路径和无效图片URL
- **错误处理** - 完善的网络异常和超时处理
- **重试机制** - 自动重试失败的请求，提高成功率

### 🛡️ 内容合规检测
- **文本分析** - 检测敏感词汇和违规内容
- **图片检测** - 分析图片内容合规性
- **多维度评估** - 综合文本和图片检测结果
- **置信度评分** - 提供检测结果的置信度

### 📊 数据存储
- **MongoDB 存储** - 使用 MongoDB 存储扫描结果
- **结构化数据** - 标准化的结果数据结构
- **时间戳记录** - 完整的扫描时间记录
- **历史查询** - 支持历史扫描结果查询

### 🔧 系统集成
- **FastAPI 接口** - RESTful API 服务
- **微服务架构** - 独立部署和扩展
- **健康检查** - 系统状态监控
- **详细日志** - 完整的操作日志和测试进度跟踪

### 📝 增强日志系统
- **实时进度跟踪** - 显示当前测试进度和状态
- **详细结果信息** - 爬取时间、文本长度、图片数量等
- **错误诊断** - 失败时显示具体错误信息和处理过程
- **性能分析** - 每个步骤的耗时统计和性能指标
- **持久化日志** - 同时输出到控制台和日志文件
- **兼容性设计** - 支持Windows和Linux系统，避免编码问题

## 技术栈

### 核心框架
- **Python 3.8+** - 主要开发语言
- **FastAPI** - Web 框架
- **Playwright** - 浏览器自动化
- **MongoDB** - 数据存储
- **Redis** - 缓存服务

### 测试框架
- **pytest** - 测试框架
- **真实网站测试** - 基于真实网站的测试策略
- **性能测试** - 响应时间和吞吐量测试
- **错误处理测试** - 异常情况处理验证
- **详细日志测试** - 完整的测试进度和结果记录

## 项目结构

```
website-scanner/
├── app/                          # 应用主目录
│   ├── __init__.py
│   ├── main.py                   # FastAPI 应用入口
│   ├── core/                     # 核心配置
│   │   ├── __init__.py
│   │   └── config.py            # 应用配置
│   ├── api/                      # API 接口
│   │   ├── __init__.py
│   │   ├── scan.py              # 扫描接口
│   │   └── results.py           # 结果查询接口
│   ├── services/                 # 业务服务
│   │   ├── __init__.py
│   │   ├── crawler.py           # 爬虫服务 (已优化)
│   │   ├── content_checker.py   # 内容检测服务
│   │   ├── scan_service.py      # 扫描服务
│   │   └── beian_checker.py     # 备案查询服务
│   ├── models/                   # 数据模型
│   │   ├── __init__.py
│   │   ├── website.py           # 网站模型
│   │   └── scan_result.py       # 扫描结果模型
│   ├── schemas/                  # 数据模式
│   │   ├── __init__.py
│   │   └── scan_result.py       # 扫描结果模式
│   └── utils/                    # 工具类
│       ├── __init__.py
│       ├── cache.py             # 缓存工具
│       └── http_client.py       # HTTP 客户端
├── tests/                        # 测试目录 (已升级)
│   ├── __init__.py
│   ├── conftest.py              # 测试配置
│   ├── test_real_crawler.py     # 真实网站爬虫测试 (带详细日志)
│   ├── test_real_scanner.py     # 真实网站扫描测试 (带详细日志)
│   ├── test_real_websites.py    # 综合真实网站测试 (带详细日志)
│   ├── real_crawler_test.log    # 爬虫测试日志文件
│   ├── real_scanner_test.log    # 扫描测试日志文件
│   ├── real_websites_test.log   # 综合测试日志文件
│   └── init-mongo.js            # MongoDB 初始化脚本
├── docker-compose.test.yml       # 测试环境 Docker 配置
├── docker-compose.yml           # 生产环境 Docker 配置
├── Dockerfile                   # Docker 镜像构建
├── requirements.txt             # Python 依赖
├── pytest.ini                  # pytest 配置
├── run_tests.py                # 测试运行脚本 (已优化)
└── README.md                   # 项目文档 (已更新)
```

## 快速开始

### 环境要求

- Python 3.8+
- Docker & Docker Compose
- MongoDB 4.4+
- Redis 6.0+

### 安装依赖

```bash
# 安装 Python 依赖
pip install -r requirements.txt

# 安装 Playwright 浏览器
playwright install
```

### 启动服务

#### 开发环境

```bash
# 启动 MongoDB 和 Redis
docker-compose up -d mongodb redis

# 启动应用
uvicorn app.main:app --reload --host 0.0.0.0 --port 8001
```

#### 生产环境

```bash
# 使用 Docker Compose 启动所有服务
docker-compose up -d
```

### 运行测试 (已升级)

```bash
# 运行所有真实网站测试 (带详细日志)
python run_tests.py unit

# 运行爬虫测试 (带详细日志)
python run_tests.py crawler

# 运行扫描测试 (带详细日志)
python run_tests.py scanner

# 运行综合测试 (带详细日志)
python run_tests.py real_website

# 运行覆盖率测试
python run_tests.py coverage

# 运行单个测试 (带详细日志)
python -m pytest tests/test_real_crawler.py::TestRealCrawler::test_real_website_crawl_performance -v -s
```

## 日志系统

### 日志功能特性

#### 📊 实时进度跟踪
- 显示当前测试进度 (如: `[PROGRESS] 进度: 1/3 - 正在测试域名: example.com`)
- 测试阶段标识 (如: `[START]`, `[COMPLETE]`)
- 成功/失败状态 (如: `[SUCCESS]`, `[FAILED]`)

#### 📝 详细结果信息
- 爬取时间统计 (如: `[TIME] 爬取时间: 4.33 秒`)
- 内容质量分析 (如: `[TEXT] 文本长度: 189 字符`)
- 图片数量统计 (如: `[IMAGE] 图片数量: 0 张`)

#### 🔍 错误诊断
- 具体错误信息 (如: `[ERROR] 连接超时: example.com`)
- 重试过程跟踪 (如: `[RETRY] 第 2/3 次重试...`)
- 降级策略执行 (如: `[FALLBACK] 尝试降级策略...`)

#### ⚡ 性能分析
- 各步骤耗时统计
- 成功率计算 (如: `[SUMMARY] 成功率: 3/3 (100.0%)`)
- 性能基准对比

### 日志格式

#### 日志级别标识
- `[SETUP]` - 服务初始化
- `[START]` - 测试开始
- `[PROGRESS]` - 测试进度
- `[SUCCESS]` - 成功结果
- `[FAILED]` - 失败结果
- `[WARNING]` - 警告信息
- `[ERROR]` - 错误信息
- `[COMPLETE]` - 测试完成
- `[SUMMARY]` - 测试总结

#### 详细信息标识
- `[TIME]` - 时间相关
- `[TEXT]` - 文本内容
- `[IMAGE]` - 图片相关
- `[SITE]` - 网站信息
- `[STATUS]` - 状态信息
- `[QUALITY]` - 质量分析
- `[PERFORMANCE]` - 性能指标

### 日志输出示例

```
2025-08-06 10:45:23,123 - INFO - [START] 开始基本真实网站爬取测试
2025-08-06 10:45:23,124 - INFO - [PROGRESS] 进度: 1/3 - 正在测试域名: example.com
2025-08-06 10:45:27,456 - INFO - [SUCCESS] example.com 爬取成功
2025-08-06 10:45:27,457 - INFO -    [TIME] 爬取时间: 4.33 秒
2025-08-06 10:45:27,458 - INFO -    [TEXT] 文本长度: 189 字符
2025-08-06 10:45:27,459 - INFO -    [IMAGE] 图片数量: 0 张
2025-08-06 10:45:30,789 - INFO - [WAIT] 等待 3 秒后继续...
2025-08-06 10:45:33,890 - INFO - [SUMMARY] 爬取成功率: 3/3 (100.0%)
2025-08-06 10:45:33,891 - INFO - [COMPLETE] 基本爬取测试完成
```

### 日志文件

每个测试文件都会生成对应的日志文件：

- `tests/real_websites_test.log` - 真实网站测试日志
- `tests/real_crawler_test.log` - 爬虫测试日志
- `tests/real_scanner_test.log` - 扫描测试日志

### 兼容性设计

为了避免Windows系统控制台的编码问题，我们使用了ASCII字符替代emoji：

- `[START]` 替代 🚀
- `[SUCCESS]` 替代 ✅
- `[FAILED]` 替代 ❌
- `[WARNING]` 替代 ⚠️
- `[TIME]` 替代 ⏱️
- `[TEXT]` 替代 📝
- `[IMAGE]` 替代 🖼️

## API 接口

### 扫描接口

#### 单个网站扫描
```http
POST /api/v1/scan
Content-Type: application/json

{
  "domain": "example.com",
  "scan_type": "basic"
}
```

#### 批量网站扫描
```http
POST /api/v1/scan/batch
Content-Type: application/json

{
  "domains": ["example.com", "httpbin.org"],
  "scan_type": "basic"
}
```

### 结果查询接口

#### 查询扫描结果
```http
GET /api/v1/results/{domain}
```

#### 查询历史记录
```http
GET /api/v1/results/history?domain={domain}&limit=10
```

### 健康检查

```http
GET /health
```

## 测试策略

### 真实网站测试

本服务采用**真实网站测试策略**，确保系统在实际环境中的可靠性：

#### 测试网站列表
- `example.com` - 示例网站
- `httpbin.org` - HTTP 测试服务
- `jsonplaceholder.typicode.com` - API 测试服务
- `github.com` - GitHub
- `stackoverflow.com` - Stack Overflow

#### 测试类型
- **爬虫测试** - 验证网站内容爬取能力
- **扫描测试** - 验证合规检测功能
- **性能测试** - 测量响应时间和吞吐量
- **错误处理测试** - 验证异常情况处理
- **内容质量测试** - 验证提取内容的质量

#### 测试特点
- ✅ **真实网络访问** - 不使用任何模拟数据
- ✅ **性能基准** - 建立性能基准和监控
- ✅ **错误恢复** - 测试网络异常和超时处理
- ✅ **内容验证** - 验证提取内容的完整性和准确性
- ✅ **详细日志** - 完整的测试进度和结果记录

### 测试命令 (已升级)

```bash
# 运行爬虫测试 (带详细日志)
python -m pytest tests/test_real_crawler.py -m real_website -v -s

# 运行扫描测试 (带详细日志)
python -m pytest tests/test_real_scanner.py -m real_website -v -s

# 运行综合测试 (带详细日志)
python -m pytest tests/test_real_websites.py -m real_website -v -s

# 运行性能测试 (带详细日志)
python -m pytest tests/ -m "real_website and slow" -v -s

# 运行完整测试套件 (带详细日志)
python run_tests.py crawler
```

## 配置说明

### 环境变量

```bash
# 数据库配置
MONGODB_URL=mongodb://localhost:27017/website_scanner
REDIS_URL=redis://localhost:6379/0

# API 配置
API_KEY=your_api_key_here
DEBUG=true

# 扫描配置
MAX_CONCURRENT_SCANS=5
SCAN_TIMEOUT=30
MAX_IMAGES_PER_SITE=5

# 缓存配置
CACHE_TTL=3600

# 日志配置
LOG_LEVEL=INFO
LOG_FORMAT=%(asctime)s - %(levelname)s - %(message)s
```

### 配置文件

#### `app/core/config.py`
```python
class Settings:
    # 数据库配置
    mongodb_url: str = "mongodb://localhost:27017/website_scanner"
    redis_url: str = "redis://localhost:6379/0"
    
    # API 配置
    api_key: str = "test_key"
    debug: bool = True
    
    # 扫描配置
    max_concurrent_scans: int = 5
    scan_timeout: int = 30
    max_images_per_site: int = 5
    
    # 缓存配置
    cache_ttl: int = 3600
    
    # 日志配置
    log_level: str = "INFO"
    log_format: str = "%(asctime)s - %(levelname)s - %(message)s"
```

## 部署指南

### Docker 部署

```bash
# 构建镜像
docker build -t website-scanner .

# 启动服务
docker-compose up -d
```

### Kubernetes 部署

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: website-scanner
spec:
  replicas: 3
  selector:
    matchLabels:
      app: website-scanner
  template:
    metadata:
      labels:
        app: website-scanner
    spec:
      containers:
      - name: website-scanner
        image: website-scanner:latest
        ports:
        - containerPort: 8001
        env:
        - name: MONGODB_URL
          value: "mongodb://mongodb:27017/website_scanner"
        - name: REDIS_URL
          value: "redis://redis:6379/0"
        - name: LOG_LEVEL
          value: "INFO"
```

## 监控和日志

### 健康检查

```bash
# 检查服务状态
curl http://localhost:8001/health

# 检查详细状态
curl http://localhost:8001/health/detailed
```

### 日志查看

```bash
# 查看应用日志
docker-compose logs website-scanner

# 查看实时日志
docker-compose logs -f website-scanner

# 查看测试日志
tail -f tests/real_crawler_test.log
tail -f tests/real_scanner_test.log
tail -f tests/real_websites_test.log
```

### 性能监控

- **响应时间** - 扫描请求的响应时间
- **吞吐量** - 每秒处理的扫描请求数
- **错误率** - 扫描失败的比例
- **资源使用** - CPU、内存、网络使用情况
- **测试成功率** - 真实网站测试的成功率

## 故障排除

### 常见问题

#### 1. Playwright 浏览器启动失败
```bash
# 重新安装浏览器
playwright install

# 检查系统依赖
playwright install-deps
```

#### 2. MongoDB 连接失败
```bash
# 检查 MongoDB 服务状态
docker-compose ps mongodb

# 检查连接字符串
echo $MONGODB_URL
```

#### 3. 网络超时
```bash
# 增加超时时间
export SCAN_TIMEOUT=60

# 检查网络连接
curl -I https://example.com
```

#### 4. 日志编码问题
```bash
# 检查系统编码
echo $LANG

# 设置UTF-8编码
export LANG=en_US.UTF-8
```

### 调试模式

```bash
# 启用调试模式
export DEBUG=true

# 查看详细日志
docker-compose logs -f website-scanner

# 查看测试日志
tail -f tests/*.log
```

## 贡献指南

### 开发环境设置

```bash
# 克隆项目
git clone <repository-url>
cd website-scanner

# 安装依赖
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 安装预提交钩子
pre-commit install
```

### 代码规范

- 遵循 PEP 8 代码风格
- 使用类型注解
- 编写完整的文档字符串
- 添加单元测试和集成测试
- 确保日志输出清晰和有用

### 提交规范

```
feat: 添加新功能
fix: 修复 bug
docs: 更新文档
test: 添加测试
refactor: 代码重构
style: 代码格式调整
log: 改进日志功能
```

## 更新日志

### v2.0.0 (最新)
- ✅ **全面升级日志系统** - 添加详细的实时测试进度和结果反馈
- ✅ **优化爬虫服务** - 改进错误处理、重试机制和内容提取策略
- ✅ **增强测试稳定性** - 提高真实网站测试的成功率
- ✅ **改进兼容性** - 解决Windows系统控制台编码问题
- ✅ **完善文档** - 更新README.md，添加详细的日志功能说明

### v1.0.0
- 初始版本发布
- 基础爬虫和扫描功能
- 真实网站测试策略

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件。

## 联系方式

- 项目维护者：[维护者姓名]
- 邮箱：[邮箱地址]
- 项目地址：[项目 URL]

---

**注意**: 本服务采用真实网站测试策略，确保系统在实际环境中的可靠性。所有测试都基于真实网站访问，不使用任何模拟数据。**现已全面升级日志系统，提供详细的实时测试进度和结果反馈。**