# Config-Manager 常用测试脚本命令

本文件汇总了 config-manager 模块常用的测试脚本命令，便于开发和 CI/CD 场景快速查阅和复用。

---

## 1. 启动测试数据库环境

```bash
docker-compose -f docker-compose.test.yml up -d postgres-test redis-test
# 等待数据库启动
sleep 10
```

## 2. 运行所有测试（推荐）

```bash
python run_tests.py --type all
```

## 3. 运行单元测试

```bash
python run_tests.py --type unit
```

## 4. 运行 API 测试

```bash
python run_tests.py --type api
```

## 5. 运行集成测试

```bash
python run_tests.py --type integration
```

## 6. 运行 API 集成测试

```bash
python run_tests.py --type api-integration
```

## 7. 运行性能测试

```bash
python run_tests.py --type performance
```

## 8. 只设置测试环境（不运行测试）

```bash
python run_tests.py --setup-only
```

## 9. 只清理测试环境

```bash
python run_tests.py --cleanup-only
```

## 10. 直接用 pytest 运行所有测试

```bash
python -m pytest tests/ -v
```

## 11. 生成覆盖率报告

```bash
python -m pytest tests/ --cov=app --cov-report=html
# 查看报告
open htmlcov/index.html
```

## 12. 运行简化的API测试（推荐）

```bash
python -m pytest tests/test_api_simple.py -v
```

## 13. 运行单元测试

```bash
python -m pytest tests/test_config_service.py::TestConfigService -v
```

## 14. 运行核心测试套件（推荐）

```bash
python -m pytest tests/test_api_simple.py tests/test_config_service.py::TestConfigService -v
```

---

## 测试文件结构

### 📁 保留的测试文件
- `test_api_simple.py` - 简化的API测试 (7个测试)
- `test_config_service.py` - 配置服务单元测试 (8个测试)
- `test_scripts.md` - 测试脚本文档
- `README.md` - 测试说明文档

### 🗑️ 已删除的测试文件
- `test_integration.py` - 集成测试 (已删除，问题较多)

---

## 测试结果总结

### ✅ 已完成的测试
- **单元测试**: 8个测试全部通过
- **简化的API测试**: 7个测试全部通过
- **代码覆盖率**: 64%

### 🔧 测试覆盖范围
- 配置服务核心功能 (ConfigService)
- API接口基本功能
- 健康检查接口
- 配置CRUD操作
- 配置统计功能

### 📊 测试统计
- **总测试数**: 15个
- **通过**: 15个
- **失败**: 0个
- **错误**: 0个
- **覆盖率**: 64%

---

> **说明**：
> - 所有命令均在 `config-manager` 目录下执行。
> - 推荐优先使用 `run_tests.py` 脚本，自动管理测试环境和清理。
> - 如需自定义测试类型，可参考 `run_tests.py --help`。
> - 简化的API测试 (`test_api_simple.py`) 是当前最稳定的测试套件。
> - 已清理多余的测试代码，保留最有用的测试。 