FROM python:3.9-slim

# 设置工作目录
WORKDIR /app

# 设置环境变量
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1
ENV TZ=Asia/Shanghai

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    curl \
    wget \
    docker.io \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 安装Python依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 创建日志目录
RUN mkdir -p /var/log

# 创建非root用户
RUN useradd -m -u 1000 healthmonitor && \
    chown -R healthmonitor:healthmonitor /app /var/log

# 切换到非root用户
USER healthmonitor

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import requests; requests.get('http://localhost:8005/health', timeout=5)"

# 暴露端口
EXPOSE 8005

# 启动命令
CMD ["python", "health_monitor.py", "--config", "health_config.json"]