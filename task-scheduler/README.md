# 任务调度模块 (task-scheduler)

**功能职责：**

本模块是系统的“心脏”，基于Celery实现，负责管理和调度所有后台异步任务。它解耦了主应用和耗时操作，提高了系统的响应能力和可靠性。

## 核心组件

1.  **Celery Beat**: 任务调度器。它是一个定时器进程，根据预设的时间表（Schedule）周期性地将任务发送到消息队列中。
2.  **Celery Worker**: 任务执行者。它是一个或多个工作进程，从消息队列中获取任务并执行。
3.  **Message Broker**: 消息中间件（如Redis、RabbitMQ），用于存储Celery Beat发出的任务和Celery Worker待执行的任务。
4.  **Result Backend**: 结果后端（如Redis、数据库），用于存储任务的执行状态和结果。

## 目录结构说明

-   `app/`: 存放Celery应用实例和任务定义。
    -   `__init__.py`: 创建和配置Celery app实例。
    -   `tasks.py`: 定义具体的异步任务（例如，从`website-scanner`模块导入扫描任务）。
-   `config/`: 存放Celery的配置文件。
    -   `celeryconfig.py`: Celery的核心配置文件，定义Broker URL, Result Backend, Task Routes, Beat Schedule等。
-   `scripts/`: 存放启动服务的脚本。
    -   `start_worker.sh`: 启动Celery Worker进程的脚本。
    -   `start_beat.sh`: 启动Celery Beat进程的脚本。
-   `tests/`: 存放任务相关的测试代码。
-   `docker-compose.yml`: (如果使用) 定义了`task-scheduler`、`redis`等服务的容器化部署配置。
-   `Dockerfile`: 用于构建`task-scheduler`服务的Docker镜像。
-   `requirements.txt`: Python依赖列表。

## 开发规范

-   **任务定义**：所有异步任务应在`app/tasks.py`中定义，并使用`@app.task`装饰器注册。
-   **调度配置**：所有定时任务的调度规则（如每分钟执行一次）应在`config/celeryconfig.py`的`beat_schedule`中集中定义。
-   **模块通信**：`task-scheduler`通过调用其他模块（如`website-scanner`）提供的任务函数来触发任务，而不是在自身实现复杂的业务逻辑。它只负责“调度”，不负责“执行细节”。
-   **配置管理**：Broker和Backend的连接信息等敏感配置应通过环境变量注入，而不是硬编码在`celeryconfig.py`中。
-   **日志记录**：为Celery配置详细的日志，方便追踪任务执行情况和排查问题。
-   **监控**：应部署Flower等Celery监控工具，实时查看任务状态、Worker负载和历史记录。