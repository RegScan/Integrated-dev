import request from './request'
import UserModel from '@/models/UserModel'

/**
 * 用户API服务
 */
export default {
  /**
   * 用户登录
   */
  async login(username, password) {
    const res = await request.post('/auth/login', {
      username,
      password
    })
    return res.data
  },

  /**
   * 用户注册
   */
  async register(userData) {
    const res = await request.post('/auth/register', userData)
    return UserModel.fromAPI(res.data)
  },

  /**
   * 获取当前用户信息
   */
  async getCurrentUser() {
    const res = await request.get('/users/me')
    return UserModel.fromAPI(res.data)
  },

  /**
   * 更新当前用户信息
   */
  async updateCurrentUser(userData) {
    const res = await request.put('/users/me', userData)
    return UserModel.fromAPI(res.data)
  },

  /**
   * 修改密码
   */
  async changePassword(oldPassword, newPassword) {
    const res = await request.post('/users/change-password', {
      old_password: oldPassword,
      new_password: newPassword
    })
    return res.data
  },

  /**
   * 获取用户列表
   */
  async getUserList(params = {}) {
    const res = await request.get('/users', params)
    return {
      list: res.data.items.map(item => UserModel.fromAPI(item)),
      total: res.data.total,
      page: res.data.page,
      pageSize: res.data.page_size
    }
  },

  /**
   * 获取用户详情
   */
  async getUserById(id) {
    const res = await request.get(`/users/${id}`)
    return UserModel.fromAPI(res.data)
  },

  /**
   * 创建用户
   */
  async createUser(userData) {
    const res = await request.post('/users', userData)
    return UserModel.fromAPI(res.data)
  },

  /**
   * 更新用户
   */
  async updateUser(id, userData) {
    const res = await request.put(`/users/${id}`, userData)
    return UserModel.fromAPI(res.data)
  },

  /**
   * 删除用户
   */
  async deleteUser(id) {
    const res = await request.delete(`/users/${id}`)
    return res.data
  },

  /**
   * 批量删除用户
   */
  async batchDeleteUsers(ids) {
    const res = await request.post('/users/batch-delete', { ids })
    return res.data
  },

  /**
   * 启用/禁用用户
   */
  async toggleUserStatus(id, status) {
    const res = await request.patch(`/users/${id}/status`, { status })
    return UserModel.fromAPI(res.data)
  },

  /**
   * 重置用户密码
   */
  async resetPassword(id) {
    const res = await request.post(`/users/${id}/reset-password`)
    return res.data
  },

  /**
   * 获取用户权限
   */
  async getUserPermissions(id) {
    const res = await request.get(`/users/${id}/permissions`)
    return res.data
  },

  /**
   * 更新用户权限
   */
  async updateUserPermissions(id, permissions) {
    const res = await request.put(`/users/${id}/permissions`, { permissions })
    return res.data
  },

  /**
   * 刷新token
   */
  async refreshToken(refreshToken) {
    const res = await request.post('/auth/refresh', {
      refresh_token: refreshToken
    })
    return res.data
  },

  /**
   * 退出登录
   */
  async logout() {
    const res = await request.post('/auth/logout')
    return res.data
  }
}