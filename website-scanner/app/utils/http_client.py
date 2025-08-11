"""
HTTP客户端模块
"""

import aiohttp
import asyncio
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class HttpClient:
    """异步HTTP客户端"""
    
    def __init__(self, timeout: int = 30):
        self.timeout = timeout
        self._session = None
    
    async def _get_session(self):
        """获取aiohttp会话"""
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self.timeout)
            self._session = aiohttp.ClientSession(timeout=timeout)
        return self._session
    
    async def get(self, url: str, headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """发送GET请求"""
        try:
            session = await self._get_session()
            async with session.get(url, headers=headers) as response:
                if response.status == 200:
                    content = await response.text()
                    return {
                        "status": response.status,
                        "data": content,
                        "headers": dict(response.headers)
                    }
                else:
                    return {
                        "status": response.status,
                        "data": None,
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"HTTP GET请求失败 {url}: {e}")
            return {
                "status": 500,
                "data": None,
                "error": str(e)
            }
    
    async def post(self, url: str, data: Optional[Dict[str, Any]] = None, 
                   headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """发送POST请求"""
        try:
            session = await self._get_session()
            async with session.post(url, json=data, headers=headers) as response:
                if response.status == 200:
                    content = await response.json()
                    return {
                        "status": response.status,
                        "data": content,
                        "headers": dict(response.headers)
                    }
                else:
                    return {
                        "status": response.status,
                        "data": None,
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            logger.error(f"HTTP POST请求失败 {url}: {e}")
            return {
                "status": 500,
                "data": None,
                "error": str(e)
            }
    
    async def close(self):
        """关闭会话"""
        if self._session:
            await self._session.close()
            self._session = None