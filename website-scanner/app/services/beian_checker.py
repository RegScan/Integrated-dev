import asyncio
import aiohttp
import re
import logging
from typing import Dict, Optional, List, Any
from urllib.parse import urlparse
from datetime import datetime, timedelta
import json
from ..core.config import settings
from ..utils.cache import cache_manager
from ..utils.http_client import HttpClient

logger = logging.getLogger(__name__)


class BeianChecker:
    """
    网站备案信息查询服务
    """
    
    def __init__(self):
        self.http_client = HttpClient()
        self.cache_ttl = 24 * 60 * 60  # 缓存24小时
        
        # 备案查询API配置
        self.beian_apis = {
            # 工信部备案查询接口（示例）
            'miit': {
                'url': 'https://beian.miit.gov.cn/api/query',
                'headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            },
            # 第三方备案查询接口（示例）
            'third_party': {
                'url': 'https://api.beian-query.com/v1/query',
                'headers': {
                    'Authorization': f'Bearer {getattr(settings, "BEIAN_API_KEY", "")}'
                }
            }
        }
        
        # 备案号正则表达式
        self.beian_patterns = [
            r'([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]ICP备\d+号)',
            r'([京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领]ICP证\d+号)',
            r'(\d+号)',  # 简化的备案号格式
        ]
    
    async def check_website_beian(self, url: str) -> Dict[str, Any]:
        """
        检查网站备案信息
        
        Args:
            url: 网站URL
            
        Returns:
            备案信息字典
        """
        try:
            # 解析域名
            domain = self._extract_domain(url)
            if not domain:
                return self._create_beian_result(url, False, "无效的URL")
            
            # 检查缓存
            cache_key = f"beian:{domain}"
            cached_result = await cache_manager.get(cache_key)
            if cached_result:
                logger.info(f"从缓存获取备案信息: {domain}")
                return json.loads(cached_result)
            
            # 执行备案查询
            beian_info = await self._query_beian_info(domain)
            
            # 从网站页面提取备案号
            page_beian = await self._extract_beian_from_page(url)
            
            # 合并结果
            result = self._merge_beian_results(url, domain, beian_info, page_beian)
            
            # 缓存结果
            await cache_manager.set(cache_key, json.dumps(result), self.cache_ttl)
            
            return result
            
        except Exception as e:
            logger.error(f"备案查询失败 {url}: {str(e)}")
            return self._create_beian_result(url, False, f"查询失败: {str(e)}")
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """
        从URL中提取域名
        """
        try:
            if not url.startswith(('http://', 'https://')):
                url = 'http://' + url
            
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            
            # 移除端口号
            if ':' in domain:
                domain = domain.split(':')[0]
            
            # 移除www前缀
            if domain.startswith('www.'):
                domain = domain[4:]
            
            return domain if domain else None
            
        except Exception as e:
            logger.error(f"域名提取失败 {url}: {str(e)}")
            return None
    
    async def _query_beian_info(self, domain: str) -> Dict[str, Any]:
        """
        通过API查询备案信息
        """
        beian_info = {
            'found': False,
            'beian_number': None,
            'company_name': None,
            'beian_type': None,
            'issue_date': None,
            'source': None
        }
        
        # 尝试多个API源
        for api_name, api_config in self.beian_apis.items():
            try:
                result = await self._query_single_api(domain, api_name, api_config)
                if result and result.get('found'):
                    beian_info.update(result)
                    beian_info['source'] = api_name
                    break
                    
            except Exception as e:
                logger.warning(f"API {api_name} 查询失败: {str(e)}")
                continue
        
        return beian_info
    
    async def _query_single_api(self, domain: str, api_name: str, api_config: Dict) -> Optional[Dict]:
        """
        查询单个API
        """
        try:
            if api_name == 'miit':
                return await self._query_miit_api(domain, api_config)
            elif api_name == 'third_party':
                return await self._query_third_party_api(domain, api_config)
            else:
                return None
                
        except Exception as e:
            logger.error(f"API {api_name} 查询异常: {str(e)}")
            return None
    
    async def _query_miit_api(self, domain: str, api_config: Dict) -> Optional[Dict]:
        """
        查询工信部API（示例实现）
        """
        try:
            # 这里是示例实现，实际需要根据真实API调整
            params = {
                'domain': domain,
                'type': 'domain'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    api_config['url'],
                    params=params,
                    headers=api_config['headers'],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_miit_response(data)
                    else:
                        logger.warning(f"工信部API返回状态码: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"工信部API查询失败: {str(e)}")
            return None
    
    async def _query_third_party_api(self, domain: str, api_config: Dict) -> Optional[Dict]:
        """
        查询第三方API（示例实现）
        """
        try:
            payload = {
                'domain': domain,
                'query_type': 'beian'
            }
            
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    api_config['url'],
                    json=payload,
                    headers=api_config['headers'],
                    timeout=aiohttp.ClientTimeout(total=10)
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        return self._parse_third_party_response(data)
                    else:
                        logger.warning(f"第三方API返回状态码: {response.status}")
                        return None
                        
        except Exception as e:
            logger.error(f"第三方API查询失败: {str(e)}")
            return None
    
    def _parse_miit_response(self, data: Dict) -> Optional[Dict]:
        """
        解析工信部API响应
        """
        try:
            if data.get('success') and data.get('data'):
                beian_data = data['data']
                return {
                    'found': True,
                    'beian_number': beian_data.get('beian_number'),
                    'company_name': beian_data.get('company_name'),
                    'beian_type': beian_data.get('beian_type', 'ICP备案'),
                    'issue_date': beian_data.get('issue_date')
                }
            return None
            
        except Exception as e:
            logger.error(f"解析工信部响应失败: {str(e)}")
            return None
    
    def _parse_third_party_response(self, data: Dict) -> Optional[Dict]:
        """
        解析第三方API响应
        """
        try:
            if data.get('code') == 0 and data.get('result'):
                result = data['result']
                return {
                    'found': True,
                    'beian_number': result.get('icp_number'),
                    'company_name': result.get('company'),
                    'beian_type': result.get('type', 'ICP备案'),
                    'issue_date': result.get('date')
                }
            return None
            
        except Exception as e:
            logger.error(f"解析第三方响应失败: {str(e)}")
            return None
    
    async def _extract_beian_from_page(self, url: str) -> Dict[str, Any]:
        """
        从网站页面提取备案号
        """
        try:
            # 获取网站首页内容
            response = await self.http_client.get(url, timeout=10)
            if not response or response.status_code != 200:
                return {'found': False}
            
            html_content = response.text
            
            # 使用正则表达式提取备案号
            for pattern in self.beian_patterns:
                matches = re.findall(pattern, html_content, re.IGNORECASE)
                if matches:
                    beian_number = matches[0]
                    return {
                        'found': True,
                        'beian_number': beian_number,
                        'source': 'page_extraction'
                    }
            
            return {'found': False}
            
        except Exception as e:
            logger.error(f"页面备案号提取失败 {url}: {str(e)}")
            return {'found': False}
    
    def _merge_beian_results(self, url: str, domain: str, api_result: Dict, page_result: Dict) -> Dict[str, Any]:
        """
        合并备案查询结果
        """
        # 优先使用API查询结果
        if api_result.get('found'):
            main_result = api_result
            secondary_result = page_result
        elif page_result.get('found'):
            main_result = page_result
            secondary_result = api_result
        else:
            # 都没有找到备案信息
            return self._create_beian_result(url, False, "未找到备案信息")
        
        # 构建最终结果
        result = {
            'url': url,
            'domain': domain,
            'has_beian': True,
            'beian_number': main_result.get('beian_number'),
            'company_name': main_result.get('company_name'),
            'beian_type': main_result.get('beian_type', 'ICP备案'),
            'issue_date': main_result.get('issue_date'),
            'query_source': main_result.get('source', 'unknown'),
            'verification_status': 'verified' if api_result.get('found') else 'extracted',
            'check_time': datetime.now().isoformat(),
            'additional_info': {
                'api_found': api_result.get('found', False),
                'page_found': page_result.get('found', False)
            }
        }
        
        # 验证备案号格式
        if result['beian_number']:
            result['beian_valid'] = self._validate_beian_number(result['beian_number'])
        else:
            result['beian_valid'] = False
        
        return result
    
    def _validate_beian_number(self, beian_number: str) -> bool:
        """
        验证备案号格式
        """
        try:
            # 基本格式验证
            for pattern in self.beian_patterns:
                if re.match(pattern, beian_number):
                    return True
            return False
            
        except Exception:
            return False
    
    def _create_beian_result(self, url: str, has_beian: bool, message: str = "") -> Dict[str, Any]:
        """
        创建备案查询结果
        """
        domain = self._extract_domain(url)
        return {
            'url': url,
            'domain': domain,
            'has_beian': has_beian,
            'beian_number': None,
            'company_name': None,
            'beian_type': None,
            'issue_date': None,
            'query_source': None,
            'verification_status': 'failed' if not has_beian else 'unknown',
            'beian_valid': False,
            'check_time': datetime.now().isoformat(),
            'message': message,
            'additional_info': {
                'api_found': False,
                'page_found': False
            }
        }
    
    async def batch_check_beian(self, urls: List[str]) -> List[Dict[str, Any]]:
        """
        批量检查备案信息
        """
        try:
            # 并发查询，限制并发数
            semaphore = asyncio.Semaphore(5)  # 最多5个并发
            
            async def check_single(url):
                async with semaphore:
                    return await self.check_website_beian(url)
            
            tasks = [check_single(url) for url in urls]
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # 处理异常结果
            final_results = []
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    final_results.append(
                        self._create_beian_result(urls[i], False, f"查询异常: {str(result)}")
                    )
                else:
                    final_results.append(result)
            
            return final_results
            
        except Exception as e:
            logger.error(f"批量备案查询失败: {str(e)}")
            return [self._create_beian_result(url, False, "批量查询失败") for url in urls]
    
    async def get_beian_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        获取备案统计信息
        """
        try:
            total_count = len(results)
            beian_count = sum(1 for r in results if r.get('has_beian'))
            valid_count = sum(1 for r in results if r.get('beian_valid'))
            
            # 按备案类型统计
            type_stats = {}
            for result in results:
                if result.get('has_beian') and result.get('beian_type'):
                    beian_type = result['beian_type']
                    type_stats[beian_type] = type_stats.get(beian_type, 0) + 1
            
            # 按查询来源统计
            source_stats = {}
            for result in results:
                if result.get('has_beian') and result.get('query_source'):
                    source = result['query_source']
                    source_stats[source] = source_stats.get(source, 0) + 1
            
            return {
                'total_checked': total_count,
                'has_beian': beian_count,
                'valid_beian': valid_count,
                'beian_rate': round(beian_count / total_count * 100, 2) if total_count > 0 else 0,
                'valid_rate': round(valid_count / beian_count * 100, 2) if beian_count > 0 else 0,
                'type_distribution': type_stats,
                'source_distribution': source_stats,
                'check_time': datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"备案统计计算失败: {str(e)}")
            return {
                'total_checked': 0,
                'has_beian': 0,
                'valid_beian': 0,
                'beian_rate': 0,
                'valid_rate': 0,
                'type_distribution': {},
                'source_distribution': {},
                'error': str(e)
            }


# 创建全局实例
beian_checker = BeianChecker()