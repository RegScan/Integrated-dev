/**
 * 网站扫描相关API
 */
import request from './request'
import { buildApiUrl, API_PATHS } from './config'

/**
 * 扫描单个网站
 * @param {Object} data - 扫描参数
 * @param {string} data.domain - 域名
 * @param {string} data.scan_type - 扫描类型
 */
export function scanWebsite(data) {
  return request.post(
    buildApiUrl('WEBSITE_SCANNER', API_PATHS.SCAN.SCAN_WEBSITE),
    data
  )
}

/**
 * 批量扫描网站
 * @param {Object} data - 批量扫描参数
 * @param {Array} data.domains - 域名列表
 * @param {string} data.scan_type - 扫描类型
 */
export function scanBatch(data) {
  return request.post(
    buildApiUrl('WEBSITE_SCANNER', API_PATHS.SCAN.SCAN_BATCH),
    data
  )
}

/**
 * 获取扫描状态
 * @param {string} taskId - 任务ID
 */
export function getScanStatus(taskId) {
  return request.get(
    buildApiUrl('WEBSITE_SCANNER', `${API_PATHS.SCAN.SCAN_STATUS}/${taskId}`)
  )
}

/**
 * 获取扫描结果列表
 * @param {Object} params - 查询参数
 */
export function getScanResults(params = {}) {
  return request.get(
    buildApiUrl('WEBSITE_SCANNER', API_PATHS.SCAN.SCAN_RESULTS),
    params
  )
}

/**
 * 获取单个扫描结果详情
 * @param {string} resultId - 结果ID
 */
export function getScanResultDetail(resultId) {
  return request.get(
    buildApiUrl('WEBSITE_SCANNER', `${API_PATHS.SCAN.SCAN_RESULTS}/${resultId}`)
  )
}

/**
 * 获取扫描历史记录
 * @param {Object} params - 查询参数
 */
export function getScanHistory(params = {}) {
  return request.get(
    buildApiUrl('WEBSITE_SCANNER', API_PATHS.SCAN.SCAN_HISTORY),
    params
  )
}

/**
 * 删除扫描结果
 * @param {string} resultId - 结果ID
 */
export function deleteScanResult(resultId) {
  return request.delete(
    buildApiUrl('WEBSITE_SCANNER', `${API_PATHS.SCAN.SCAN_RESULTS}/${resultId}`)
  )
}

/**
 * 重新扫描
 * @param {string} domain - 域名
 */
export function rescanWebsite(domain) {
  return request.post(
    buildApiUrl('WEBSITE_SCANNER', `${API_PATHS.SCAN.SCAN_WEBSITE}/${domain}/rescan`)
  )
} 