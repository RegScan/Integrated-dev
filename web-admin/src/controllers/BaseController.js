/**
 * 基础控制器类
 * MVC架构 - Controller层基类
 */
export default class BaseController {
  constructor() {
    this.loading = false
    this.error = null
    this.data = null
  }

  /**
   * 执行操作（带错误处理和加载状态）
   */
  async execute(action, ...args) {
    this.loading = true
    this.error = null
    
    try {
      const result = await action(...args)
      this.data = result
      return result
    } catch (error) {
      this.error = error
      this.handleError(error)
      throw error
    } finally {
      this.loading = false
    }
  }

  /**
   * 处理错误
   */
  handleError(error) {
    console.error('Controller Error:', error)
    
    // 可以在这里添加统一的错误处理逻辑
    // 比如发送错误日志到服务器
    if (import.meta.env.VITE_ENABLE_DEBUG === 'true') {
      console.error('Error Stack:', error.stack)
    }
  }

  /**
   * 验证数据
   */
  validate(data, rules) {
    const errors = {}
    
    for (const field in rules) {
      const fieldRules = rules[field]
      const value = data[field]
      
      for (const rule of fieldRules) {
        const error = this.validateRule(field, value, rule, data)
        if (error) {
          if (!errors[field]) {
            errors[field] = []
          }
          errors[field].push(error)
        }
      }
    }
    
    if (Object.keys(errors).length > 0) {
      const error = new Error('验证失败')
      error.errors = errors
      throw error
    }
    
    return true
  }

  /**
   * 验证单个规则
   */
  validateRule(field, value, rule, data) {
    if (rule.required && !value) {
      return rule.message || `${field}不能为空`
    }
    
    if (rule.min && value.length < rule.min) {
      return rule.message || `${field}长度不能小于${rule.min}`
    }
    
    if (rule.max && value.length > rule.max) {
      return rule.message || `${field}长度不能大于${rule.max}`
    }
    
    if (rule.pattern && !rule.pattern.test(value)) {
      return rule.message || `${field}格式不正确`
    }
    
    if (rule.validator && !rule.validator(value, data)) {
      return rule.message || `${field}验证失败`
    }
    
    return null
  }

  /**
   * 格式化分页参数
   */
  formatPagination(page = 1, pageSize = 10, sort = null) {
    const params = {
      page: Math.max(1, parseInt(page)),
      page_size: Math.max(1, Math.min(100, parseInt(pageSize)))
    }
    
    if (sort) {
      params.sort = sort
    }
    
    return params
  }

  /**
   * 格式化过滤参数
   */
  formatFilters(filters = {}) {
    const formatted = {}
    
    for (const key in filters) {
      const value = filters[key]
      if (value !== null && value !== undefined && value !== '') {
        formatted[key] = value
      }
    }
    
    return formatted
  }

  /**
   * 批量操作
   */
  async batchExecute(items, action, concurrency = 5) {
    const results = []
    const errors = []
    
    // 分批处理
    for (let i = 0; i < items.length; i += concurrency) {
      const batch = items.slice(i, i + concurrency)
      const promises = batch.map(async (item, index) => {
        try {
          const result = await action(item)
          results.push({ index: i + index, item, result })
        } catch (error) {
          errors.push({ index: i + index, item, error })
        }
      })
      
      await Promise.all(promises)
    }
    
    return { results, errors }
  }

  /**
   * 重试机制
   */
  async retry(action, maxRetries = 3, delay = 1000) {
    let lastError = null
    
    for (let i = 0; i < maxRetries; i++) {
      try {
        return await action()
      } catch (error) {
        lastError = error
        if (i < maxRetries - 1) {
          await this.sleep(delay * Math.pow(2, i)) // 指数退避
        }
      }
    }
    
    throw lastError
  }

  /**
   * 延迟执行
   */
  sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms))
  }

  /**
   * 防抖
   */
  debounce(func, wait = 300) {
    let timeout
    return function executedFunction(...args) {
      const later = () => {
        clearTimeout(timeout)
        func(...args)
      }
      clearTimeout(timeout)
      timeout = setTimeout(later, wait)
    }
  }

  /**
   * 节流
   */
  throttle(func, limit = 300) {
    let inThrottle
    return function(...args) {
      if (!inThrottle) {
        func.apply(this, args)
        inThrottle = true
        setTimeout(() => inThrottle = false, limit)
      }
    }
  }

  /**
   * 缓存结果
   */
  memoize(func, keyGenerator) {
    const cache = new Map()
    
    return async function(...args) {
      const key = keyGenerator ? keyGenerator(...args) : JSON.stringify(args)
      
      if (cache.has(key)) {
        return cache.get(key)
      }
      
      const result = await func.apply(this, args)
      cache.set(key, result)
      
      // 设置缓存过期（5分钟）
      setTimeout(() => cache.delete(key), 5 * 60 * 1000)
      
      return result
    }
  }
}