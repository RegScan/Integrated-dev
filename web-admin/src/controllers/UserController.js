import BaseController from './BaseController'
import userAPI from '@/api/user'
import { ElMessage, ElMessageBox } from 'element-plus'

/**
 * 用户控制器
 * 处理用户相关的业务逻辑
 */
class UserController extends BaseController {
  constructor() {
    super()
    this.userList = []
    this.currentUser = null
    this.pagination = {
      page: 1,
      pageSize: 10,
      total: 0
    }
  }

  /**
   * 登录
   */
  async login(username, password) {
    // 验证输入
    this.validate({ username, password }, {
      username: [
        { required: true, message: '请输入用户名' }
      ],
      password: [
        { required: true, message: '请输入密码' }
      ]
    })

    // 执行登录
    const result = await this.execute(
      userAPI.login,
      username,
      password
    )

    if (result) {
      ElMessage.success('登录成功')
      return result
    }
  }

  /**
   * 注册
   */
  async register(userData) {
    // 验证输入
    this.validate(userData, {
      username: [
        { required: true, message: '请输入用户名' },
        { min: 3, message: '用户名至少3个字符' },
        { max: 20, message: '用户名最多20个字符' }
      ],
      email: [
        { required: true, message: '请输入邮箱' },
        { pattern: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: '邮箱格式不正确' }
      ],
      password: [
        { required: true, message: '请输入密码' },
        { min: 6, message: '密码至少6个字符' }
      ],
      confirmPassword: [
        { required: true, message: '请确认密码' },
        { 
          validator: (value, data) => value === data.password,
          message: '两次输入的密码不一致'
        }
      ]
    })

    // 执行注册
    const user = await this.execute(userAPI.register, userData)
    
    if (user) {
      ElMessage.success('注册成功')
      return user
    }
  }

  /**
   * 获取当前用户信息
   */
  async getCurrentUser() {
    const user = await this.execute(userAPI.getCurrentUser)
    this.currentUser = user
    return user
  }

  /**
   * 更新当前用户信息
   */
  async updateCurrentUser(userData) {
    const user = await this.execute(
      userAPI.updateCurrentUser,
      userData
    )
    
    if (user) {
      this.currentUser = user
      ElMessage.success('更新成功')
      return user
    }
  }

  /**
   * 修改密码
   */
  async changePassword(oldPassword, newPassword, confirmPassword) {
    // 验证输入
    this.validate(
      { oldPassword, newPassword, confirmPassword },
      {
        oldPassword: [
          { required: true, message: '请输入原密码' }
        ],
        newPassword: [
          { required: true, message: '请输入新密码' },
          { min: 6, message: '密码至少6个字符' },
          {
            validator: (value) => value !== oldPassword,
            message: '新密码不能与原密码相同'
          }
        ],
        confirmPassword: [
          { required: true, message: '请确认新密码' },
          {
            validator: (value, data) => value === data.newPassword,
            message: '两次输入的密码不一致'
          }
        ]
      }
    )

    // 执行修改
    const result = await this.execute(
      userAPI.changePassword,
      oldPassword,
      newPassword
    )
    
    if (result) {
      ElMessage.success('密码修改成功，请重新登录')
      return result
    }
  }

  /**
   * 获取用户列表
   */
  async getUserList(params = {}) {
    const { page, pageSize, ...filters } = params
    
    const paginationParams = this.formatPagination(page, pageSize)
    const filterParams = this.formatFilters(filters)
    
    const result = await this.execute(
      userAPI.getUserList,
      { ...paginationParams, ...filterParams }
    )
    
    if (result) {
      this.userList = result.list
      this.pagination = {
        page: result.page,
        pageSize: result.pageSize,
        total: result.total
      }
      return result
    }
  }

  /**
   * 获取用户详情
   */
  async getUserById(id) {
    return await this.execute(userAPI.getUserById, id)
  }

  /**
   * 创建用户
   */
  async createUser(userData) {
    // 验证输入
    this.validate(userData, {
      username: [
        { required: true, message: '请输入用户名' }
      ],
      email: [
        { required: true, message: '请输入邮箱' }
      ],
      password: [
        { required: true, message: '请输入密码' }
      ]
    })

    const user = await this.execute(userAPI.createUser, userData)
    
    if (user) {
      ElMessage.success('创建成功')
      // 刷新列表
      await this.getUserList()
      return user
    }
  }

  /**
   * 更新用户
   */
  async updateUser(id, userData) {
    const user = await this.execute(
      userAPI.updateUser,
      id,
      userData
    )
    
    if (user) {
      ElMessage.success('更新成功')
      // 更新列表中的用户
      const index = this.userList.findIndex(u => u.get('id') === id)
      if (index !== -1) {
        this.userList[index] = user
      }
      return user
    }
  }

  /**
   * 删除用户
   */
  async deleteUser(id) {
    const confirmed = await ElMessageBox.confirm(
      '确定要删除该用户吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmed) return

    const result = await this.execute(userAPI.deleteUser, id)
    
    if (result) {
      ElMessage.success('删除成功')
      // 从列表中移除
      this.userList = this.userList.filter(u => u.get('id') !== id)
      return result
    }
  }

  /**
   * 批量删除用户
   */
  async batchDeleteUsers(ids) {
    if (!ids || ids.length === 0) {
      ElMessage.warning('请选择要删除的用户')
      return
    }

    const confirmed = await ElMessageBox.confirm(
      `确定要删除选中的${ids.length}个用户吗？`,
      '批量删除',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmed) return

    const result = await this.execute(
      userAPI.batchDeleteUsers,
      ids
    )
    
    if (result) {
      ElMessage.success(`成功删除${ids.length}个用户`)
      // 刷新列表
      await this.getUserList()
      return result
    }
  }

  /**
   * 启用/禁用用户
   */
  async toggleUserStatus(id, status) {
    const action = status === 'active' ? '启用' : '禁用'
    
    const confirmed = await ElMessageBox.confirm(
      `确定要${action}该用户吗？`,
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmed) return

    const user = await this.execute(
      userAPI.toggleUserStatus,
      id,
      status
    )
    
    if (user) {
      ElMessage.success(`${action}成功`)
      // 更新列表中的用户
      const index = this.userList.findIndex(u => u.get('id') === id)
      if (index !== -1) {
        this.userList[index] = user
      }
      return user
    }
  }

  /**
   * 重置用户密码
   */
  async resetPassword(id) {
    const confirmed = await ElMessageBox.confirm(
      '确定要重置该用户的密码吗？新密码将发送到用户邮箱',
      '重置密码',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmed) return

    const result = await this.execute(
      userAPI.resetPassword,
      id
    )
    
    if (result) {
      ElMessage.success('密码重置成功，新密码已发送到用户邮箱')
      return result
    }
  }

  /**
   * 导出用户列表
   */
  async exportUsers(filters = {}) {
    // 获取所有用户数据
    const allUsers = await this.execute(
      userAPI.getUserList,
      { page: 1, page_size: 10000, ...filters }
    )

    if (!allUsers || allUsers.list.length === 0) {
      ElMessage.warning('没有可导出的数据')
      return
    }

    // 转换为CSV格式
    const headers = ['ID', '用户名', '邮箱', '姓名', '角色', '状态', '创建时间']
    const rows = allUsers.list.map(user => [
      user.get('id'),
      user.get('username'),
      user.get('email'),
      user.get('fullName'),
      user.get('role'),
      user.get('status'),
      user.get('createdAt')
    ])

    // 生成CSV内容
    const csvContent = [
      headers.join(','),
      ...rows.map(row => row.join(','))
    ].join('\n')

    // 创建下载链接
    const blob = new Blob(['\ufeff' + csvContent], { type: 'text/csv;charset=utf-8;' })
    const link = document.createElement('a')
    link.href = URL.createObjectURL(blob)
    link.download = `users_${new Date().getTime()}.csv`
    link.click()

    ElMessage.success('导出成功')
  }

  /**
   * 退出登录
   */
  async logout() {
    const confirmed = await ElMessageBox.confirm(
      '确定要退出登录吗？',
      '提示',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning'
      }
    ).catch(() => false)

    if (!confirmed) return

    await this.execute(userAPI.logout)
    
    this.currentUser = null
    ElMessage.success('已退出登录')
    return true
  }
}

// 导出单例
export default new UserController()