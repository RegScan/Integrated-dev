import BaseModel from './BaseModel'

/**
 * 配置数据模型
 */
export default class ConfigModel extends BaseModel {
  constructor(data = {}) {
    super({
      id: null,
      key: '',
      value: '',
      category: 'general',
      environment: 'development',
      description: '',
      isEncrypted: false,
      isSensitive: false,
      dataType: 'string',
      defaultValue: null,
      validation: null,
      createdAt: null,
      updatedAt: null,
      createdBy: null,
      updatedBy: null,
      version: 1,
      ...data
    })
  }

  /**
   * 验证规则
   */
  get rules() {
    return {
      key: [
        { required: true, message: '配置键不能为空' },
        { pattern: /^[a-zA-Z0-9._-]+$/, message: '配置键只能包含字母、数字、点、下划线和横线' }
      ],
      value: [
        { required: true, message: '配置值不能为空' },
        { validator: this.validateValue.bind(this), message: '配置值格式不正确' }
      ],
      category: [
        { required: true, message: '分类不能为空' }
      ],
      environment: [
        { required: true, message: '环境不能为空' }
      ]
    }
  }

  /**
   * 验证配置值
   */
  validateValue(value) {
    const dataType = this.get('dataType')
    const validation = this.get('validation')
    
    // 根据数据类型验证
    switch (dataType) {
      case 'number':
        if (isNaN(Number(value))) {
          this.addError('value', '配置值必须是数字')
          return false
        }
        break
      case 'boolean':
        if (!['true', 'false', '1', '0'].includes(value.toString().toLowerCase())) {
          this.addError('value', '配置值必须是布尔值')
          return false
        }
        break
      case 'json':
        try {
          JSON.parse(value)
        } catch (e) {
          this.addError('value', '配置值必须是有效的JSON')
          return false
        }
        break
      case 'array':
        try {
          const arr = JSON.parse(value)
          if (!Array.isArray(arr)) {
            this.addError('value', '配置值必须是数组')
            return false
          }
        } catch (e) {
          this.addError('value', '配置值必须是有效的数组')
          return false
        }
        break
    }
    
    // 自定义验证
    if (validation) {
      try {
        const validationRule = JSON.parse(validation)
        if (validationRule.pattern) {
          const pattern = new RegExp(validationRule.pattern)
          if (!pattern.test(value)) {
            this.addError('value', validationRule.message || '配置值格式不正确')
            return false
          }
        }
      } catch (e) {
        // 忽略验证规则解析错误
      }
    }
    
    return true
  }

  /**
   * 获取解析后的值
   */
  getParsedValue() {
    const value = this.get('value')
    const dataType = this.get('dataType')
    
    switch (dataType) {
      case 'number':
        return Number(value)
      case 'boolean':
        return ['true', '1'].includes(value.toString().toLowerCase())
      case 'json':
      case 'array':
        try {
          return JSON.parse(value)
        } catch (e) {
          return value
        }
      default:
        return value
    }
  }

  /**
   * 设置值（自动转换为字符串）
   */
  setValue(value) {
    let stringValue = value
    
    if (typeof value === 'object') {
      stringValue = JSON.stringify(value)
    } else {
      stringValue = String(value)
    }
    
    this.set('value', stringValue)
    return this
  }

  /**
   * 是否是敏感配置
   */
  isSensitive() {
    return this.get('isSensitive') || this.get('isEncrypted')
  }

  /**
   * 获取分类标签
   */
  getCategoryLabel() {
    const categoryMap = {
      general: '通用配置',
      database: '数据库配置',
      api: 'API配置',
      security: '安全配置',
      service: '服务配置',
      feature: '功能配置'
    }
    return categoryMap[this.get('category')] || this.get('category')
  }

  /**
   * 获取环境标签
   */
  getEnvironmentLabel() {
    const envMap = {
      development: '开发环境',
      test: '测试环境',
      staging: '预发布环境',
      production: '生产环境'
    }
    return envMap[this.get('environment')] || this.get('environment')
  }

  /**
   * 转换为API格式
   */
  toAPI() {
    return {
      id: this.get('id'),
      key: this.get('key'),
      value: this.get('value'),
      category: this.get('category'),
      environment: this.get('environment'),
      description: this.get('description'),
      is_encrypted: this.get('isEncrypted'),
      is_sensitive: this.get('isSensitive'),
      data_type: this.get('dataType'),
      default_value: this.get('defaultValue'),
      validation: this.get('validation')
    }
  }

  /**
   * 从API数据创建模型
   */
  static fromAPI(data) {
    return new ConfigModel({
      id: data.id,
      key: data.key,
      value: data.value,
      category: data.category,
      environment: data.environment,
      description: data.description,
      isEncrypted: data.is_encrypted,
      isSensitive: data.is_sensitive,
      dataType: data.data_type,
      defaultValue: data.default_value,
      validation: data.validation,
      createdAt: data.created_at,
      updatedAt: data.updated_at,
      createdBy: data.created_by,
      updatedBy: data.updated_by,
      version: data.version
    })
  }
}