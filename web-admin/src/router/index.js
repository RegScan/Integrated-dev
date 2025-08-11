import { createRouter, createWebHistory } from 'vue-router'
import NProgress from 'nprogress'

// 路由配置
const routes = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { title: '登录', noAuth: true }
  },

  {
    path: '/',
    component: () => import('@/views/layout/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '仪表盘', icon: 'DataAnalysis', cache: true }
      },
      // 扫描管理
      {
        path: 'scan',
        name: 'Scan',
        redirect: '/scan/website',
        meta: { title: '扫描管理', icon: 'Search' },
        children: [
          {
            path: 'website',
            name: 'WebsiteScan',
            component: () => import('@/views/scan/WebsiteScan.vue'),
            meta: { title: '网站扫描', cache: true }
          },
          {
            path: 'traffic',
            name: 'TrafficScan',
            component: () => import('@/views/scan/TrafficScan.vue'),
            meta: { title: '流量检测', cache: true }
          },
          {
            path: 'history',
            name: 'ScanHistory',
            component: () => import('@/views/scan/ScanHistory.vue'),
            meta: { title: '扫描历史' }
          },
          {
            path: 'task/:id',
            name: 'TaskDetail',
            component: () => import('@/views/scan/TaskDetail.vue'),
            meta: { title: '任务详情', hidden: true }
          }
        ]
      },
      // 告警中心
      {
        path: 'alert',
        name: 'Alert',
        redirect: '/alert/list',
        meta: { title: '告警中心', icon: 'Warning' },
        children: [
          {
            path: 'list',
            name: 'AlertList',
            component: () => import('@/views/alert/AlertList.vue'),
            meta: { title: '告警列表' }
          },
          {
            path: 'rules',
            name: 'AlertRules',
            component: () => import('@/views/alert/AlertRules.vue'),
            meta: { title: '告警规则' }
          },
          {
            path: 'statistics',
            name: 'AlertStatistics',
            component: () => import('@/views/alert/AlertStatistics.vue'),
            meta: { title: '告警统计' }
          },
          {
            path: 'detail/:id',
            name: 'AlertDetail',
            component: () => import('@/views/alert/AlertDetail.vue'),
            meta: { title: '告警详情', hidden: true }
          }
        ]
      },
      // 配置管理
      {
        path: 'config',
        name: 'Config',
        redirect: '/config/system',
        meta: { title: '配置管理', icon: 'Setting' },
        children: [
          {
            path: 'system',
            name: 'SystemConfig',
            component: () => import('@/views/config/SystemConfig.vue'),
            meta: { title: '系统配置', cache: true }
          },
          {
            path: 'service',
            name: 'ServiceConfig',
            component: () => import('@/views/config/ServiceConfig.vue'),
            meta: { title: '服务配置' }
          },
          {
            path: 'api',
            name: 'ApiConfig',
            component: () => import('@/views/config/ApiConfig.vue'),
            meta: { title: 'API配置' }
          }
        ]
      },
      // 用户管理
      {
        path: 'user',
        name: 'User',
        redirect: '/user/list',
        meta: { title: '用户管理', icon: 'UserFilled' },
        children: [
          {
            path: 'list',
            name: 'UserList',
            component: () => import('@/views/user/UserList.vue'),
            meta: { title: '用户列表' }
          },
          {
            path: 'role',
            name: 'RoleManage',
            component: () => import('@/views/user/RoleManage.vue'),
            meta: { title: '角色管理' }
          },
          {
            path: 'permission',
            name: 'PermissionManage',
            component: () => import('@/views/user/PermissionManage.vue'),
            meta: { title: '权限管理' }
          }
        ]
      },
      // 报表分析
      {
        path: 'report',
        name: 'Report',
        redirect: '/report/compliance',
        meta: { title: '报表分析', icon: 'Document' },
        children: [
          {
            path: 'compliance',
            name: 'ComplianceReport',
            component: () => import('@/views/report/ComplianceReport.vue'),
            meta: { title: '合规报表' }
          },
          {
            path: 'operation',
            name: 'OperationReport',
            component: () => import('@/views/report/OperationReport.vue'),
            meta: { title: '运营报表' }
          },
          {
            path: 'export',
            name: 'ReportExport',
            component: () => import('@/views/report/ReportExport.vue'),
            meta: { title: '报表导出' }
          }
        ]
      },
      // 系统监控
      {
        path: 'system',
        name: 'System',
        redirect: '/system/status',
        meta: { title: '系统监控', icon: 'Monitor' },
        children: [
          {
            path: 'status',
            name: 'SystemStatus',
            component: () => import('@/views/system/SystemStatus.vue'),
            meta: { title: '服务状态' }
          },
          {
            path: 'logs',
            name: 'SystemLogs',
            component: () => import('@/views/system/SystemLogs.vue'),
            meta: { title: '系统日志' }
          },
          {
            path: 'backup',
            name: 'SystemBackup',
            component: () => import('@/views/system/SystemBackup.vue'),
            meta: { title: '备份恢复' }
          }
        ]
      },
      // 个人中心
      {
        path: 'profile',
        name: 'Profile',
        component: () => import('@/views/Profile.vue'),
        meta: { title: '个人中心', hidden: true }
      },
      // 系统设置
      {
        path: 'settings',
        name: 'Settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '系统设置', hidden: true }
      }
    ]
  },
  {
    path: '/403',
    name: '403',
    component: () => import('@/views/error/403.vue'),
    meta: { title: '无权限', noAuth: true }
  },
  {
    path: '/404',
    name: '404',
    component: () => import('@/views/error/404.vue'),
    meta: { title: '页面不存在', noAuth: true }
  },
  {
    path: '/500',
    name: '500',
    component: () => import('@/views/error/500.vue'),
    meta: { title: '服务器错误', noAuth: true }
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/404'
  }
]

// 创建路由实例
const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
  scrollBehavior(to, from, savedPosition) {
    if (savedPosition) {
      return savedPosition
    } else {
      return { top: 0 }
    }
  }
})

// 路由守卫
router.beforeEach(async (to, from, next) => {
  // 开始进度条
  NProgress.start()
  
  // 设置页面标题
  document.title = `${to.meta.title || '页面'} - 内容合规检测系统`
  
  // 不需要认证的页面
  if (to.meta.noAuth) {
    next()
    return
  }
  
  // 动态导入store，避免在模块顶层使用
  try {
    const { useUserStore } = await import('@/stores/user')
    const userStore = useUserStore()
    
    // 检查是否登录
    if (!userStore.isLoggedIn) {
      next({
        path: '/login',
        query: { redirect: to.fullPath }
      })
      return
    }
    
    // 检查权限
    if (to.meta.permission) {
      const hasPermission = userStore.hasPermission(to.meta.permission)
      if (!hasPermission) {
        next('/403')
        return
      }
    }
    
    // 如果用户信息不存在，获取用户信息
    if (!userStore.userInfo) {
      try {
        await userStore.getUserInfo()
      } catch (error) {
        console.error('获取用户信息失败:', error)
        next('/login')
        return
      }
    }
    
    next()
  } catch (error) {
    console.error('路由守卫错误:', error)
    // 如果store初始化失败，重定向到登录页
    next('/login')
  }
})

router.afterEach(() => {
  // 结束进度条
  NProgress.done()
})

export default router