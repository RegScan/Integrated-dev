import asyncio
import logging
from typing import Dict, Any, Optional
from datetime import datetime
import sys
import os

# 添加项目根目录到路径
sys.path.append(os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from utils.config_client import alert_client, config_client

logger = logging.getLogger(__name__)

class AlertIntegration:
    """告警集成服务 - 处理扫描结果与告警系统的集成"""
    
    def __init__(self):
        self.alert_client = alert_client
        self.config_client = config_client
        self.alert_enabled = True
        self.alert_threshold = 0.7  # 默认告警阈值
    
    async def initialize(self):
        """初始化告警集成配置"""
        try:
            # 从配置服务获取告警相关配置
            self.alert_enabled = await self.config_client.get_config(
                "alert_enabled", True, "website-scanner"
            )
            self.alert_threshold = await self.config_client.get_config(
                "alert_threshold", 0.7, "website-scanner"
            )
            
            logger.info(f"Alert integration initialized: enabled={self.alert_enabled}, threshold={self.alert_threshold}")
        except Exception as e:
            logger.error(f"Failed to initialize alert integration: {e}")
    
    async def process_scan_result(self, scan_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """处理扫描结果，根据需要创建告警"""
        if not self.alert_enabled:
            logger.debug("Alert integration is disabled")
            return None
        
        try:
            # 检查是否需要创建告警
            if self._should_create_alert(scan_result):
                alert_data = self._build_alert_data(scan_result)
                alert_response = await self._create_alert(alert_data)
                
                if alert_response:
                    logger.info(f"Alert created for scan result: {alert_response.get('id')}")
                    return alert_response
                else:
                    logger.warning("Failed to create alert for scan result")
            
        except Exception as e:
            logger.error(f"Error processing scan result for alerts: {e}")
        
        return None
    
    def _should_create_alert(self, scan_result: Dict[str, Any]) -> bool:
        """判断是否应该创建告警"""
        # 检查是否有违规内容
        violations = scan_result.get("violations", [])
        if not violations:
            return False
        
        # 检查置信度是否超过阈值
        for violation in violations:
            confidence = violation.get("confidence", 0)
            if confidence >= self.alert_threshold:
                return True
        
        return False
    
    def _build_alert_data(self, scan_result: Dict[str, Any]) -> Dict[str, Any]:
        """构建告警数据"""
        violations = scan_result.get("violations", [])
        highest_confidence_violation = max(violations, key=lambda x: x.get("confidence", 0))
        
        # 确定告警严重级别
        severity = self._determine_severity(highest_confidence_violation)
        
        # 构建告警标题和描述
        domain = scan_result.get("domain", "unknown")
        violation_type = highest_confidence_violation.get("type", "unknown")
        confidence = highest_confidence_violation.get("confidence", 0)
        
        title = f"内容违规检测: {domain}"
        description = f"在域名 {domain} 检测到 {violation_type} 类型的违规内容，置信度: {confidence:.2%}"
        
        # 构建证据信息
        evidence = {
            "scan_id": scan_result.get("id"),
            "scan_time": scan_result.get("created_at"),
            "violation_details": violations,
            "scan_summary": {
                "total_pages": scan_result.get("total_pages", 0),
                "violation_pages": len([v for v in violations if v.get("confidence", 0) >= self.alert_threshold]),
                "scan_duration": scan_result.get("scan_duration")
            }
        }
        
        alert_data = {
            "source_module": "website-scanner",
            "target_url": scan_result.get("url"),
            "domain": domain,
            "alert_type": "content_violation",
            "severity": severity,
            "title": title,
            "description": description,
            "evidence": evidence,
            "priority": self._determine_priority(severity, confidence),
            "tags": self._generate_tags(scan_result, violations),
            "metadata": {
                "scanner_version": "1.0.0",
                "scan_type": scan_result.get("scan_type", "full"),
                "detection_rules": [v.get("rule_id") for v in violations if v.get("rule_id")]
            }
        }
        
        return alert_data
    
    def _determine_severity(self, violation: Dict[str, Any]) -> str:
        """确定告警严重级别"""
        confidence = violation.get("confidence", 0)
        violation_type = violation.get("type", "").lower()
        
        # 根据违规类型和置信度确定严重级别
        if "illegal" in violation_type or "criminal" in violation_type:
            return "critical"
        elif confidence >= 0.9:
            return "critical"
        elif confidence >= 0.8:
            return "high"
        elif confidence >= 0.7:
            return "medium"
        else:
            return "low"
    
    def _determine_priority(self, severity: str, confidence: float) -> int:
        """确定告警优先级 (1-5, 1最高)"""
        if severity == "critical":
            return 1
        elif severity == "high":
            return 2
        elif severity == "medium":
            return 3
        else:
            return 4
    
    def _generate_tags(self, scan_result: Dict[str, Any], violations: list) -> list:
        """生成告警标签"""
        tags = ["website-scanner", "content-violation"]
        
        # 添加域名标签
        domain = scan_result.get("domain")
        if domain:
            tags.append(f"domain:{domain}")
        
        # 添加违规类型标签
        violation_types = set(v.get("type") for v in violations if v.get("type"))
        for vtype in violation_types:
            tags.append(f"violation:{vtype}")
        
        # 添加扫描类型标签
        scan_type = scan_result.get("scan_type")
        if scan_type:
            tags.append(f"scan-type:{scan_type}")
        
        return tags
    
    async def _create_alert(self, alert_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """创建告警"""
        try:
            response = await self.alert_client.post("/alerts", json_data=alert_data)
            return response
        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return None
    
    async def update_alert_status(self, alert_id: str, status: str, 
                                 resolution_notes: str = None) -> bool:
        """更新告警状态"""
        try:
            update_data = {"status": status}
            if resolution_notes:
                update_data["resolution_notes"] = resolution_notes
            
            await self.alert_client.put(f"/alerts/{alert_id}", json_data=update_data)
            return True
        except Exception as e:
            logger.error(f"Failed to update alert {alert_id}: {e}")
            return False
    
    async def get_alert_statistics(self) -> Dict[str, Any]:
        """获取告警统计信息"""
        try:
            response = await self.alert_client.get("/alerts/statistics/overview")
            return response
        except Exception as e:
            logger.error(f"Failed to get alert statistics: {e}")
            return {}
    
    async def batch_process_scan_results(self, scan_results: list) -> Dict[str, Any]:
        """批量处理扫描结果"""
        results = {
            "processed": 0,
            "alerts_created": 0,
            "errors": 0,
            "alert_ids": []
        }
        
        for scan_result in scan_results:
            try:
                alert_response = await self.process_scan_result(scan_result)
                results["processed"] += 1
                
                if alert_response:
                    results["alerts_created"] += 1
                    results["alert_ids"].append(alert_response.get("id"))
                    
            except Exception as e:
                logger.error(f"Error processing scan result {scan_result.get('id')}: {e}")
                results["errors"] += 1
        
        return results
    
    async def health_check(self) -> Dict[str, Any]:
        """健康检查"""
        try:
            alert_service_healthy = await self.alert_client.health_check()
            config_service_healthy = await self.config_client.health_check()
            
            return {
                "alert_integration_enabled": self.alert_enabled,
                "alert_service_healthy": alert_service_healthy,
                "config_service_healthy": config_service_healthy,
                "alert_threshold": self.alert_threshold,
                "status": "healthy" if alert_service_healthy and config_service_healthy else "unhealthy"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "status": "error",
                "error": str(e)
            }


# 全局实例
alert_integration = AlertIntegration()


# 便捷函数
async def process_scan_for_alerts(scan_result: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """处理扫描结果并创建告警的便捷函数"""
    return await alert_integration.process_scan_result(scan_result)


async def initialize_alert_integration():
    """初始化告警集成的便捷函数"""
    await alert_integration.initialize()