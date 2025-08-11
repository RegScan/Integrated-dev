/**
 * 告警管理相关API
 */
import request from './request'
import { buildApiUrl, API_PATHS } from './config'

/**
 * 获取告警列表
 * @param {Object} params - 查询参数
 */
export function getAlerts(params = {}) {
  return request.get(
    buildApiUrl('ALERT_HANDLER', API_PATHS.ALERT.ALERTS),
    params
  )
}

/**
 * 获取告警详情
 * @param {string} alertId - 告警ID
 */
export function getAlertDetail(alertId) {
  return request.get(
    buildApiUrl('ALERT_HANDLER', `${API_PATHS.ALERT.ALERTS}/${alertId}`)
  )
}

/**
 * 处理告警
 * @param {string} alertId - 告警ID
 * @param {Object} data - 处理数据
 */
export function handleAlert(alertId, data) {
  return request.post(
    buildApiUrl('ALERT_HANDLER', `${API_PATHS.ALERT.ALERTS}/${alertId}/handle`),
    data
  )
}

/**
 * 批量处理告警
 * @param {Array} alertIds - 告警ID列表
 * @param {Object} data - 处理数据
 */
export function handleBatchAlerts(alertIds, data) {
  return request.post(
    buildApiUrl('ALERT_HANDLER', `${API_PATHS.ALERT.ALERTS}/batch-handle`),
    { alert_ids: alertIds, ...data }
  )
}

/**
 * 获取告警规则列表
 * @param {Object} params - 查询参数
 */
export function getAlertRules(params = {}) {
  return request.get(
    buildApiUrl('ALERT_HANDLER', API_PATHS.ALERT.ALERT_RULES),
    params
  )
}

/**
 * 创建告警规则
 * @param {Object} data - 规则数据
 */
export function createAlertRule(data) {
  return request.post(
    buildApiUrl('ALERT_HANDLER', API_PATHS.ALERT.ALERT_RULES),
    data
  )
}

/**
 * 更新告警规则
 * @param {string} ruleId - 规则ID
 * @param {Object} data - 规则数据
 */
export function updateAlertRule(ruleId, data) {
  return request.put(
    buildApiUrl('ALERT_HANDLER', `${API_PATHS.ALERT.ALERT_RULES}/${ruleId}`),
    data
  )
}

/**
 * 删除告警规则
 * @param {string} ruleId - 规则ID
 */
export function deleteAlertRule(ruleId) {
  return request.delete(
    buildApiUrl('ALERT_HANDLER', `${API_PATHS.ALERT.ALERT_RULES}/${ruleId}`)
  )
}

/**
 * 获取告警统计信息
 * @param {Object} params - 查询参数
 */
export function getAlertStatistics(params = {}) {
  return request.get(
    buildApiUrl('ALERT_HANDLER', API_PATHS.ALERT.ALERT_STATS),
    params
  )
}

/**
 * 获取告警处置动作列表
 * @param {Object} params - 查询参数
 */
export function getAlertActions(params = {}) {
  return request.get(
    buildApiUrl('ALERT_HANDLER', API_PATHS.ALERT.ALERT_ACTIONS),
    params
  )
}

/**
 * 执行告警处置动作
 * @param {string} alertId - 告警ID
 * @param {string} actionType - 动作类型
 * @param {Object} data - 动作参数
 */
export function executeAlertAction(alertId, actionType, data = {}) {
  return request.post(
    buildApiUrl('ALERT_HANDLER', `${API_PATHS.ALERT.ALERT_ACTIONS}/${actionType}`),
    { alert_id: alertId, ...data }
  )
} 