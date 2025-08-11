# Website Scanner 测试指南

## 概述

本目录包含 website-scanner 微服务的完整测试套件，包括单元测试、集成测试和API测试。

## 测试结构

```
tests/
├── conftest.py              # 测试配置和共享fixture
├── test_crawler_service.py  # 爬虫服务测试
├── test_content_checker.py  # 内容检测服务测试
├── test_scan_service.py     # 扫描服务测试
├── test_beian_checker.py    # 备案查询服务测试
├── test_api_endpoints.py    # API接口测试
├── test_integration.py      # 集成测试
├── init-mongo.js           # MongoDB初始化脚本
└── README.md               # 本文件
```

## 测试类型

### 1. 单元测试 (Unit Tests)
- **文件**: `test_*.py` (除了 `test_integration.py`)
- **目的**: 测试单个函数或类的功能
- **特点**: 快速执行，使用模拟对象
- **运行**: `python -m pytest tests/ -m unit`

### 2. 集成测试 (Integration Tests)
- **文件**: `test_integration.py`
- **目的**: 测试多个组件之间的交互
- **特点**: 需要外部服务（MongoDB、Redis）
- **运行**: `python -m pytest tests/ -m integration`

### 3. API测试 (API Tests)
- **文件**: `test_api_endpoints.py`
- **目的**: 测试HTTP API接口
- **特点**: 使用FastAPI TestClient
- **运行**: `python -m pytest tests/test_api_endpoints.py`

## 测试环境

### 本地测试环境

1. **安装依赖**:
```bash
pip install -r requirements.txt
pip install pytest pytest-cov pytest-asyncio pytest-html
```

2. **启动测试服务**:
```bash
# 启动MongoDB测试实例
docker run -d --name mongodb-test -p 27018:27017 mongo:6.0

# 启动Redis测试实例
docker run -d --name redis-test -p 6380:6379 redis:7-alpine
```

3. **设置环境变量**:
```bash
export TESTING=1
export MONGODB_URL=mongodb://localhost:27018/test_scanner
export REDIS_URL=redis://localhost:6380/0
export DEBUG=true
```

### Docker测试环境

使用提供的Docker Compose配置：

```bash
# 启动测试环境
docker-compose -f docker-compose.test.yml up -d

# 运行测试
docker-compose -f docker-compose.test.yml run --rm website-scanner-test python -m pytest tests/ -v

# 清理测试环境
docker-compose -f docker-compose.test.yml down
```

## 运行测试

### 使用测试运行脚本

```bash
# 运行所有测试
python run_tests.py all

# 运行单元测试
python run_tests.py unit

# 运行集成测试
python run_tests.py integration

# 运行覆盖率测试
python run_tests.py coverage

# 运行Docker环境测试
python run_tests.py docker

# 生成测试报告
python run_tests.py report

# 运行特定测试文件
python run_tests.py unit --test-file tests/test_crawler_service.py
```

### 使用pytest直接运行

```bash
# 运行所有测试
pytest tests/ -v

# 运行特定测试文件
pytest tests/test_crawler_service.py -v

# 运行特定测试类
pytest tests/test_crawler_service.py::TestCrawlerService -v

# 运行特定测试方法
pytest tests/test_crawler_service.py::TestCrawlerService::test_crawl_website_success -v

# 运行标记的测试
pytest tests/ -m unit -v
pytest tests/ -m integration -v
pytest tests/ -m crawler -v

# 运行覆盖率测试
pytest tests/ --cov=app --cov-report=html --cov-report=term-missing
```

## 测试标记

- `@pytest.mark.unit`: 单元测试
- `@pytest.mark.integration`: 集成测试
- `@pytest.mark.crawler`: 爬虫相关测试
- `@pytest.mark.scanner`: 扫描相关测试
- `@pytest.mark.slow`: 慢速测试
- `@pytest.mark.asyncio`: 异步测试

## 测试数据

### MongoDB测试数据

测试数据在 `init-mongo.js` 中定义，包括：

- 网站扫描结果
- 备案查询记录
- 测试集合和索引

### 模拟数据

在 `conftest.py` 中定义了各种模拟数据：

- `sample_scan_data`: 扫描配置数据
- `sample_website_content`: 网站内容数据
- `sensitive_words_list`: 敏感词列表

## 测试覆盖率

### 覆盖率目标

- **总体覆盖率**: ≥ 80%
- **核心服务覆盖率**: ≥ 90%
- **API接口覆盖率**: ≥ 85%

### 生成覆盖率报告

```bash
# 生成HTML覆盖率报告
pytest tests/ --cov=app --cov-report=html

# 生成终端覆盖率报告
pytest tests/ --cov=app --cov-report=term-missing

# 生成XML覆盖率报告（用于CI/CD）
pytest tests/ --cov=app --cov-report=xml
```

覆盖率报告位置：
- HTML报告: `htmlcov/index.html`
- XML报告: `coverage.xml`

## 测试最佳实践

### 1. 测试命名

```python
def test_function_name_scenario_expected_result():
    """测试函数名_场景_期望结果"""
    pass
```

### 2. 测试结构

```python
def test_example():
    """测试描述"""
    # Arrange (准备)
    service = Service()
    
    # Act (执行)
    result = service.method()
    
    # Assert (断言)
    assert result == expected_value
```

### 3. 使用Fixture

```python
@pytest.fixture
def service():
    """创建服务实例"""
    return Service()

def test_with_fixture(service):
    """使用fixture的测试"""
    result = service.method()
    assert result is not None
```

### 4. 模拟外部依赖

```python
@patch('module.external_service')
def test_with_mock(mock_service):
    """使用模拟的测试"""
    mock_service.return_value = "mocked_result"
    # 测试逻辑
```

## 故障排除

### 常见问题

1. **MongoDB连接失败**
   ```bash
   # 检查MongoDB是否运行
   docker ps | grep mongodb
   
   # 重启MongoDB
   docker restart mongodb-test
   ```

2. **Redis连接失败**
   ```bash
   # 检查Redis是否运行
   docker ps | grep redis
   
   # 重启Redis
   docker restart redis-test
   ```

3. **测试超时**
   ```bash
   # 增加超时时间
   pytest tests/ --timeout=600
   ```

4. **内存不足**
   ```bash
   # 清理Docker资源
   docker system prune -f
   ```

### 调试测试

```bash
# 详细输出
pytest tests/ -v -s

# 只运行失败的测试
pytest tests/ --lf

# 在失败时停止
pytest tests/ -x

# 显示最慢的测试
pytest tests/ --durations=10
```

## 持续集成

### GitHub Actions配置

```yaml
name: Tests
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
        run: |
          pip install -r requirements.txt
          pip install pytest pytest-cov
      - name: Run tests
        run: |
          python run_tests.py all
      - name: Upload coverage
        uses: codecov/codecov-action@v1
```

## 测试报告

### 生成HTML报告

```bash
pytest tests/ --html=test-report.html --self-contained-html
```

### 生成JUnit XML报告

```bash
pytest tests/ --junitxml=test-results.xml
```

## 性能测试

### 基准测试

```bash
# 运行性能测试
pytest tests/test_integration.py::TestIntegration::test_performance_integration -v

# 内存使用测试
pytest tests/test_integration.py::TestIntegration::test_memory_usage_integration -v
```

### 并发测试

```bash
# 运行并发测试
pytest tests/test_integration.py::TestIntegration::test_concurrent_scanning -v
```

## 安全测试

### 输入验证测试

```bash
# 运行安全相关测试
pytest tests/test_api_endpoints.py -k "invalid" -v
```

## 维护

### 更新测试数据

1. 修改 `init-mongo.js` 中的测试数据
2. 更新 `conftest.py` 中的模拟数据
3. 重新运行测试验证

### 添加新测试

1. 创建新的测试文件 `test_new_feature.py`
2. 添加适当的测试标记
3. 更新本README文件
4. 运行测试确保通过

### 测试清理

```bash
# 清理测试数据
docker exec mongodb-test mongo test_scanner --eval "db.dropDatabase()"

# 清理覆盖率报告
rm -rf htmlcov/
rm -f .coverage
```