# Celery 配置目录

**功能职责：**

本目录存放Celery应用的所有配置文件，将配置与代码分离，便于管理和修改。

## 文件说明

- `celeryconfig.py`: Celery的核心配置文件。这是一个Python文件，允许进行灵活的编程配置。其主要内容包括：
  - **Broker Settings**: 
    - `broker_url`: 指定消息中间件的连接地址，例如 `redis://localhost:6379/0`。
  - **Result Backend Settings**:
    - `result_backend`: 指定任务结果存储的后端，例如 `redis://localhost:6379/1`。
  - **Task Settings**:
    - `task_serializer`: 任务序列化格式，通常为`json`。
    - `result_serializer`: 结果序列化格式，通常为`json`。
    - `accept_content`: 可接受的内容类型列表。
    - `timezone`: 时区设置，对定时任务非常重要。
    - `enable_utc`: 是否使用UTC时间。
  - **Celery Beat Settings (定时任务)**:
    - `beat_schedule`: 这是定义所有周期性任务的核心配置。它是一个字典，每个条目定义一个定时任务的名称、要执行的任务、执行频率（`schedule`）和传递的参数（`args`）。
      ```python
      from celery.schedules import crontab

      beat_schedule = {
          'scan-every-30-seconds': {
              'task': 'tasks.start_website_scan',
              'schedule': 30.0, # 每30秒
              'args': (1,)
          },
          'cleanup-every-night': {
              'task': 'tasks.cleanup_logs',
              'schedule': crontab(hour=0, minute=0), # 每天午夜
          },
      }
      ```
  - **Routing Settings** (可选):
    - `task_routes`: 用于将不同类型的任务路由到不同的队列，实现任务隔离和优先级管理。

## 开发规范

- **集中管理**: 所有Celery相关的配置都应集中在`celeryconfig.py`中，而不是分散在代码各处。
- **环境变量优先**: 对于敏感信息（如Broker的密码）或在不同环境间需要变更的配置，应优先从环境变量中读取，并提供一个默认值。
  ```python
  import os
  broker_url = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
  ```
- **文档清晰**: 对复杂的配置项（特别是`beat_schedule`和`task_routes`）添加注释，说明其用途和目的。