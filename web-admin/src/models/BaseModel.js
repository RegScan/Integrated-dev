/**
 * 基础数据模型类
 * MVC架构 - Model层基类
 */
export default class BaseModel {
  constructor(data = {}) {
    this._data = data
    this._errors = {}
    this._dirty = false
  }

  /**
   * 获取模型数据
   */
  get data() {
    return this._data
  }

  /**
   * 设置模型数据
   */
  set data(value) {
    this._data = value
    this._dirty = true
  }

  /**
   * 获取指定字段值
   */
  get(field) {
    return this._data[field]
  }

  /**
   * 设置指定字段值
   */
  set(field, value) {
    this._data[field] = value
    this._dirty = true
    return this
  }

  /**
   * 批量设置字段
   */
  fill(data) {
    Object.assign(this._data, data)
    this._dirty = true
    return this
  }

  /**
   * 验证数据
   */
  validate() {
    this._errors = {}
    return this.rules ? this.validateRules() : true
  }

  /**
   * 验证规则
   */
  validateRules() {
    let isValid = true
    
    for (const field in this.rules) {
      const rules = this.rules[field]
      const value = this._data[field]
      
      for (const rule of rules) {
        if (!this.validateRule(field, value, rule)) {
          isValid = false
          break
        }
      }
    }
    
    return isValid
  }

  /**
   * 验证单个规则
   */
  validateRule(field, value, rule) {
    if (rule.required && !value) {
      this.addError(field, rule.message || `${field}不能为空`)
      return false
    }
    
    if (rule.min && value.length < rule.min) {
      this.addError(field, rule.message || `${field}长度不能小于${rule.min}`)
      return false
    }
    
    if (rule.max && value.length > rule.max) {
      this.addError(field, rule.message || `${field}长度不能大于${rule.max}`)
      return false
    }
    
    if (rule.pattern && !rule.pattern.test(value)) {
      this.addError(field, rule.message || `${field}格式不正确`)
      return false
    }
    
    if (rule.validator && !rule.validator(value, this._data)) {
      this.addError(field, rule.message || `${field}验证失败`)
      return false
    }
    
    return true
  }

  /**
   * 添加错误信息
   */
  addError(field, message) {
    if (!this._errors[field]) {
      this._errors[field] = []
    }
    this._errors[field].push(message)
  }

  /**
   * 获取错误信息
   */
  getErrors() {
    return this._errors
  }

  /**
   * 获取第一个错误信息
   */
  getFirstError() {
    for (const field in this._errors) {
      if (this._errors[field].length > 0) {
        return this._errors[field][0]
      }
    }
    return null
  }

  /**
   * 是否有错误
   */
  hasErrors() {
    return Object.keys(this._errors).length > 0
  }

  /**
   * 是否被修改
   */
  isDirty() {
    return this._dirty
  }

  /**
   * 重置修改状态
   */
  resetDirty() {
    this._dirty = false
    return this
  }

  /**
   * 转换为JSON
   */
  toJSON() {
    return this._data
  }

  /**
   * 克隆模型
   */
  clone() {
    return new this.constructor(JSON.parse(JSON.stringify(this._data)))
  }
}