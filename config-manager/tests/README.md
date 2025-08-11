# Config-Manager 测试指南

## 概述

本目录包含配置管理模块的完整测试套件，包括单元测试、集成测试、API测试和性能测试。

## 测试结构

```
tests/
├── test_config_service.py      # 核心服务测试
├── test_integration.py         # 集成测试
└── README.md                   # 测试说明文档
```

## 测试类型

### 1. 单元测试 (Unit Tests)
- **文件**: `test_config_service.py::TestConfigService`
- **范围**: 配置服务的核心功能
- **特点**: 使用内存数据库，快速执行
- **覆盖**: 配置CRUD、加密解密、批量操作

### 2. API测试 (API Tests)
- **文件**: `test_config_service.py::TestConfigAPI`
- **范围**: RESTful API接口
- **特点**: 测试HTTP请求和响应
- **覆盖**: 所有API端点的功能验证

### 3. 集成测试 (Integration Tests)
- **文件**: `test_integration.py::TestConfigManagerIntegration`
- **范围**: 真实数据库连接和完整工作流程
- **特点**: 使用PostgreSQL数据库
- **覆盖**: 端到端功能验证

### 4. API集成测试 (API Integration Tests)
- **文件**: `test_integration.py::TestConfigManagerAPI`
- **范围**: 完整的API工作流程
- **特点**: 真实HTTP客户端测试
- **覆盖**: 完整API生命周期

### 5. 性能测试 (Performance Tests)
- **文件**: `test_integration.py::TestConfigManagerPerformance`
- **范围**: 系统性能验证
- **特点**: 批量操作和性能基准
- **覆盖**: 响应时间、吞吐量测试

## 环境要求

### 系统要求
- Python 3.9+
- Docker & Docker Compose
- PostgreSQL 15+
- Redis 7+

### Python依赖
```bash
pip install -r requirements.txt
```

### 测试依赖
```bash
pip install pytest pytest-asyncio httpx coverage
```

## 快速开始

### 1. 设置测试环境

```bash
# 启动测试数据库
docker-compose -f docker-compose.test.yml up -d postgres-test redis-test

# 等待数据库启动
sleep 10
```

### 2. 运行所有测试

```bash
# 使用测试脚本（推荐）
python run_tests.py

# 或直接使用pytest
python -m pytest tests/ -v
```

### 3. 运行特定测试

```bash
# 单元测试
python run_tests.py --type unit

# API测试
python run_tests.py --type api

# 集成测试
python run_tests.py --type integration

# 性能测试
python run_tests.py --type performance
```

## 详细测试说明

### 单元测试

测试配置服务的核心功能：

```bash
python -m pytest tests/test_config_service.py::TestConfigService -v
```

**测试内容**:
- 配置创建、读取、更新、删除
- 加密配置的创建和解密
- 批量配置操作
- 配置查询和过滤
- 配置统计功能

### API测试

测试RESTful API接口：

```bash
python -m pytest tests/test_config_service.py::TestConfigAPI -v
```

**测试内容**:
- 健康检查接口
- 配置CRUD API
- 批量操作API
- 配置统计API
- 错误处理

### 集成测试

测试真实数据库连接：

```bash
python -m pytest tests/test_integration.py::TestConfigManagerIntegration -v
```

**测试内容**:
- 数据库连接验证
- 完整CRUD工作流程
- 加密配置工作流程
- 批量操作
- 配置统计

### API集成测试

测试完整API工作流程：

```bash
python -m pytest tests/test_integration.py::TestConfigManagerAPI -v
```

**测试内容**:
- 完整API生命周期
- 加密配置API
- 批量操作API
- 搜索功能
- 导入导出功能

### 性能测试

测试系统性能：

```bash
python -m pytest tests/test_integration.py::TestConfigManagerPerformance -v
```

**测试内容**:
- 批量配置创建性能
- 配置检索性能
- 加密配置性能
- 响应时间验证

## 测试配置

### 环境变量

```bash
# 测试数据库配置
export TEST_DATABASE_URL="postgresql://test_user:test_password@localhost:5433/config_manager_test"

# 测试环境
export ENVIRONMENT=test
export SECRET_KEY=test-secret-key-for-testing-only
```

### 配置文件

测试使用 `configs/test.yaml` 配置文件，包含：
- 测试数据库连接
- 测试API密钥
- 测试服务配置
- 测试数据样本

## 测试报告

### 覆盖率报告

运行测试后，会生成覆盖率报告：

```bash
# 生成HTML覆盖率报告
python -m pytest tests/ --cov=app --cov-report=html

# 查看报告
open htmlcov/index.html
```

### 测试结果

测试结果包含：
- 测试通过/失败统计
- 执行时间统计
- 错误详情
- 覆盖率报告

## 故障排除

### 常见问题

1. **数据库连接失败**
   ```bash
   # 检查Docker容器状态
   docker-compose -f docker-compose.test.yml ps
   
   # 重启数据库容器
   docker-compose -f docker-compose.test.yml restart postgres-test
   ```

2. **测试超时**
   ```bash
   # 增加超时时间
   python -m pytest tests/ --timeout=300
   ```

3. **依赖问题**
   ```bash
   # 重新安装依赖
   pip install -r requirements.txt --force-reinstall
   ```

### 调试模式

```bash
# 启用详细输出
python -m pytest tests/ -v -s

# 只运行失败的测试
python -m pytest tests/ --lf

# 在失败时停止
python -m pytest tests/ -x
```

## 持续集成

### GitHub Actions

```yaml
name: Config Manager Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.9
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python run_tests.py
```

### 本地CI

```bash
# 创建测试脚本
chmod +x run_tests.py

# 运行完整测试套件
./run_tests.py --type all
```

## 测试最佳实践

### 1. 测试隔离
- 每个测试用例独立运行
- 测试前后清理数据
- 使用测试专用数据库

### 2. 测试数据
- 使用真实的测试数据
- 避免硬编码的测试值
- 测试数据可重复使用

### 3. 性能基准
- 设置合理的性能基准
- 监控测试执行时间
- 定期更新性能标准

### 4. 错误处理
- 测试异常情况
- 验证错误响应
- 测试边界条件

## 扩展测试

### 添加新测试

1. 创建测试文件
2. 继承现有测试类
3. 添加测试方法
4. 更新测试文档

### 自定义测试

```python
class TestCustomFeature:
    def test_custom_functionality(self):
        # 自定义测试逻辑
        pass
```

## 联系信息

如有测试相关问题，请联系：
- 项目维护者：[维护者邮箱]
- 测试团队：[测试团队邮箱]