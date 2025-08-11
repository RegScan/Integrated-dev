import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import userAPI from '@/api/user'
import router from '@/router'

export const useUserStore = defineStore('user', () => {
  // 状态
  const token = ref(localStorage.getItem('token') || '')
  const refreshToken = ref(localStorage.getItem('refreshToken') || '')
  const userInfo = ref(null)
  const permissions = ref([])
  const cachedViews = ref([])

  // 计算属性
  const isLoggedIn = computed(() => !!token.value)
  const username = computed(() => userInfo.value?.username || '')
  const avatar = computed(() => userInfo.value?.avatar || '')
  const role = computed(() => userInfo.value?.role || '')
  const isAdmin = computed(() => ['admin', 'super_admin'].includes(role.value))

  // 方法
  /**
   * 登录
   */
  const login = async (username, password) => {
    try {
      const res = await userAPI.login(username, password)
      
      // 保存token
      token.value = res.access_token
      refreshToken.value = res.refresh_token
      localStorage.setItem('token', res.access_token)
      localStorage.setItem('refreshToken', res.refresh_token)
      
      // 获取用户信息
      await getUserInfo()
      
      return true
    } catch (error) {
      console.error('登录失败:', error)
      throw error
    }
  }

  /**
   * 获取用户信息
   */
  const getUserInfo = async () => {
    try {
      const user = await userAPI.getCurrentUser()
      userInfo.value = user.data
      permissions.value = user.data.permissions || []
      return user
    } catch (error) {
      console.error('获取用户信息失败:', error)
      throw error
    }
  }

  /**
   * 更新用户信息
   */
  const updateUserInfo = (info) => {
    userInfo.value = { ...userInfo.value, ...info }
  }

  /**
   * 检查权限
   */
  const hasPermission = (permission) => {
    if (isAdmin.value) return true
    return permissions.value.includes(permission)
  }

  /**
   * 刷新token
   */
  const refreshAccessToken = async () => {
    try {
      const res = await userAPI.refreshToken(refreshToken.value)
      token.value = res.access_token
      localStorage.setItem('token', res.access_token)
      return res.access_token
    } catch (error) {
      console.error('刷新token失败:', error)
      logout()
      throw error
    }
  }

  /**
   * 退出登录
   */
  const logout = () => {
    // 清除token
    token.value = ''
    refreshToken.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('refreshToken')
    
    // 清除用户信息
    userInfo.value = null
    permissions.value = []
    cachedViews.value = []
    
    // 跳转到登录页
    router.push('/login')
  }

  /**
   * 添加缓存视图
   */
  const addCachedView = (name) => {
    if (!cachedViews.value.includes(name)) {
      cachedViews.value.push(name)
    }
  }

  /**
   * 删除缓存视图
   */
  const removeCachedView = (name) => {
    const index = cachedViews.value.indexOf(name)
    if (index > -1) {
      cachedViews.value.splice(index, 1)
    }
  }

  /**
   * 清空缓存视图
   */
  const clearCachedViews = () => {
    cachedViews.value = []
  }

  return {
    // 状态
    token,
    refreshToken,
    userInfo,
    permissions,
    cachedViews,
    
    // 计算属性
    isLoggedIn,
    username,
    avatar,
    role,
    isAdmin,
    
    // 方法
    login,
    logout,
    getUserInfo,
    updateUserInfo,
    hasPermission,
    refreshAccessToken,
    addCachedView,
    removeCachedView,
    clearCachedViews
  }
})