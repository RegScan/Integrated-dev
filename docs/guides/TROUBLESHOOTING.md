# 故障排除指南

## 🚨 紧急解决方案

### 您当前遇到的问题

基于启动日志，您遇到了以下问题：

1. ✅ **基础服务正常** - PostgreSQL, Redis, MongoDB 已成功启动
2. ❌ **网络连接超时** - 无法从Docker Hub拉取镜像  
3. ❌ **Python依赖冲突** - alert-handler服务构建失败
4. ❌ **后端服务未启动** - 所有微服务健康检查失败

### 🎯 推荐解决方案

#### 方案1: 立即可用 (推荐)

```powershell
# 1. 停止所有容器
docker-compose down

# 2. 仅启动基础服务 (已修复)
.\start-basic-services.ps1

# 3. 本地启动Python服务
.\start-local-dev.ps1
```

#### 方案2: 修复后重试

```powershell
# 1. 清理Docker缓存
docker system prune -f

# 2. 重新构建有问题的服务
docker-compose build --no-cache alert-handler

# 3. 重新启动
.\start-project.ps1
```

## 📋 当前系统状态

| 服务 | 状态 | 端口 | 备注 |
|------|------|------|------|
| ✅ PostgreSQL | 运行中 | 5432 | 健康 |
| ✅ Redis | 运行中 | 6379 | 健康 |  
| ✅ MongoDB | 运行中 | 27017 | 健康 |
| ❌ API网关 | 未启动 | 8080 | 需构建 |
| ❌ 配置管理 | 未启动 | 8000 | 需构建 |
| ❌ 网站扫描 | 未启动 | 8001 | 需构建 |
| ❌ 告警处理 | 构建失败 | 8002 | 依赖冲突 |
| ❌ Web管理 | 未启动 | 3000 | 需构建 |

## 🛠️ 详细修复步骤

### 步骤1: 验证基础服务

```powershell
# 检查基础服务状态
docker-compose ps postgres redis mongodb

# 测试数据库连接
docker exec postgres pg_isready -U postgres
docker exec redis redis-cli ping
docker exec mongodb mongosh --eval "db.adminCommand('ping')" --quiet
```

### 步骤2: 选择启动方式

根据您的需求选择：

#### A. 快速开发测试
```powershell
# 启动基础服务 + 本地Python服务
.\start-local-dev.ps1

# 然后手动启动各个服务:
.\start-config-manager.ps1
.\start-website-scanner.ps1  
.\start-web-admin.ps1
```

#### B. 完整Docker环境
```powershell
# 如果网络问题解决，重新尝试完整启动
.\start-project.ps1
```

### 步骤3: 验证服务连接

```powershell
# 运行连接测试
python test-services.py
```

## 🔍 问题分析

### 网络问题原因

1. **DNS解析问题** - 无法解析Docker Hub域名
2. **防火墙限制** - 企业网络阻止Docker Hub访问
3. **代理配置** - 需要配置HTTP代理
4. **镜像源问题** - 需要使用国内镜像源

### Python依赖问题

- `charset-normalizer` 版本冲突已修复
- 更新了 `requests` 和 `pydantic` 版本
- 如果仍有问题，请使用本地开发模式

## 📞 获取帮助

### 自助诊断

1. 查看容器日志：
   ```bash
   docker-compose logs [服务名]
   ```

2. 检查网络连接：
   ```bash
   docker network inspect RegScan_app-network
   ```

3. 验证端口状态：
   ```bash
   netstat -ano | findstr :8080
   ```

### 常用调试命令

```powershell
# 查看所有容器状态
docker ps -a

# 查看Docker资源使用
docker system df

# 清理未使用的资源
docker system prune

# 重启Docker Desktop
# 在Windows任务栏右键Docker图标 -> Restart
```

## 🎯 成功标志

系统正常运行的标志：

1. ✅ 基础服务健康检查通过
2. ✅ 至少一个后端服务响应 `/health`
3. ✅ 前端页面可以正常加载
4. ✅ API请求返回正常响应

## 📈 后续优化

一旦系统运行正常，建议：

1. 配置Docker镜像加速器
2. 设置服务自动重启策略  
3. 建立监控和告警机制
4. 定期备份配置和数据

---

**注意**: 如果问题仍然存在，请使用本地开发模式 (`.\start-local-dev.ps1`)，这是最快的解决方案。