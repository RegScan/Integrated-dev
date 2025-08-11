<template>
  <el-container class="main-layout">
    <!-- 侧边栏 -->
    <el-aside :width="isCollapse ? '64px' : '240px'" class="layout-aside">
      <div class="logo-container">
        <img src="/logo.svg" alt="Logo" class="logo" />
        <span v-if="!isCollapse" class="logo-text">合规检测系统</span>
      </div>
      
      <el-scrollbar>
        <el-menu
          :default-active="activeMenu"
          :collapse="isCollapse"
          :unique-opened="true"
          :collapse-transition="false"
          router
          class="layout-menu"
        >
          <template v-for="item in menuList" :key="item.path">
            <!-- 有子菜单 -->
            <el-sub-menu v-if="item.children && item.children.length > 0" :index="item.path">
              <template #title>
                <el-icon><component :is="item.icon" /></el-icon>
                <span>{{ item.title }}</span>
              </template>
              <el-menu-item
                v-for="child in item.children"
                :key="child.path"
                :index="child.path"
              >
                <el-icon><component :is="child.icon" /></el-icon>
                <span>{{ child.title }}</span>
              </el-menu-item>
            </el-sub-menu>
            
            <!-- 无子菜单 -->
            <el-menu-item v-else :index="item.path">
              <el-icon><component :is="item.icon" /></el-icon>
              <span>{{ item.title }}</span>
            </el-menu-item>
          </template>
        </el-menu>
      </el-scrollbar>
    </el-aside>
    
    <el-container>
      <!-- 顶部栏 -->
      <el-header class="layout-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="toggleCollapse">
            <component :is="isCollapse ? 'Expand' : 'Fold'" />
          </el-icon>
          
          <!-- 面包屑 -->
          <el-breadcrumb separator="/" class="breadcrumb">
            <el-breadcrumb-item :to="{ path: '/' }">首页</el-breadcrumb-item>
            <el-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
              {{ item.title }}
            </el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        
        <div class="header-right">
          <!-- 全屏按钮 -->
          <el-tooltip content="全屏" placement="bottom">
            <el-icon class="header-icon" @click="toggleFullscreen">
              <FullScreen />
            </el-icon>
          </el-tooltip>
          
          <!-- 消息通知 -->
          <el-popover placement="bottom" :width="350" trigger="click">
            <template #reference>
              <el-badge :value="unreadCount" :hidden="unreadCount === 0">
                <el-icon class="header-icon">
                  <Bell />
                </el-icon>
              </el-badge>
            </template>
            <div class="notification-list">
              <div class="notification-header">
                <span>消息通知</span>
                <el-link type="primary" @click="markAllRead">全部已读</el-link>
              </div>
              <el-scrollbar max-height="300px">
                <div
                  v-for="item in notifications"
                  :key="item.id"
                  class="notification-item"
                  @click="handleNotificationClick(item)"
                >
                  <div class="notification-content">
                    <div class="notification-title">{{ item.title }}</div>
                    <div class="notification-time">{{ item.time }}</div>
                  </div>
                  <el-tag v-if="!item.read" type="danger" size="small">未读</el-tag>
                </div>
              </el-scrollbar>
              <div class="notification-footer">
                <el-button link @click="viewAllNotifications">查看全部</el-button>
              </div>
            </div>
          </el-popover>
          
          <!-- 用户信息 -->
          <el-dropdown trigger="click" class="user-dropdown">
            <div class="user-info">
              <el-avatar :size="32" :src="userInfo.avatar">
                {{ userInfo.username?.charAt(0) }}
              </el-avatar>
              <span class="username">{{ userInfo.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </div>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="goToProfile">
                  <el-icon><User /></el-icon>
                  个人中心
                </el-dropdown-item>
                <el-dropdown-item @click="goToSettings">
                  <el-icon><Setting /></el-icon>
                  系统设置
                </el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">
                  <el-icon><SwitchButton /></el-icon>
                  退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>
      
      <!-- 主内容区 -->
      <el-main class="layout-main">
        <router-view v-slot="{ Component }">
          <transition name="fade-transform" mode="out-in">
            <keep-alive :include="cachedViews">
              <component :is="Component" />
            </keep-alive>
          </transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '@/stores/user'
import userController from '@/controllers/UserController'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

// 响应式数据
const isCollapse = ref(false)
const notifications = ref([
  { id: 1, title: '系统检测到新的违规内容', time: '5分钟前', read: false },
  { id: 2, title: '扫描任务已完成', time: '1小时前', read: false },
  { id: 3, title: '配置更新成功', time: '2小时前', read: true }
])

// 菜单配置
const menuList = ref([
  {
    path: '/dashboard',
    title: '仪表盘',
    icon: 'DataAnalysis'
  },
  {
    path: '/scan',
    title: '扫描管理',
    icon: 'Search',
    children: [
      { path: '/scan/website', title: '网站扫描', icon: 'Globe' },
      { path: '/scan/traffic', title: '流量检测', icon: 'Connection' },
      { path: '/scan/history', title: '扫描历史', icon: 'Clock' }
    ]
  },
  {
    path: '/alert',
    title: '告警中心',
    icon: 'Warning',
    children: [
      { path: '/alert/list', title: '告警列表', icon: 'List' },
      { path: '/alert/rules', title: '告警规则', icon: 'SetUp' },
      { path: '/alert/statistics', title: '告警统计', icon: 'DataLine' }
    ]
  },
  {
    path: '/config',
    title: '配置管理',
    icon: 'Setting',
    children: [
      { path: '/config/system', title: '系统配置', icon: 'Tools' },
      { path: '/config/service', title: '服务配置', icon: 'Service' },
      { path: '/config/api', title: 'API配置', icon: 'Link' }
    ]
  },
  {
    path: '/user',
    title: '用户管理',
    icon: 'UserFilled',
    children: [
      { path: '/user/list', title: '用户列表', icon: 'User' },
      { path: '/user/role', title: '角色管理', icon: 'Avatar' },
      { path: '/user/permission', title: '权限管理', icon: 'Lock' }
    ]
  },
  {
    path: '/report',
    title: '报表分析',
    icon: 'Document',
    children: [
      { path: '/report/compliance', title: '合规报表', icon: 'DocumentChecked' },
      { path: '/report/operation', title: '运营报表', icon: 'TrendCharts' },
      { path: '/report/export', title: '报表导出', icon: 'Download' }
    ]
  },
  {
    path: '/system',
    title: '系统监控',
    icon: 'Monitor',
    children: [
      { path: '/system/status', title: '服务状态', icon: 'CircleCheck' },
      { path: '/system/logs', title: '系统日志', icon: 'Notebook' },
      { path: '/system/backup', title: '备份恢复', icon: 'FolderOpened' }
    ]
  }
])

// 计算属性
const activeMenu = computed(() => route.path)
const breadcrumbs = computed(() => {
  const matched = route.matched.filter(item => item.meta && item.meta.title)
  return matched.map(item => ({
    path: item.path,
    title: item.meta.title
  }))
})
const cachedViews = computed(() => userStore.cachedViews || [])
const userInfo = computed(() => userStore.userInfo || {})
const unreadCount = computed(() => notifications.value.filter(n => !n.read).length)

// 方法
const toggleCollapse = () => {
  isCollapse.value = !isCollapse.value
}

const toggleFullscreen = () => {
  if (document.fullscreenElement) {
    document.exitFullscreen()
  } else {
    document.documentElement.requestFullscreen()
  }
}

const markAllRead = () => {
  notifications.value.forEach(n => n.read = true)
}

const handleNotificationClick = (item) => {
  item.read = true
  // 跳转到相关页面
}

const viewAllNotifications = () => {
  router.push('/notifications')
}

const goToProfile = () => {
  router.push('/profile')
}

const goToSettings = () => {
  router.push('/settings')
}

const handleLogout = async () => {
  try {
    const success = await userController.logout()
    if (success) {
      userStore.logout()
      router.push('/login')
    }
  } catch (error) {
    console.error('退出登录失败:', error)
  }
}

// 生命周期
onMounted(() => {
  // 获取用户信息
  try {
    userController.getCurrentUser()
  } catch (error) {
    console.error('获取用户信息失败:', error)
  }
})
</script>

<style lang="scss" scoped>
.main-layout {
  height: 100vh;
  
  .layout-aside {
    background: linear-gradient(180deg, #304156 0%, #283443 100%);
    box-shadow: 2px 0 8px rgba(0, 0, 0, 0.1);
    transition: width 0.3s;
    
    .logo-container {
      height: 60px;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 0 20px;
      border-bottom: 1px solid rgba(255, 255, 255, 0.1);
      
      .logo {
        width: 32px;
        height: 32px;
      }
      
      .logo-text {
        margin-left: 12px;
        font-size: 16px;
        font-weight: 600;
        color: #fff;
        white-space: nowrap;
      }
    }
    
    .layout-menu {
      border: none;
      background: transparent;
      
      :deep(.el-menu-item),
      :deep(.el-sub-menu__title) {
        color: rgba(255, 255, 255, 0.85);
        
        &:hover {
          background: rgba(255, 255, 255, 0.1);
        }
        
        &.is-active {
          background: rgba(64, 158, 255, 0.2);
          color: #409eff;
        }
      }
    }
  }
  
  .layout-header {
    height: 60px;
    padding: 0 20px;
    background: #fff;
    box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
    display: flex;
    align-items: center;
    justify-content: space-between;
    
    .header-left {
      display: flex;
      align-items: center;
      
      .collapse-btn {
        font-size: 20px;
        cursor: pointer;
        margin-right: 20px;
        transition: transform 0.3s;
        
        &:hover {
          transform: scale(1.1);
          color: #409eff;
        }
      }
      
      .breadcrumb {
        font-size: 14px;
      }
    }
    
    .header-right {
      display: flex;
      align-items: center;
      gap: 20px;
      
      .header-icon {
        font-size: 20px;
        cursor: pointer;
        transition: color 0.3s;
        
        &:hover {
          color: #409eff;
        }
      }
      
      .user-dropdown {
        .user-info {
          display: flex;
          align-items: center;
          gap: 8px;
          cursor: pointer;
          
          .username {
            font-size: 14px;
            color: #606266;
          }
        }
      }
    }
  }
  
  .layout-main {
    background: #f5f7fa;
    padding: 20px;
    overflow-y: auto;
  }
}

.notification-list {
  .notification-header {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px 0;
    border-bottom: 1px solid #ebeef5;
    margin-bottom: 8px;
    
    span {
      font-weight: 600;
      font-size: 16px;
    }
  }
  
  .notification-item {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 12px;
    cursor: pointer;
    transition: background 0.3s;
    
    &:hover {
      background: #f5f7fa;
    }
    
    .notification-content {
      flex: 1;
      
      .notification-title {
        font-size: 14px;
        color: #303133;
        margin-bottom: 4px;
      }
      
      .notification-time {
        font-size: 12px;
        color: #909399;
      }
    }
  }
  
  .notification-footer {
    padding: 12px 0;
    text-align: center;
    border-top: 1px solid #ebeef5;
    margin-top: 8px;
  }
}

// 页面切换动画
.fade-transform-enter-active,
.fade-transform-leave-active {
  transition: all 0.3s;
}

.fade-transform-enter-from {
  opacity: 0;
  transform: translateX(-30px);
}

.fade-transform-leave-to {
  opacity: 0;
  transform: translateX(30px);
}
</style>