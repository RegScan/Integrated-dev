# 测试目录

**功能职责：**

本目录存放`task-scheduler`模块的测试代码，重点是验证任务能否被正确触发、执行以及定时任务的调度配置是否正确。

## 文件说明

- `.gitkeep`: 空文件，用于确保该空目录能被Git追踪。

## 开发规范

- **测试框架**: 使用`pytest`。
- **测试重点**:
  - **任务单元测试**: 测试单个任务函数的逻辑。这通常在任务所属的业务模块（如`website-scanner`）中完成，但也可以在这里添加针对任务包装逻辑的测试。
  - **任务集成测试**: 测试任务的完整生命周期，从发送任务到获取结果。
  - **调度配置测试**: 验证`celeryconfig.py`中的`beat_schedule`配置是否正确，例如检查任务名称、频率和参数是否符合预期。

- **Celery测试模式**: 
  - `task_always_eager`: 这是一个非常有用的Celery配置项，在测试时可以将其设置为`True`。它会使所有异步任务都在本地同步执行，而不会发送到Broker。这样，调用`.delay()`或`.apply_async()`会立即返回结果，极大地简化了任务的测试，使其像调用普通函数一样。
    ```python
    # 在测试的conftest.py或setup中
    celery_app.conf.update(task_always_eager=True)
    ```

- **配置测试**: 编写测试用例来加载`celeryconfig.py`并断言其中的`beat_schedule`字典包含正确的键和值。

- **命名规范**: 测试文件名和函数名均以`test_`开头。

- **CI/CD集成**: 将测试套件集成到CI/CD流程中。