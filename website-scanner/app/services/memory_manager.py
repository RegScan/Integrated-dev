"""
内存管理器服务
"""

import asyncio
import gc
import psutil
import time
import logging
from typing import List, Dict, Optional, Set
from datetime import datetime, timedelta
from contextlib import asynccontextmanager

from ..core.config import settings
from ..database import redis_client

logger = logging.getLogger(__name__)

class MemoryManager:
    """内存管理器 - 防止OOM和内存泄漏"""
    
    def __init__(self):
        self.process = psutil.Process()
        self.active_browsers: Set = set()
        self.browser_lock = asyncio.Lock()
        self.memory_history: List[Dict] = []
        self.last_cleanup_time = time.time()
        self.cleanup_interval = settings.CLEANUP_INTERVAL
        self.memory_threshold = settings.MEMORY_MAX_PERCENT
        self.max_browsers = settings.MAX_CONCURRENT_SCANS
        
        # 注意：在模块级别不创建异步任务，会在main.py的lifespan中启动
        # asyncio.create_task(self._periodic_cleanup_task())  # 移除自动任务创建
    
    async def get_memory_usage(self) -> float:
        """获取当前内存使用率"""
        return self.process.memory_percent()
    
    async def check_memory_safe(self) -> bool:
        """检查内存是否安全"""
        memory_usage = await self.get_memory_usage()
        return memory_usage < self.memory_threshold
    
    async def force_gc(self):
        """强制垃圾回收"""
        before_memory = self.process.memory_info().rss
        collected = gc.collect()
        after_memory = self.process.memory_info().rss
        freed_memory = before_memory - after_memory
        
        logger.info(f"强制垃圾回收完成，回收对象: {collected}, 释放内存: {freed_memory / 1024 / 1024:.2f}MB")
        
        # 记录到Redis
        await self._record_memory_event("gc", {
            "collected_objects": collected,
            "freed_memory_mb": freed_memory / 1024 / 1024
        })
    
    async def wait_for_memory(self, timeout: int = 30) -> bool:
        """等待内存释放"""
        start_time = time.time()
        
        while not await self.check_memory_safe() and (time.time() - start_time) < timeout:
            await self.force_gc()
            await asyncio.sleep(2)
        
        if not await self.check_memory_safe():
            logger.warning(f"内存使用率过高: {await self.get_memory_usage():.1f}%")
            return False
        
        return True
    
    @asynccontextmanager
    async def get_browser_instance(self):
        """获取浏览器实例的上下文管理器"""
        browser = None
        try:
            # 检查内存是否安全
            if not await self.check_memory_safe():
                if not await self.wait_for_memory():
                    raise MemoryError(f"内存使用率过高: {await self.get_memory_usage():.1f}%")
            
            # 获取浏览器实例
            async with self.browser_lock:
                if len(self.active_browsers) >= self.max_browsers:
                    # 清理一些浏览器实例
                    await self._cleanup_old_browsers()
                
                browser = await self._create_browser_instance()
                self.active_browsers.add(browser)
                logger.info(f"创建浏览器实例，当前活跃实例数: {len(self.active_browsers)}")
            
            yield browser
            
        except Exception as e:
            logger.error(f"浏览器实例操作失败: {e}")
            raise
        finally:
            if browser:
                await self._release_browser_instance(browser)
    
    async def _create_browser_instance(self):
        """创建浏览器实例"""
        from playwright.async_api import async_playwright
        
        playwright = await async_playwright().start()
        browser = await playwright.chromium.launch(
            headless=True,
            args=[
                f"--max_old_space_size={settings.BROWSER_MAX_MEMORY_MB}",
                "--disable-dev-shm-usage",
                "--no-sandbox",
                "--disable-setuid-sandbox"
            ]
        )
        
        return browser
    
    async def _release_browser_instance(self, browser):
        """释放浏览器实例"""
        try:
            async with self.browser_lock:
                if browser in self.active_browsers:
                    self.active_browsers.remove(browser)
                
                await browser.close()
                logger.info(f"释放浏览器实例，当前活跃实例数: {len(self.active_browsers)}")
                
        except Exception as e:
            logger.error(f"释放浏览器实例失败: {e}")
    
    def get_active_browsers(self) -> Set:
        """获取活跃浏览器实例"""
        return self.active_browsers.copy()
    
    async def cleanup_browsers(self):
        """清理所有浏览器实例"""
        async with self.browser_lock:
            for browser in list(self.active_browsers):
                try:
                    await browser.close()
                except Exception as e:
                    logger.error(f"清理浏览器实例失败: {e}")
            
            self.active_browsers.clear()
            logger.info("所有浏览器实例已清理")
    
    async def _cleanup_old_browsers(self):
        """清理旧的浏览器实例"""
        if len(self.active_browsers) > self.max_browsers // 2:
            # 清理一半的实例
            browsers_to_remove = list(self.active_browsers)[:len(self.active_browsers) // 2]
            for browser in browsers_to_remove:
                await self._release_browser_instance(browser)
    
    async def _memory_monitoring_task(self):
        """内存监控任务"""
        while True:
            try:
                memory_usage = await self.get_memory_usage()
                
                # 记录内存使用历史
                await self._record_memory_usage(memory_usage)
                
                # 检查内存状态
                if memory_usage > self.memory_threshold:
                    await self._handle_memory_warning(memory_usage)
                
                # 检查是否需要紧急清理
                if memory_usage > 90:
                    await self._handle_memory_emergency(memory_usage)
                
                await asyncio.sleep(settings.MEMORY_CHECK_INTERVAL)
                
            except Exception as e:
                logger.error(f"内存监控任务失败: {e}")
                await asyncio.sleep(10)
    
    async def _periodic_cleanup_task(self):
        """定期清理任务"""
        while True:
            try:
                current_time = time.time()
                
                if current_time - self.last_cleanup_time > self.cleanup_interval:
                    await self._perform_cleanup()
                    self.last_cleanup_time = current_time
                
                await asyncio.sleep(60)  # 每分钟检查一次
                
            except Exception as e:
                logger.error(f"定期清理任务失败: {e}")
                await asyncio.sleep(60)
    
    async def _perform_cleanup(self):
        """执行清理操作"""
        logger.info("开始定期内存清理")
        
        # 强制垃圾回收
        await self.force_gc()
        
        # 清理浏览器实例
        await self._cleanup_old_browsers()
        
        # 清理Redis缓存
        await self._cleanup_redis_cache()
        
        # 清理内存历史记录
        await self._cleanup_memory_history()
        
        logger.info("定期内存清理完成")
    
    async def _cleanup_redis_cache(self):
        """清理Redis缓存"""
        try:
            # 获取缓存大小
            cache_size = await redis_client.dbsize()
            
            if cache_size > 1000:  # 如果缓存项超过1000个
                # 删除过期的缓存
                await redis_client.eval("""
                    local keys = redis.call('keys', 'cache:*')
                    local deleted = 0
                    for i, key in ipairs(keys) do
                        if redis.call('ttl', key) == -1 then
                            redis.call('del', key)
                            deleted = deleted + 1
                        end
                    end
                    return deleted
                """, 0)
                
                logger.info(f"清理Redis缓存，删除过期项")
        
        except Exception as e:
            logger.error(f"清理Redis缓存失败: {e}")
    
    async def _cleanup_memory_history(self):
        """清理内存历史记录"""
        # 只保留最近24小时的数据
        cutoff_time = time.time() - 24 * 3600
        self.memory_history = [
            record for record in self.memory_history
            if record['timestamp'] > cutoff_time
        ]
    
    async def _handle_memory_warning(self, memory_usage: float):
        """处理内存警告"""
        logger.warning(f"内存使用率警告: {memory_usage:.1f}%")
        
        # 记录告警
        await self._record_alert("warning", f"内存使用率过高: {memory_usage:.1f}%")
        
        # 执行轻度清理
        await self.force_gc()
        await self._cleanup_old_browsers()
    
    async def _handle_memory_emergency(self, memory_usage: float):
        """处理内存紧急情况"""
        logger.critical(f"内存使用率紧急: {memory_usage:.1f}%")
        
        # 记录紧急告警
        await self._record_alert("emergency", f"内存使用率紧急: {memory_usage:.1f}%")
        
        # 执行紧急清理
        await self.cleanup_browsers()
        await self.force_gc()
        await redis_client.flushdb()
    
    async def _record_memory_usage(self, memory_usage: float):
        """记录内存使用情况"""
        record = {
            'timestamp': time.time(),
            'memory_usage': memory_usage,
            'browser_count': len(self.active_browsers)
        }
        
        self.memory_history.append(record)
        
        # 保存到Redis
        await redis_client.hmset(
            f"memory:trend:{int(time.time())}",
            record
        )
        
        # 设置过期时间（24小时）
        await redis_client.expire(f"memory:trend:{int(time.time())}", 24 * 3600)
    
    async def _record_memory_event(self, event_type: str, data: Dict):
        """记录内存事件"""
        event = {
            'timestamp': time.time(),
            'type': event_type,
            'data': data
        }
        
        await redis_client.hmset(
            f"memory:event:{int(time.time())}",
            event
        )
    
    async def _record_alert(self, level: str, message: str):
        """记录告警"""
        alert = {
            'timestamp': time.time(),
            'service': 'website-scanner',
            'level': level,
            'message': message,
            'resolved': 'false'
        }
        
        await redis_client.hmset(
            f"memory:alert:{int(time.time())}",
            alert
        )
    
    def update_config(self, config: Dict):
        """更新配置"""
        if 'memory_threshold' in config:
            self.memory_threshold = config['memory_threshold']
        if 'cleanup_interval' in config:
            self.cleanup_interval = config['cleanup_interval']
        if 'max_concurrent' in config:
            self.max_browsers = config['max_concurrent']
        
        logger.info(f"内存管理器配置已更新: {config}")
    
    async def get_memory_stats(self) -> Dict:
        """获取内存统计信息"""
        memory_usage = await self.get_memory_usage()
        memory_info = self.process.memory_info()
        
        return {
            'memory_usage_percent': memory_usage,
            'memory_usage_mb': memory_info.rss / 1024 / 1024,
            'active_browsers': len(self.active_browsers),
            'max_browsers': self.max_browsers,
            'memory_threshold': self.memory_threshold,
            'last_cleanup': self.last_cleanup_time,
            'history_count': len(self.memory_history)
        } 