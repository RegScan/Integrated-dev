# Web-Admin 故障排除指南

## 常见问题

### 1. 页面一直转圈圈加载，控制台报错

**错误信息**:
```
vendor-7Gwuoxjh.js:5 Uncaught ReferenceError: Cannot access 'aa' before initialization
```

**原因分析**:
- JavaScript模块初始化顺序问题
- Element Plus组件注册时机不当
- 路由守卫中过早使用Pinia store
- Vite构建配置问题

**解决方案**:

#### 方案1: 重新构建Docker镜像
```bash
# 停止并删除现有容器
docker-compose down

# 清理构建缓存
docker-compose build --no-cache

# 重新启动
docker-compose up -d
```

#### 方案2: 使用开发环境
```bash
# 进入web-admin目录
cd web-admin

# 安装依赖
npm install

# 启动开发服务器
npm run dev:simple
```

#### 方案3: 清理并重新安装
```bash
# 清理缓存
npm run clean

# 重新安装依赖
npm run reinstall

# 启动开发服务器
npm run dev
```

### 2. 访问测试页面

如果基本功能有问题，可以访问测试页面验证：
- 测试页面: http://localhost:3000/test
- 登录页面: http://localhost:3000/login

### 3. 检查依赖版本

确保以下依赖版本兼容：
```json
{
  "vue": "^3.4.21",
  "element-plus": "^2.7.0",
  "@element-plus/icons-vue": "^2.3.1",
  "vite": "^5.2.0"
}
```

### 4. 浏览器兼容性

- 推荐使用 Chrome 90+ 或 Edge 90+
- 确保浏览器支持 ES6+ 特性
- 禁用浏览器扩展，避免冲突

### 5. 网络问题

- 检查防火墙设置
- 确保端口3000未被占用
- 检查代理设置

## 开发环境调试

### 1. 启用调试模式
```bash
# 设置环境变量
export VITE_DEBUG=true
export VITE_LOG_LEVEL=debug

# 启动开发服务器
npm run dev
```

### 2. 查看详细日志
```bash
# 查看Docker日志
docker-compose logs web-admin

# 实时日志
docker-compose logs -f web-admin
```

### 3. 进入容器调试
```bash
# 进入运行中的容器
docker exec -it web-admin sh

# 检查文件
ls -la /usr/share/nginx/html
cat /etc/nginx/nginx.conf
```

## 性能优化

### 1. 开发环境优化
- 使用 `npm run dev:simple` 启动
- 禁用错误覆盖层
- 启用热重载

### 2. 生产环境优化
- 启用Gzip压缩
- 静态资源缓存
- 代码分割优化

## 联系支持

如果问题仍然存在，请提供以下信息：
1. 错误日志截图
2. 浏览器控制台输出
3. Docker日志
4. 系统环境信息
