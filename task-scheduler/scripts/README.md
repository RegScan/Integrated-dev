# 启动脚本目录

**功能职责：**

本目录存放用于启动和管理`task-scheduler`服务的Shell脚本。这些脚本封装了启动Celery进程所需的复杂命令，简化了服务的部署和运维操作。

## 文件说明

- `start_worker.sh`: 
  - **功能**: 启动一个或多个Celery Worker进程。
  - **核心命令**: `celery -A app worker -l info`
  - **常用参数**:
    - `-A app`: 指定Celery应用实例的位置。
    - `-l info`: 设置日志级别为INFO。
    - `-c 4`: 指定并发worker进程/线程的数量（根据CPU核心数调整）。
    - `-Q queue1,queue2`: 指定该worker只消费来自特定队列的任务。
    - `--hostname=worker1@%h`: 为worker指定一个唯一的主机名。

- `start_beat.sh`:
  - **功能**: 启动Celery Beat定时任务调度器进程。
  - **核心命令**: `celery -A app beat -l info`
  - **常用参数**:
    - `-s /var/run/celery/beat-schedule`: 指定存储调度状态的文件路径，确保Beat进程重启后能恢复状态。
    - `--pidfile=/var/run/celery/beat.pid`: 指定进程ID文件的路径。

## 开发规范

- **使用环境变量**: 脚本应设计为可配置的，通过环境变量来接收参数（如Worker数量、队列名称等），而不是将它们硬编码在脚本中。
- **可执行权限**: 确保所有`.sh`脚本都具有可执行权限 (`chmod +x *.sh`)。
- **日志输出**: 脚本应将Celery进程的输出重定向到日志文件，而不是直接打印到控制台，以便于后台运行和问题排查。
- **进程管理**: 在生产环境中，应使用`supervisor`、`systemd`或类似的进程管理工具来调用这些脚本，以确保服务的稳定运行和自动重启。
- **平台兼容性**: 如果需要在不同操作系统（如Linux和macOS）上运行，请确保脚本使用的是兼容的Shell语法。