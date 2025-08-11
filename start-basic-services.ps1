# 简化启动脚本 - 仅启动基础服务
# 用于网络问题时的应急启动

Write-Host "=== 启动基础服务 ===" -ForegroundColor Green
Write-Host "仅启动数据库和Redis，跳过需要构建的服务" -ForegroundColor Yellow

# 检查Docker是否运行
try {
    docker --version | Out-Null
    if ($LASTEXITCODE -ne 0) {
        throw "Docker not found"
    }
} catch {
    Write-Host "错误: Docker未安装或未运行，请先启动Docker Desktop" -ForegroundColor Red
    exit 1
}

# 停止所有现有容器
Write-Host "停止现有容器..." -ForegroundColor Yellow
docker-compose down --remove-orphans

# 创建必要的目录
Write-Host "创建必要的目录..." -ForegroundColor Yellow
$directories = @(
    "config-manager/data",
    "config-manager/logs", 
    "config-manager/configs",
    "website-scanner/logs",
    "website-scanner/data",
    "alert-handler/templates",
    "logs"
)

foreach ($dir in $directories) {
    if (!(Test-Path $dir)) {
        New-Item -ItemType Directory -Path $dir -Force | Out-Null
        Write-Host "创建目录: $dir" -ForegroundColor Gray
    }
}

# 仅启动基础服务（不需要构建的服务）
Write-Host "启动基础服务..." -ForegroundColor Yellow
docker-compose up -d postgres redis mongodb

# 等待服务启动
Write-Host "等待服务启动..." -ForegroundColor Yellow
Start-Sleep -Seconds 10

# 显示服务状态
Write-Host "`n=== 基础服务状态 ===" -ForegroundColor Green
docker-compose ps postgres redis mongodb

# 显示连接信息
Write-Host "`n=== 数据库连接信息 ===" -ForegroundColor Green
Write-Host "PostgreSQL:  localhost:5432 (用户名: postgres, 密码: password)" -ForegroundColor Cyan
Write-Host "MongoDB:     localhost:27017" -ForegroundColor Cyan
Write-Host "Redis:       localhost:6379" -ForegroundColor Cyan

# 健康检查
Write-Host "`n=== 健康检查 ===" -ForegroundColor Green

# PostgreSQL健康检查
Write-Host "检查PostgreSQL..." -ForegroundColor Gray
try {
    $result = docker exec postgres pg_isready -U postgres 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ PostgreSQL - 健康" -ForegroundColor Green
    } else {
        Write-Host "✗ PostgreSQL - 异常" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ PostgreSQL - 无法检查" -ForegroundColor Red
}

# Redis健康检查
Write-Host "检查Redis..." -ForegroundColor Gray
try {
    $result = docker exec redis redis-cli ping 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ Redis - 健康" -ForegroundColor Green
    } else {
        Write-Host "✗ Redis - 异常" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ Redis - 无法检查" -ForegroundColor Red
}

# MongoDB健康检查
Write-Host "检查MongoDB..." -ForegroundColor Gray
try {
    $result = docker exec mongodb mongosh --eval "db.adminCommand('ping')" --quiet 2>$null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ MongoDB - 健康" -ForegroundColor Green
    } else {
        Write-Host "✗ MongoDB - 异常" -ForegroundColor Red
    }
} catch {
    Write-Host "✗ MongoDB - 无法检查" -ForegroundColor Red
}

Write-Host "`n=== 下一步 ===" -ForegroundColor Green
Write-Host "基础服务已启动，现在可以：" -ForegroundColor Yellow
Write-Host "1. 手动启动单个服务进行测试" -ForegroundColor White
Write-Host "2. 修复网络问题后重新运行完整启动脚本" -ForegroundColor White
Write-Host "3. 使用本地开发模式启动具体服务" -ForegroundColor White
Write-Host ""
Write-Host "手动启动示例：" -ForegroundColor Yellow
Write-Host "  cd config-manager && python -m app.main" -ForegroundColor Gray
Write-Host "  cd website-scanner && python -m app.main" -ForegroundColor Gray
