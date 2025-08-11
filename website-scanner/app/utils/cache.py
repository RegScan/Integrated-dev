"""
缓存管理模块
"""

import json
import asyncio
from typing import Optional, Any


class CacheManager:
    """缓存管理器（内存实现）"""
    
    def __init__(self):
        self._cache = {}
    
    async def get(self, key: str) -> Optional[str]:
        """获取缓存值"""
        try:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry is None or asyncio.get_event_loop().time() < expiry:
                    return value
                else:
                    del self._cache[key]
            return None
        except Exception as e:
            print(f"缓存获取失败: {e}")
            return None
    
    async def set(self, key: str, value: str, ttl: int = 3600) -> bool:
        """设置缓存值"""
        try:
            expiry = None if ttl <= 0 else asyncio.get_event_loop().time() + ttl
            self._cache[key] = (value, expiry)
            return True
        except Exception as e:
            print(f"缓存设置失败: {e}")
            return False
    
    async def delete(self, key: str) -> bool:
        """删除缓存值"""
        try:
            if key in self._cache:
                del self._cache[key]
            return True
        except Exception as e:
            print(f"缓存删除失败: {e}")
            return False
    
    async def exists(self, key: str) -> bool:
        """检查键是否存在"""
        try:
            if key in self._cache:
                value, expiry = self._cache[key]
                if expiry is None or asyncio.get_event_loop().time() < expiry:
                    return True
                else:
                    del self._cache[key]
            return False
        except Exception as e:
            print(f"缓存检查失败: {e}")
            return False


# 全局缓存管理器实例
cache_manager = CacheManager()