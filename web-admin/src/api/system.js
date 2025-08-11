/**
 * 系统管理相关API
 */
import request from './request'
import { buildApiUrl, API_PATHS, getHealthCheckUrl } from './config'

/**
 * 获取系统健康状态
 * @param {string} service - 服务名称 (可选)
 */
export function getSystemHealth(service = null) {
  if (service) {
    return request.get(getHealthCheckUrl(service))
  }
  
  // 获取所有服务的健康状态
  const services = ['WEBSITE_SCANNER', 'CONFIG_MANAGER', 'ALERT_HANDLER', 'TASK_SCHEDULER']
  const promises = services.map(srv => 
    request.get(getHealthCheckUrl(srv)).catch(err => ({
      service: srv,
      status: 'error',
      error: err.message
    }))
  )
  
  return Promise.all(promises)
}

/**
 * 获取系统指标
 * @param {Object} params - 查询参数
 */
export function getSystemMetrics(params = {}) {
  return request.get(
    buildApiUrl('CONFIG_MANAGER', API_PATHS.SYSTEM.METRICS),
    params
  )
}

/**
 * 获取系统日志
 * @param {Object} params - 查询参数
 */
export function getSystemLogs(params = {}) {
  return request.get(
    buildApiUrl('CONFIG_MANAGER', API_PATHS.SYSTEM.LOGS),
    params
  )
}

/**
 * 获取系统配置
 */
export function getSystemConfig() {
  return request.get(
    buildApiUrl('CONFIG_MANAGER', API_PATHS.CONFIG.SYSTEM)
  )
}

/**
 * 更新系统配置
 * @param {Object} data - 配置数据
 */
export function updateSystemConfig(data) {
  return request.put(
    buildApiUrl('CONFIG_MANAGER', API_PATHS.CONFIG.SYSTEM),
    data
  )
}

/**
 * 重启服务
 * @param {string} service - 服务名称
 */
export function restartService(service) {
  return request.post(
    buildApiUrl('CONFIG_MANAGER', `/system/services/${service}/restart`)
  )
}

/**
 * 获取服务状态
 * @param {string} service - 服务名称
 */
export function getServiceStatus(service) {
  return request.get(
    buildApiUrl('CONFIG_MANAGER', `/system/services/${service}/status`)
  )
}

/**
 * 清理系统缓存
 */
export function clearSystemCache() {
  return request.post(
    buildApiUrl('CONFIG_MANAGER', '/system/cache/clear')
  )
}

/**
 * 备份系统数据
 * @param {Object} data - 备份配置
 */
export function backupSystem(data = {}) {
  return request.post(
    buildApiUrl('CONFIG_MANAGER', '/system/backup'),
    data
  )
}

/**
 * 恢复系统数据
 * @param {Object} data - 恢复配置
 */
export function restoreSystem(data) {
  return request.post(
    buildApiUrl('CONFIG_MANAGER', '/system/restore'),
    data
  )
}

/**
 * 获取系统版本信息
 */
export function getSystemVersion() {
  return request.get(
    buildApiUrl('CONFIG_MANAGER', '/system/version')
  )
}

/**
 * 检查系统更新
 */
export function checkSystemUpdate() {
  return request.get(
    buildApiUrl('CONFIG_MANAGER', '/system/update/check')
  )
} 