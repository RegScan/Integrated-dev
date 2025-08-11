# 7-21-demo 文档中心

## 📚 文档导航

欢迎来到7-21-demo内容合规检测系统的文档中心！所有技术文档已按照用途和类型进行分类整理。

### 🎯 快速导航

| 分类 | 路径 | 说明 |
|------|------|------|
| **📖 使用指南** | [guides/](./guides/) | 系统使用、故障排除、文档索引 |
| **👨‍💻 开发文档** | [development/](./development/) | 开发方案、进度报告、分阶段规划 |
| **🚀 部署文档** | [deployment/](./deployment/) | 安全配置、服务对接方案 |
| **⚡ 优化文档** | [optimization/](./optimization/) | 性能优化、系统调优方案 |

---

## 📁 详细目录结构

### 📖 guides/ - 使用指南
```
guides/
├── PROJECT_GUIDE.md          # 📋 总运行指南（推荐首读）
├── TROUBLESHOOTING.md        # 🔧 故障排除详细指南
└── DOCUMENTATION_INDEX.md    # 📚 完整文档索引
```

**用途**：系统使用、问题解决、文档导航

### 👨‍💻 development/ - 开发文档
```
development/
├── phases/                   # 分阶段开发文档
│   ├── 第一阶段-核心功能开发.md
│   ├── 第二阶段-功能增强.md
│   └── 第三阶段-系统优化.md
├── 模块化开发方案.md         # 架构设计和开发规范
└── 进度.md                   # 详细开发进度报告
```

**用途**：开发规划、架构设计、进度跟踪

### 🚀 deployment/ - 部署文档
```
deployment/
├── 安全配置说明.md           # 生产环境安全配置
└── 服务对接方案.md           # 第三方服务集成方案
```

**用途**：生产部署、安全配置、服务集成

### ⚡ optimization/ - 优化文档
```
optimization/
└── 性能优化补充方案.md       # 系统性能优化策略
```

**用途**：性能调优、系统优化、扩展方案

---

## 🚀 新用户推荐阅读路径

### 🎯 快速上手（5-10分钟）
1. **[guides/PROJECT_GUIDE.md](./guides/PROJECT_GUIDE.md)** - 了解系统架构和快速启动
2. 根据指南启动系统并验证功能

### 🔍 深入了解（30-60分钟）
1. **[development/进度.md](./development/进度.md)** - 了解项目完整实现状态
2. **[development/模块化开发方案.md](./development/模块化开发方案.md)** - 了解架构设计原理
3. **[deployment/](./deployment/)** - 了解部署和集成方案

### 🛠️ 开发参与（根据需要）
1. **[development/phases/](./development/phases/)** - 了解各开发阶段的详细规划
2. **[optimization/](./optimization/)** - 了解系统优化策略
3. **[guides/TROUBLESHOOTING.md](./guides/TROUBLESHOOTING.md)** - 掌握问题解决方法

---

## 🔗 相关资源

### 📋 项目核心文档
- **[../README.md](../README.md)** - 项目总概述（包含技术方案和实施状态）
- **[../docker-compose.yml](../docker-compose.yml)** - Docker部署配置
- **[../env.example](../env.example)** - 环境变量模板

### 🛠️ 启动脚本
- **[../robust-fix.ps1](../robust-fix.ps1)** - 健壮修复脚本（推荐）
- **[../start-basic-services.ps1](../start-basic-services.ps1)** - 基础服务启动
- **[../start-local-dev.ps1](../start-local-dev.ps1)** - 本地开发指导

### 🧪 测试工具
- **[../test-services.py](../test-services.py)** - 服务连接测试
- **[../quick-test.py](../quick-test.py)** - 快速功能验证

### 📁 模块文档
- **[../config-manager/README.md](../config-manager/README.md)** - 配置管理服务
- **[../website-scanner/README.md](../website-scanner/README.md)** - 网站扫描服务
- **[../alert-handler/README.md](../alert-handler/README.md)** - 告警处理服务
- **[../web-admin/README.md](../web-admin/README.md)** - Web管理界面

---

## 💡 使用建议

### 📖 按角色选择文档

**🆕 新用户/运维人员**：
- 重点阅读：`guides/` 目录
- 关注：快速启动、故障排除

**👨‍💻 开发人员**：
- 重点阅读：`development/` 目录
- 关注：架构设计、开发规范

**🏗️ 架构师/技术负责人**：
- 重点阅读：`development/` + `optimization/` 目录
- 关注：系统设计、性能优化

**🚀 部署/DevOps工程师**：
- 重点阅读：`deployment/` 目录
- 关注：安全配置、服务集成

### 🔄 文档更新

文档会根据项目发展持续更新，建议：
1. 关注项目核心文档（README.md）的版本信息
2. 定期查看 `development/进度.md` 了解最新开发状态
3. 遇到问题优先查看 `guides/TROUBLESHOOTING.md`

---

## 📞 反馈和建议

如果您在使用文档过程中遇到问题或有改进建议：

1. **查找现有文档**：先检查相关目录是否有解答
2. **使用索引**：参考 `guides/DOCUMENTATION_INDEX.md` 查找具体文档
3. **反馈问题**：按照项目贡献指南提交反馈

---

**文档版本**：v2.0  
**最后更新**：2025年1月  
**维护状态**：✅ 活跃维护中

> 💡 **提示**：建议从 [guides/PROJECT_GUIDE.md](./guides/PROJECT_GUIDE.md) 开始您的7-21-demo之旅！