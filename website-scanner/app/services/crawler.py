"""
爬虫服务
负责网站内容爬取（性能优化版本 + OOM防护）
"""

import time
import logging
import asyncio
import psutil
import gc
from typing import Optional, Dict, List
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError
from concurrent.futures import ThreadPoolExecutor
import aiohttp
from functools import lru_cache
from contextlib import asynccontextmanager

from ..database import cache_result, monitor_performance, redis_client, CacheKeys
from ..core.config import settings, get_crawler_config, get_browser_config

# 配置日志
logger = logging.getLogger(__name__)

class MemoryManager:
    """内存管理器 - OOM防护"""
    
    def __init__(self, max_memory_percent: float = 80.0):
        self.max_memory_percent = max_memory_percent
        self.process = psutil.Process()
    
    def get_memory_usage(self) -> float:
        """获取当前内存使用率"""
        return self.process.memory_percent()
    
    def check_memory_safe(self) -> bool:
        """检查内存是否安全"""
        return self.get_memory_usage() < self.max_memory_percent
    
    def force_gc(self):
        """强制垃圾回收"""
        gc.collect()
        logger.info(f"强制垃圾回收完成，当前内存使用: {self.get_memory_usage():.1f}%")
    
    async def wait_for_memory(self, timeout: int = 30):
        """等待内存释放"""
        start_time = time.time()
        while not self.check_memory_safe() and (time.time() - start_time) < timeout:
            self.force_gc()
            await asyncio.sleep(2)
        
        if not self.check_memory_safe():
            raise MemoryError(f"内存使用率过高: {self.get_memory_usage():.1f}%")

class AsyncCrawlerService:
    """异步爬虫服务（性能优化版本 + OOM防护）"""
    
    def __init__(self):
        self.crawler_config = get_crawler_config()
        self.browser_config = get_browser_config()
        # 根据内存情况动态调整并发数
        self.max_concurrent = min(settings.MAX_CONCURRENT_SCANS, 5)  # 降低默认并发数
        self.semaphore = asyncio.Semaphore(self.max_concurrent)
        self.executor = ThreadPoolExecutor(max_workers=self.max_concurrent)
        self.memory_manager = MemoryManager()
        self.browser_pool = []  # 浏览器实例池
        self.browser_pool_lock = asyncio.Lock()
    
    @asynccontextmanager
    async def get_browser_instance(self):
        """获取浏览器实例（带内存管理）"""
        # 检查内存使用
        if not self.memory_manager.check_memory_safe():
            await self.memory_manager.wait_for_memory()
        
        browser = None
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(
                    headless=self.browser_config["headless"],
                    args=[
                        '--no-sandbox',
                        '--disable-dev-shm-usage',
                        '--disable-gpu',
                        '--disable-web-security',
                        '--disable-features=VizDisplayCompositor',
                        '--disable-blink-features=AutomationControlled',
                        '--disable-extensions',
                        '--disable-background-timer-throttling',
                        '--disable-backgrounding-occluded-windows',
                        '--disable-renderer-backgrounding',
                        '--memory-pressure-off',  # 减少内存压力
                        '--max_old_space_size=512',  # 限制V8内存使用
                        '--disable-javascript',  # 可选：禁用JS减少内存
                        '--disable-images',  # 可选：禁用图片加载
                        '--disable-css'  # 可选：禁用CSS
                    ]
                )
                yield browser
        except Exception as e:
            logger.error(f"浏览器启动失败: {e}")
            raise
        finally:
            if browser:
                try:
                    await browser.close()
                except Exception as e:
                    logger.warning(f"浏览器关闭失败: {e}")
            # 强制垃圾回收
            self.memory_manager.force_gc()
    
    @monitor_performance("crawl_website")
    @cache_result(ttl=settings.CACHE_SCAN_RESULT_TTL, key_prefix="crawler")
    async def crawl_website(self, domain: str, max_pages: int = 10) -> Optional[Dict]:
        """异步爬取网站内容（OOM防护版本）"""
        async with self.semaphore:  # 限制并发数
            for attempt in range(self.crawler_config["retry_times"] + 1):
                try:
                    # 检查内存使用
                    if not self.memory_manager.check_memory_safe():
                        logger.warning(f"内存使用率过高: {self.memory_manager.get_memory_usage():.1f}%，等待内存释放")
                        await self.memory_manager.wait_for_memory()
                    
                    async with self.get_browser_instance() as browser:
                        page = await browser.new_page()
                        
                        # 设置视口和用户代理
                        await page.set_viewport_size(self.browser_config["viewport_size"])
                        await page.set_extra_http_headers({
                            "User-Agent": self.crawler_config["user_agent"],
                            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
                            "Accept-Language": "en-US,en;q=0.5",
                            "Accept-Encoding": "gzip, deflate",
                            "Connection": "keep-alive",
                            "Upgrade-Insecure-Requests": "1"
                        })
                        
                        try:
                            # 构建URL
                            url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
                            
                            logger.info(f"正在访问: {url}")
                            
                            # 异步访问页面
                            await page.goto(
                                url, 
                                timeout=self.browser_config["timeout"],
                                wait_until="domcontentloaded"
                            )
                            
                            # 等待页面稳定
                            await asyncio.sleep(2)
                            
                            # 异步滚动页面以加载懒加载内容
                            try:
                                await page.evaluate("window.scrollTo(0, document.body.scrollHeight)")
                                await asyncio.sleep(1)
                                await page.evaluate("window.scrollTo(0, 0)")
                                await asyncio.sleep(1)
                            except:
                                pass
                            
                            # 异步提取内容
                            text_content = await self._extract_text_content_async(page)
                            image_urls = await self._extract_images_async(page)
                            title = await page.title()
                            
                            # 验证内容质量
                            if not text_content or len(text_content.strip()) == 0:
                                logger.warning(f"⚠️ {domain} 文本内容为空，尝试备用方法")
                                text_content = await page.inner_text("body")
                                text_content = text_content[:5000]  # 限制文本长度防止内存溢出
                            
                            # 限制图片数量防止内存溢出
                            image_urls = image_urls[:self.browser_config.get("max_images", 5)]
                            
                            result = {
                                "domain": domain,
                                "url": url,
                                "title": title,
                                "text": text_content[:10000],  # 限制文本长度
                                "images": image_urls,
                                "timestamp": time.time(),
                                "status": "success"
                            }
                            
                            logger.info(f"✅ {domain} 爬取成功")
                            return result
                            
                        except PlaywrightTimeoutError as e:
                            logger.warning(f"⏰ {domain} 超时 (尝试 {attempt + 1}/{self.crawler_config['retry_times'] + 1}): {e}")
                            if attempt == self.crawler_config["retry_times"]:
                                logger.error(f"❌ {domain} 最终超时失败")
                                return None
                            await asyncio.sleep(self.crawler_config["retry_delay"])
                            
                        except Exception as e:
                            logger.error(f"❌ {domain} 爬取失败 (尝试 {attempt + 1}/{self.crawler_config['retry_times'] + 1}): {e}")
                            if attempt == self.crawler_config["retry_times"]:
                                return None
                            await asyncio.sleep(self.crawler_config["retry_delay"])
                            
                        finally:
                            try:
                                await page.close()
                            except Exception as e:
                                logger.warning(f"页面关闭失败: {e}")
                            
                except MemoryError as e:
                    logger.error(f"❌ 内存不足，无法处理 {domain}: {e}")
                    self.memory_manager.force_gc()
                    await asyncio.sleep(5)  # 等待内存释放
                    return None
                except Exception as e:
                    logger.error(f"❌ 浏览器启动失败: {domain}, 错误: {e}")
                    if attempt == self.crawler_config["retry_times"]:
                        return None
                    await asyncio.sleep(self.crawler_config["retry_delay"])
            
            return None
    
    async def _extract_text_content_async(self, page) -> str:
        """异步智能提取文本内容"""
        try:
            # 尝试多种选择器来提取文本
            selectors = [
                "body",
                "main",
                "article",
                "div[role='main']",
                ".content",
                "#content",
                ".main-content"
            ]
            
            text_content = ""
            for selector in selectors:
                try:
                    element = await page.query_selector(selector)
                    if element:
                        text = await element.inner_text()
                        if text and len(text.strip()) > 0:
                            text_content = text
                            break
                except:
                    continue
            
            # 如果所有选择器都失败，尝试获取整个页面的文本
            if not text_content:
                text_content = await page.inner_text("body")
            
            # 如果还是空的，尝试获取可见文本
            if not text_content or len(text_content.strip()) == 0:
                text_content = await page.evaluate("""
                    () => {
                        const walker = document.createTreeWalker(
                            document.body,
                            NodeFilter.SHOW_TEXT,
                            null,
                            false
                        );
                        let text = '';
                        let node;
                        while (node = walker.nextNode()) {
                            const style = window.getComputedStyle(node.parentElement);
                            if (style.display !== 'none' && style.visibility !== 'hidden') {
                                text += node.textContent + ' ';
                            }
                        }
                        return text.trim();
                    }
                """)
            
            return text_content.strip()
            
        except Exception as e:
            logger.error(f"文本提取失败: {e}")
            return ""
    
    async def _extract_images_async(self, page) -> list:
        """异步提取图片URL"""
        try:
            image_elements = await page.query_selector_all("img")
            image_urls = []
            
            for img in image_elements:
                try:
                    src = await img.get_attribute("src")
                    if src:
                        # 处理相对URL
                        if src.startswith("//"):
                            src = "https:" + src
                        elif src.startswith("/"):
                            src = page.url + src
                        elif not src.startswith(("http://", "https://")):
                            src = page.url + "/" + src
                        
                        if src.startswith(("http://", "https://")):
                            image_urls.append(src)
                except:
                    continue
            
            return image_urls
            
        except Exception as e:
            logger.error(f"图片提取失败: {e}")
            return []
    
    async def crawl_websites_batch(self, domains: List[str]) -> List[Dict]:
        """并发爬取多个网站"""
        tasks = []
        for domain in domains:
            task = self.crawl_website(domain)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # 处理结果
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"爬取失败 {domains[i]}: {result}")
                processed_results.append({
                    "domain": domains[i],
                    "status": "error",
                    "error": str(result)
                })
            elif result:
                processed_results.append({
                    "domain": domains[i],
                    "status": "success",
                    "data": result
                })
            else:
                processed_results.append({
                    "domain": domains[i],
                    "status": "failed",
                    "error": "爬取失败"
                })
        
        return processed_results
    
    @monitor_performance("crawl_with_fallback")
    async def crawl_with_fallback(self, domain: str) -> Optional[Dict]:
        """带降级策略的异步爬取方法"""
        # 首先尝试完整爬取
        result = await self.crawl_website(domain)
        if result and result.get("text"):
            return result
        
        # 如果失败，尝试简化版本
        try:
            async with async_playwright() as p:
                browser = await p.chromium.launch(headless=True)
                page = await browser.new_page()
                
                try:
                    url = f"https://{domain}" if not domain.startswith(('http://', 'https://')) else domain
                    await page.goto(url, timeout=15000, wait_until="load")
                    
                    # 简化内容提取
                    text_content = await self._extract_text_content_async(page)
                    if not text_content:
                        text_content = await page.inner_text("body")
                        text_content = text_content[:1000]  # 限制文本长度
                    
                    return {
                        "text": text_content,
                        "images": [],
                        "url": url,
                        "title": await page.title(),
                        "fallback": True
                    }
                    
                except Exception as e:
                    logger.error(f"降级爬取也失败: {domain}, 错误: {e}")
                    return None
                finally:
                    await browser.close()
                    
        except Exception as e:
            logger.error(f"降级浏览器启动失败: {domain}, 错误: {e}")
            return None

class CrawlerService:
    """同步爬虫服务（保持向后兼容）"""
    
    def __init__(self, timeout: int = 30000, retry_count: int = 2):
        self.timeout = timeout
        self.retry_count = retry_count
        self.async_crawler = AsyncCrawlerService()
    
    def crawl_website(self, domain: str, max_pages: int = 10) -> Optional[Dict]:
        """同步爬取网站内容（调用异步版本）"""
        return asyncio.run(self.async_crawler.crawl_website(domain, max_pages))
    
    def crawl_with_fallback(self, domain: str) -> Optional[Dict]:
        """同步降级爬取（调用异步版本）"""
        return asyncio.run(self.async_crawler.crawl_with_fallback(domain))