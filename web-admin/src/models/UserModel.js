import BaseModel from './BaseModel'

/**
 * 用户数据模型
 */
export default class UserModel extends BaseModel {
  constructor(data = {}) {
    super({
      id: null,
      username: '',
      email: '',
      fullName: '',
      role: 'user',
      avatar: '',
      phone: '',
      status: 'active',
      lastLogin: null,
      createdAt: null,
      updatedAt: null,
      permissions: [],
      ...data
    })
  }

  /**
   * 验证规则
   */
  get rules() {
    return {
      username: [
        { required: true, message: '用户名不能为空' },
        { min: 3, message: '用户名长度不能小于3个字符' },
        { max: 20, message: '用户名长度不能大于20个字符' },
        { pattern: /^[a-zA-Z0-9_]+$/, message: '用户名只能包含字母、数字和下划线' }
      ],
      email: [
        { required: true, message: '邮箱不能为空' },
        { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '邮箱格式不正确' }
      ],
      phone: [
        { pattern: /^1[3-9]\d{9}$/, message: '手机号格式不正确' }
      ],
      password: [
        { required: true, message: '密码不能为空' },
        { min: 6, message: '密码长度不能小于6个字符' }
      ]
    }
  }

  /**
   * 是否是管理员
   */
  isAdmin() {
    return this.get('role') === 'admin' || this.get('role') === 'super_admin'
  }

  /**
   * 是否是超级管理员
   */
  isSuperAdmin() {
    return this.get('role') === 'super_admin'
  }

  /**
   * 是否激活
   */
  isActive() {
    return this.get('status') === 'active'
  }

  /**
   * 是否有权限
   */
  hasPermission(permission) {
    const permissions = this.get('permissions') || []
    return permissions.includes(permission) || this.isSuperAdmin()
  }

  /**
   * 获取显示名称
   */
  getDisplayName() {
    return this.get('fullName') || this.get('username')
  }

  /**
   * 获取头像URL
   */
  getAvatarUrl() {
    return this.get('avatar') || '/default-avatar.png'
  }

  /**
   * 格式化最后登录时间
   */
  getLastLoginFormatted() {
    const lastLogin = this.get('lastLogin')
    if (!lastLogin) return '从未登录'
    
    const date = new Date(lastLogin)
    return date.toLocaleString('zh-CN')
  }

  /**
   * 转换为API格式
   */
  toAPI() {
    const data = this.toJSON()
    // 移除敏感信息
    delete data.password
    return data
  }

  /**
   * 从API数据创建模型
   */
  static fromAPI(data) {
    return new UserModel({
      id: data.id,
      username: data.username,
      email: data.email,
      fullName: data.full_name,
      role: data.role,
      avatar: data.avatar,
      phone: data.phone,
      status: data.status,
      lastLogin: data.last_login,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
      permissions: data.permissions || []
    })
  }
}