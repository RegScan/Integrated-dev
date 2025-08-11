/**
 * API配置管理
 * 统一管理所有后端服务的API地址
 */

// 服务端点配置 - 统一通过API网关
export const API_ENDPOINTS = {
  // API网关 (统一入口) - 所有请求都通过网关
  GATEWAY: '',  // 使用相对路径，通过nginx代理
  WEBSITE_SCANNER: '',
  CONFIG_MANAGER: '',
  ALERT_HANDLER: '',
  TASK_SCHEDULER: ''
}

// API路径配置 - 与nginx路由配置匹配
export const API_PATHS = {
  // 用户认证 (通过 /api/auth/ 路由到 config-manager)
  AUTH: {
    LOGIN: '/auth/login',
    LOGOUT: '/auth/logout',
    REFRESH: '/auth/refresh',
    USER_INFO: '/auth/user-info'
  },
  
  // 网站扫描 (通过 /api/scan/ 路由到 website-scanner)
  SCAN: {
    SCAN_WEBSITE: '/scan/scan',
    SCAN_BATCH: '/scan/batch',
    SCAN_STATUS: '/scan/status',
    SCAN_RESULTS: '/results/results',
    SCAN_HISTORY: '/results/history'
  },
  
  // 告警管理 (通过 /api/alerts/ 路由到 alert-handler)
  ALERT: {
    ALERTS: '/alerts/alerts',
    ALERT_RULES: '/alert-rules/rules',
    ALERT_ACTIONS: '/actions/actions',
    ALERT_STATS: '/alerts/statistics'
  },
  
  // 配置管理 (通过 /api/config/ 路由到 config-manager)
  CONFIG: {
    SYSTEM: '/config/system',
    USERS: '/users/users',
    SETTINGS: '/config/settings'
  },
  
  // 任务调度 (通过 /api/tasks/ 路由到 task-scheduler)
  TASK: {
    TASKS: '/tasks/tasks',
    SCHEDULES: '/schedules/schedules',
    TASK_STATUS: '/tasks/status'
  },
  
  // 系统监控 (通过 /api/system/ 路由到 config-manager)
  SYSTEM: {
    HEALTH: '/system/health',
    METRICS: '/system/metrics',
    LOGS: '/system/logs'
  }
}

// 构建完整API URL - 直接使用路径，通过nginx代理
export function buildApiUrl(service, path) {
  // 所有请求都通过nginx代理，直接返回路径
  return path
}

// 获取服务健康检查URL
export function getHealthCheckUrl(service) {
  const healthPaths = {
    'WEBSITE_SCANNER': '/api/health/scanner',
    'CONFIG_MANAGER': '/api/health/config',
    'ALERT_HANDLER': '/api/health/alert',
    'TASK_SCHEDULER': '/api/health/task'
  }
  return healthPaths[service] || '/health'
}

// API请求配置
export const API_CONFIG = {
  timeout: 30000,
  retries: 3,
  retryDelay: 1000
} 