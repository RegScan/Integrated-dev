FROM python:3.8-slim

WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    wget \
    curl \
    gcc \
    g++ \
    && rm -rf /var/lib/apt/lists/*

# 复制requirements文件
COPY requirements.txt .

# 升级pip
RUN pip install --upgrade pip

# 分步安装依赖，先安装基础包
RUN pip install --no-cache-dir fastapi==0.104.1 uvicorn==0.24.0 requests==2.31.0

# 安装其他依赖
RUN pip install --no-cache-dir psutil==5.9.6 aiohttp==3.9.1 beautifulsoup4==4.12.2 lxml==4.9.3

# 安装数据库相关依赖
RUN pip install --no-cache-dir pymongo==4.6.0 sqlalchemy==2.0.23

# 安装认证相关依赖
RUN pip install --no-cache-dir python-jose[cryptography]==3.3.0 passlib[bcrypt]==1.7.4 python-multipart==0.0.6

# 复制应用代码
COPY ./app /app

# 暴露端口
EXPOSE 8001

# 启动命令
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8001"]