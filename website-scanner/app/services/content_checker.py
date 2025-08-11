import requests
import re
import logging
from typing import Dict, List, Optional
from ..core.config import settings

logger = logging.getLogger(__name__)

class ContentCheckerService:
    def __init__(self):
        # 百度AI内容审核API配置
        self.baidu_api_key = getattr(settings, "BAIDU_API_KEY", "")
        self.baidu_secret_key = getattr(settings, "BAIDU_SECRET_KEY", "")
        self.baidu_access_token = None
        
        # 阿里云内容安全API配置
        self.aliyun_access_key = getattr(settings, "ALIYUN_ACCESS_KEY", "")
        self.aliyun_secret_key = getattr(settings, "ALIYUN_SECRET_KEY", "")
        self.aliyun_region = getattr(settings, "ALIYUN_REGION", "cn-shanghai")
        
        # 本地敏感词库（作为降级策略）
        self.sensitive_keywords = {
            "gambling": ["赌博", "博彩", "赌场", "老虎机", "百家乐", "轮盘", "扑克", "骰子", "投注", "开奖"],
            "porn": ["成人", "色情", "情色", "裸体", "性爱", "成人内容", "成人娱乐"],
            "violence": ["暴力", "血腥", "恐怖", "杀人", "武器", "管制刀具", "仿真枪械"],
            "drugs": ["毒品", "大麻", "冰毒", "摇头丸", "可卡因", "违禁药物", "种植技术"],
            "political": ["反动", "颠覆", "政治敏感", "非法组织", "颠覆国家政权"]
        }
        
        # 初始化百度AI访问令牌
        if self.baidu_api_key and self.baidu_secret_key:
            self._init_baidu_token()

    def _init_baidu_token(self):
        """初始化百度AI访问令牌"""
        try:
            url = f"https://aip.baidubce.com/oauth/2.0/token?grant_type=client_credentials&client_id={self.baidu_api_key}&client_secret={self.baidu_secret_key}"
            response = requests.post(url, timeout=10)
            if response.status_code == 200:
                data = response.json()
                self.baidu_access_token = data.get("access_token")
                logger.info("百度AI访问令牌获取成功")
            else:
                logger.warning("百度AI访问令牌获取失败")
        except Exception as e:
            logger.error(f"百度AI访问令牌获取异常: {e}")

    def check_content_safety(self, text: str, images: List[str] = None) -> Dict:
        """
        检查内容安全性（文本+图片）
        
        Args:
            text: 文本内容
            images: 图片URL列表
            
        Returns:
            检测结果字典
        """
        try:
            # 1. 文本内容检测
            text_result = self._check_text(text)
            
            # 2. 图片内容检测
            image_results = []
            if images:
                for img_url in images[:3]:  # 限制图片数量
                    if img_url.startswith("http"):
                        img_result = self._check_image(img_url)
                        image_results.append(img_result)
            
            # 3. 综合评估
            is_compliant = all([
                text_result.get("compliant", False),
                all([r.get("compliant", False) for r in image_results])
            ])
            
            # 4. 汇总结果
            result = {
                "compliant": is_compliant,
                "text_result": text_result,
                "image_results": image_results,
                "overall_confidence": self._calculate_confidence(text_result, image_results),
                "detection_method": "multi_api_with_fallback"
            }
            
            logger.info(f"内容检测完成，合规性: {is_compliant}")
            return result
            
        except Exception as e:
            logger.error(f"内容检测异常: {e}")
            return self._create_fallback_result(text, images, str(e))

    def _check_text(self, text: str) -> Dict:
        """文本内容检测（优先使用百度AI，失败时使用本地检测）"""
        # 1. 尝试百度AI API
        if self.baidu_access_token:
            result = self._check_text_baidu(text)
            if result:
                return result
        
        # 2. 尝试阿里云API
        if self.aliyun_access_key:
            result = self._check_text_aliyun(text)
            if result:
                return result
        
        # 3. 降级到本地检测
        return self._local_text_check(text, "所有API调用失败")

    def _check_text_baidu(self, text: str) -> Optional[Dict]:
        """使用百度AI检测文本"""
        try:
            if not self.baidu_access_token:
                return None
                
            url = f"https://aip.baidubce.com/rest/2.0/solution/v1/text_censor/v2/user_defined?access_token={self.baidu_access_token}"
            
            payload = {
                "text": text[:1000]  # 限制文本长度
            }
            
            response = requests.post(url, data=payload, timeout=10)
            if response.status_code == 200:
                data = response.json()
                
                # 解析百度AI响应
                if "conclusion" in data:
                    conclusion = data["conclusion"]
                    is_compliant = conclusion in ["合规", "疑似", "审核中"]
                    
                    return {
                        "compliant": is_compliant,
                        "method": "baidu_ai",
                        "confidence": 0.9,
                        "raw_response": data,
                        "violations": [] if is_compliant else [{"type": "baidu_detected", "confidence": 0.9}]
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"百度AI文本检测失败: {e}")
            return None

    def _check_text_aliyun(self, text: str) -> Optional[Dict]:
        """使用阿里云检测文本"""
        try:
            if not self.aliyun_access_key:
                return None
                
            # 这里需要根据阿里云SDK进行实际集成
            # 暂时返回None，表示未实现
            return None
            
        except Exception as e:
            logger.error(f"阿里云文本检测失败: {e}")
            return None

    def _check_image(self, image_url: str) -> Dict:
        """图片内容检测（优先使用百度AI，失败时使用本地检测）"""
        # 1. 尝试百度AI API
        if self.baidu_access_token:
            result = self._check_image_baidu(image_url)
            if result:
                return result
        
        # 2. 降级到本地检测
        return self._local_image_check(image_url, "图片检测API调用失败")

    def _check_image_baidu(self, image_url: str) -> Optional[Dict]:
        """使用百度AI检测图片"""
        try:
            if not self.baidu_access_token:
                return None
                
            url = f"https://aip.baidubce.com/rest/2.0/solution/v1/img_censor/v2/user_defined?access_token={self.baidu_access_token}"
            
            payload = {
                "imgUrl": image_url
            }
            
            response = requests.post(url, data=payload, timeout=15)
            if response.status_code == 200:
                data = response.json()
                
                # 解析百度AI响应
                if "conclusion" in data:
                    conclusion = data["conclusion"]
                    is_compliant = conclusion in ["合规", "疑似", "审核中"]
                    
                    return {
                        "compliant": is_compliant,
                        "method": "baidu_ai",
                        "confidence": 0.9,
                        "raw_response": data,
                        "violations": [] if is_compliant else [{"type": "baidu_detected", "confidence": 0.9}]
                    }
            
            return None
            
        except Exception as e:
            logger.error(f"百度AI图片检测失败: {e}")
            return None

    def _local_text_check(self, text: str, error_msg: str) -> Dict:
        """本地文本内容检测（降级策略）"""
        detected_violations = []
        
        # 检查各种违规类型
        for violation_type, keywords in self.sensitive_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    detected_violations.append({
                        "type": violation_type,
                        "keyword": keyword,
                        "confidence": 0.8
                    })
                    break  # 找到一种违规类型就停止
        
        if detected_violations:
            return {
                "compliant": False,
                "violations": detected_violations,
                "method": "local_detection",
                "api_error": error_msg,
                "confidence": 0.7
            }
        else:
            return {
                "compliant": True,
                "method": "local_detection",
                "api_error": error_msg,
                "confidence": 0.6
            }

    def _local_image_check(self, image_url: str, error_msg: str) -> Dict:
        """本地图片内容检测（降级策略）"""
        # 简单的图片URL检查
        suspicious_patterns = [
            r"gambling", r"porn", r"violence", r"drugs", r"weapon",
            r"adult", r"sex", r"nude", r"blood", r"gun"
        ]
        
        detected_violations = []
        for pattern in suspicious_patterns:
            if re.search(pattern, image_url, re.IGNORECASE):
                detected_violations.append({
                    "type": "suspicious_url",
                    "pattern": pattern,
                    "confidence": 0.6
                })
        
        if detected_violations:
            return {
                "compliant": False,
                "violations": detected_violations,
                "method": "local_detection",
                "api_error": error_msg,
                "confidence": 0.6
            }
        else:
            return {
                "compliant": True,
                "method": "local_detection",
                "api_error": error_msg,
                "confidence": 0.5
            }

    def _calculate_confidence(self, text_result: Dict, image_results: List[Dict]) -> float:
        """计算整体置信度"""
        confidences = [text_result.get("confidence", 0.5)]
        confidences.extend([r.get("confidence", 0.5) for r in image_results])
        
        if not confidences:
            return 0.5
            
        return sum(confidences) / len(confidences)

    def _create_fallback_result(self, text: str, images: List[str], error_msg: str) -> Dict:
        """创建降级结果"""
        return {
            "compliant": False,
            "text_result": {"compliant": False, "method": "fallback", "error": error_msg},
            "image_results": [],
            "overall_confidence": 0.3,
            "detection_method": "fallback",
            "error": error_msg
        }