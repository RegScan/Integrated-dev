# Celery 应用目录

**功能职责：**

本目录是Celery应用的核心所在，负责定义和配置Celery实例，以及注册所有可被调度的异步任务。

## 文件说明

- `__init__.py`: (通常在此文件或一个单独的`main.py`或`celery.py`文件中) 
  - **创建Celery实例**: `app = Celery(...)`。
  - **加载配置**: `app.config_from_object('config.celeryconfig')`，从指定的配置文件中加载Broker、Backend、任务路由等设置。
  - **自动发现任务**: `app.autodiscover_tasks()`，自动查找并注册在各个模块中定义的任务。

- `tasks.py`: 
  - **定义异步任务**: 在此文件中定义所有具体的业务任务函数，并使用`@app.task`装饰器进行标记。
  - **任务导入**: 为了解耦，此文件通常会从其他业务模块（如`website-scanner`）导入实际的执行函数，然后将其包装成Celery任务。
    ```python
    from celery_app import app
    from website_scanner.services.scanner import run_scan

    @app.task(name='tasks.start_website_scan')
    def start_website_scan(website_id):
        return run_scan(website_id)
    ```

## 开发规范

- **保持简洁**: `task-scheduler`的`app`目录应保持轻量，主要负责任务的“注册”和“代理”，具体的业务逻辑实现应放在相应的业务模块中（如`website-scanner`）。
- **明确命名**: 给任务指定一个明确的名称（`name='...'`），便于追踪和调用。
- **参数序列化**: 确保传递给任务的所有参数都是可以被JSON序列化的（如字符串、数字、列表、字典等），避免传递复杂的Python对象。
- **依赖管理**: 如果任务依赖于其他模块，请确保这些模块已经正确安装在该`task-scheduler`服务的环境中。