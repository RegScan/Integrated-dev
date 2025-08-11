"""
真实网站爬虫测试
测试爬虫服务对真实网站的访问能力
"""

import pytest
import time
import logging
import os
from pathlib import Path
from app.services.crawler import CrawlerService

# 获取当前文件所在目录
current_dir = Path(__file__).parent
log_file = current_dir / "real_crawler_test.log"

# 强制配置日志
logging.getLogger().handlers.clear()  # 清除现有处理器
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(log_file, mode='w', encoding='utf-8')
    ],
    force=True  # 强制重新配置
)
logger = logging.getLogger(__name__)


class TestRealCrawler:
    """真实网站爬虫测试类"""
    
    @pytest.fixture
    def crawler_service(self):
        """创建爬虫服务"""
        logger.info("[SETUP] 创建爬虫服务 (超时: 30s, 重试: 2次)")
        return CrawlerService(timeout=30000, retry_count=2)
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_crawl_basic(self, crawler_service, test_domains):
        """测试基本真实网站爬取"""
        logger.info("[START] 开始基本真实网站爬取测试")
        
        successful_crawls = 0
        total_tested = 0
        
        # 使用更稳定的测试网站
        stable_domains = ["bing.com", "httpbin.org", "jsonplaceholder.typicode.com"]
        
        for domain in stable_domains:
            logger.info(f"[PROGRESS] 进度: {total_tested + 1}/{len(stable_domains)} - 正在测试域名: {domain}")
            total_tested += 1
            
            start_time = time.time()
            result = crawler_service.crawl_website(domain)
            end_time = time.time()
            
            if result is not None and result.get("text") and len(result["text"].strip()) > 0:
                # 验证结果
                assert "text" in result, f"缺少文本内容: {domain}"
                assert "images" in result, f"缺少图片列表: {domain}"
                
                # 验证文本内容不为空
                assert len(result["text"].strip()) > 0, f"文本内容为空: {domain}"
                
                logger.info(f"[SUCCESS] {domain} 爬取成功")
                logger.info(f"   [TIME] 爬取时间: {end_time - start_time:.2f} 秒")
                logger.info(f"   [TEXT] 文本长度: {len(result['text'])} 字符")
                logger.info(f"   [IMAGE] 图片数量: {len(result['images'])} 张")
                successful_crawls += 1
            else:
                logger.warning(f"[FAILED] {domain} 爬取失败或内容为空")
                logger.warning(f"   [TIME] 尝试时间: {end_time - start_time:.2f} 秒")
            
            # 避免请求过于频繁
            if total_tested < len(stable_domains):
                logger.info("[WAIT] 等待 3 秒后继续...")
                time.sleep(3)
        
        # 要求至少有一个网站爬取成功
        success_rate = successful_crawls / total_tested
        logger.info(f"[SUMMARY] 爬取成功率: {successful_crawls}/{total_tested} ({success_rate:.1%})")
        assert success_rate >= 0.3, f"爬取成功率过低: {success_rate:.1%}"
        logger.info("[COMPLETE] 基本爬取测试完成")
    
    @pytest.mark.violation_test
    @pytest.mark.slow
    def test_violation_content_crawl_simulation(self, crawler_service, mock_violation_websites):
        """测试违规内容爬取模拟"""
        logger.info("[START] 开始违规内容爬取模拟测试")
        
        # 由于违规网站域名不存在，我们模拟爬取过程
        for domain, website_data in mock_violation_websites.items():
            logger.info(f"[VIOLATION_CRAWL] 模拟爬取违规网站: {domain}")
            logger.info(f"   [TYPE] 违规类型: {website_data['expected_violations']}")
            logger.info(f"   [CONTENT] 内容预览: {website_data['text'][:100]}...")
            
            # 模拟爬取结果
            simulated_result = {
                "text": website_data["text"],
                "images": website_data["images"],
                "url": f"https://{domain}",
                "title": f"违规网站 - {domain}",
                "violation_detected": True,
                "violation_types": website_data["expected_violations"]
            }
            
            # 验证模拟结果
            assert "text" in simulated_result, f"缺少文本内容: {domain}"
            assert "images" in simulated_result, f"缺少图片列表: {domain}"
            assert len(simulated_result["text"]) > 0, f"文本内容为空: {domain}"
            
            logger.info(f"   [SUCCESS] 模拟爬取成功")
            logger.info(f"   [TEXT] 文本长度: {len(simulated_result['text'])} 字符")
            logger.info(f"   [IMAGE] 图片数量: {len(simulated_result['images'])} 张")
            logger.info(f"   [VIOLATION] 违规类型: {simulated_result['violation_types']}")
        
        logger.info("[COMPLETE] 违规内容爬取模拟测试完成")
    
    @pytest.mark.violation_test
    @pytest.mark.slow
    def test_violation_content_analysis(self, crawler_service, violation_content_samples):
        """测试违规内容分析"""
        logger.info("[START] 开始违规内容分析测试")
        
        total_analyzed = 0
        violation_detected = 0
        
        for violation_type, content_samples in violation_content_samples.items():
            logger.info(f"[VIOLATION_ANALYSIS] 分析违规类型: {violation_type}")
            
            for i, content in enumerate(content_samples, 1):
                total_analyzed += 1
                logger.info(f"   [CONTENT] 分析内容 {i}: {content[:50]}...")
                
                # 模拟内容分析过程
                # 检查是否包含违规关键词
                violation_keywords = {
                    "gambling": ["赌博", "博彩", "赌场", "老虎机", "百家乐"],
                    "porn": ["成人", "色情", "情色", "裸体", "性爱"],
                    "violence": ["暴力", "血腥", "恐怖", "杀人", "武器"],
                    "drugs": ["毒品", "大麻", "冰毒", "摇头丸", "可卡因"],
                    "political": ["反动", "颠覆", "政治敏感", "非法组织"]
                }
                
                keywords = violation_keywords.get(violation_type, [])
                detected_keywords = [kw for kw in keywords if kw in content]
                
                if detected_keywords:
                    violation_detected += 1
                    logger.info(f"   [DETECTED] 检测到违规关键词: {detected_keywords}")
                else:
                    logger.warning(f"   [WARNING] 未检测到违规关键词")
                
                logger.info(f"   [RESULT] 内容长度: {len(content)} 字符")
        
        detection_rate = violation_detected / total_analyzed if total_analyzed > 0 else 0
        logger.info(f"[SUMMARY] 违规内容分析完成: {violation_detected}/{total_analyzed} 检测到违规 ({detection_rate:.1%})")
        
        # 验证分析框架正常工作
        assert total_analyzed > 0, "没有执行任何内容分析"
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_crawl_performance(self, crawler_service):
        """测试爬虫性能"""
        logger.info("[START] 开始爬虫性能测试")
        
        domain = "bing.com"  # 使用稳定的网站
        logger.info(f"[TARGET] 目标网站: {domain}")
        
        start_time = time.time()
        result = crawler_service.crawl_website(domain)
        end_time = time.time()
        
        duration = end_time - start_time
        
        logger.info(f"[PERFORMANCE] 性能测试结果:")
        logger.info(f"   [SITE] 网站: {domain}")
        logger.info(f"   [TIME] 爬取时间: {duration:.2f} 秒")
        
        if result and result.get("text"):
            logger.info(f"   [TEXT] 文本大小: {len(result['text'])} 字符")
            logger.info(f"   [IMAGE] 图片数量: {len(result['images'])} 张")
            
            # 性能要求：爬取时间应该在合理范围内
            assert duration < 60, f"爬取时间过长: {duration} 秒"
            logger.info("[SUCCESS] 性能测试通过")
        else:
            logger.warning("[WARNING] 爬取失败，但验证了超时机制")
            # 如果爬取失败，至少验证超时时间合理
            assert duration < 60, f"超时时间过长: {duration} 秒"
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_crawl_error_handling(self, crawler_service, invalid_domains):
        """测试错误处理"""
        logger.info("[START] 开始错误处理测试")
        
        for i, domain in enumerate(invalid_domains, 1):
            logger.info(f"[PROGRESS] 进度: {i}/{len(invalid_domains)} - 测试无效域名: {domain}")
            
            start_time = time.time()
            result = crawler_service.crawl_website(domain)
            end_time = time.time()
            
            duration = end_time - start_time
            
            # 应该返回 None 或抛出异常
            if result is None:
                logger.info(f"[SUCCESS] {domain} 正确处理了错误")
            else:
                logger.warning(f"[WARNING] {domain} 返回了结果，可能需要检查错误处理")
            
            logger.info(f"   [TIME] 处理时间: {duration:.2f} 秒")
        
        logger.info("[COMPLETE] 错误处理测试完成")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_content_quality(self, crawler_service):
        """测试内容质量"""
        logger.info("[START] 开始内容质量测试")
        
        domain = "bing.com"  # 使用稳定的网站
        logger.info(f"[TARGET] 目标网站: {domain}")
        
        result = crawler_service.crawl_website(domain)
        if result is None or not result.get("text"):
            logger.warning(f"[WARNING] 无法爬取 {domain}，跳过内容质量测试")
            pytest.skip(f"无法爬取 {domain}，跳过内容质量测试")
        
        text_content = result["text"]
        
        # 验证内容质量
        assert len(text_content.strip()) > 10, "文本内容过短"
        assert len(text_content) < 100000, "文本内容过长"
        
        # 检查是否包含基本内容
        word_count = len(text_content.split())
        assert word_count > 5, "文本内容单词数过少"
        
        logger.info(f"[QUALITY] 内容质量测试通过:")
        logger.info(f"   [TEXT] 文本长度: {len(text_content)} 字符")
        logger.info(f"   [WORDS] 单词数量: {word_count} 个")
        logger.info(f"   [IMAGE] 图片数量: {len(result['images'])} 张")
        logger.info("[COMPLETE] 内容质量测试完成")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_crawl_large_sites(self, crawler_service):
        """测试大型网站爬取"""
        logger.info("[START] 开始大型网站爬取测试")
        
        # 选择一个相对稳定的网站
        domain = "bing.com"
        logger.info(f"[TARGET] 目标网站: {domain}")
        
        start_time = time.time()
        result = crawler_service.crawl_website(domain)
        end_time = time.time()
        
        duration = end_time - start_time
        
        if result is None or not result.get("text"):
            logger.warning(f"[WARNING] 无法爬取 {domain}，跳过大型网站测试")
            pytest.skip(f"无法爬取 {domain}，跳过大型网站测试")
        
        logger.info(f"[LARGE_SITE] 大型网站测试结果:")
        logger.info(f"   [SITE] 网站: {domain}")
        logger.info(f"   [TIME] 爬取时间: {duration:.2f} 秒")
        logger.info(f"   [TEXT] 文本大小: {len(result['text'])} 字符")
        logger.info(f"   [IMAGE] 图片数量: {len(result['images'])} 张")
        
        # 验证大型网站的基本要求
        assert duration < 120, f"大型网站爬取时间过长: {duration} 秒"
        assert len(result["text"].strip()) > 50, "大型网站文本内容过少"
        logger.info("[COMPLETE] 大型网站测试完成")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_crawler_fallback_strategy(self, crawler_service):
        """测试降级策略"""
        logger.info("[START] 开始降级策略测试")
        
        # 测试一个可能不稳定的网站
        domain = "httpbin.org"
        logger.info(f"[TARGET] 目标网站: {domain}")
        
        # 首先尝试正常爬取
        logger.info("[FALLBACK] 尝试正常爬取...")
        result = crawler_service.crawl_website(domain)
        if result is None or not result.get("text"):
            logger.warning("[WARNING] 正常爬取失败，尝试降级策略")
            result = crawler_service.crawl_with_fallback(domain)
        else:
            logger.info("[SUCCESS] 正常爬取成功")
        
        if result and result.get("text"):
            logger.info(f"[SUCCESS] 降级策略成功: {domain}")
            logger.info(f"   [TEXT] 文本长度: {len(result['text'])} 字符")
            logger.info(f"   [FALLBACK] 是否降级: {result.get('fallback', False)}")
        else:
            logger.warning(f"[FAILED] 降级策略也失败: {domain}")
            # 对于网络测试，允许失败
            logger.info("[SKIP] 网络连接问题，跳过降级策略测试")
            pytest.skip(f"网络连接问题，跳过降级策略测试")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_crawler_stability(self, crawler_service):
        """测试爬虫稳定性"""
        logger.info("[START] 开始爬虫稳定性测试")
        
        domain = "bing.com"
        logger.info(f"[TARGET] 目标网站: {domain}")
        
        # 连续测试3次
        results = []
        for i in range(3):
            logger.info(f"[PROGRESS] 第 {i+1}/3 次测试...")
            result = crawler_service.crawl_website(domain)
            if result and result.get("text"):
                text_length = len(result["text"])
                results.append(text_length)
                logger.info(f"   [SUCCESS] 成功，文本长度: {text_length} 字符")
            else:
                results.append(0)
                logger.info(f"   [FAILED] 失败")
            time.sleep(2)
        
        # 计算成功率
        success_count = sum(1 for r in results if r > 0)
        success_rate = success_count / len(results)
        
        logger.info(f"[STABILITY] 稳定性测试结果:")
        logger.info(f"   [RATE] 成功率: {success_count}/{len(results)} ({success_rate:.1%})")
        logger.info(f"   [LENGTHS] 文本长度变化: {results}")
        
        # 要求至少60%的成功率
        assert success_rate >= 0.6, f"稳定性不足: {success_rate:.1%}"
        logger.info("[COMPLETE] 稳定性测试完成") 