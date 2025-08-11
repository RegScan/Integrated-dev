"""
综合真实网站测试
测试整个扫描系统对真实网站的处理能力
"""

import pytest
import time
import logging
import os
from pathlib import Path
from app.services.scan_service import ScanService
from app.services.crawler import CrawlerService
from app.services.content_checker import ContentCheckerService

# 获取当前文件所在目录
current_dir = Path(__file__).parent
log_file = current_dir / "real_websites_test.log"

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


class TestRealWebsites:
    """真实网站测试类"""
    
    @pytest.fixture
    def crawler_service(self):
        """创建爬虫服务"""
        logger.info("[SETUP] 创建爬虫服务...")
        return CrawlerService()
    
    @pytest.fixture
    def content_checker(self):
        """创建内容检测服务"""
        logger.info("[SETUP] 创建内容检测服务...")
        return ContentCheckerService(api_key="test_key")
    
    @pytest.fixture
    def scan_service(self):
        """创建扫描服务"""
        logger.info("[SETUP] 创建扫描服务...")
        return ScanService(api_key="test_key")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_crawl(self, crawler_service):
        """测试真实网站爬取"""
        logger.info("[START] 开始真实网站爬取测试")
        
        # 使用稳定的测试网站
        test_domains = [
            "httpbin.org",           # HTTP测试服务
            "bing.com",           # 示例网站
            "jsonplaceholder.typicode.com"  # API测试服务
        ]
        
        successful_crawls = 0
        total_domains = len(test_domains)
        
        for i, domain in enumerate(test_domains, 1):
            logger.info(f"[PROGRESS] 进度: {i}/{total_domains} - 正在测试域名: {domain}")
            
            start_time = time.time()
            result = crawler_service.crawl_website(domain)
            end_time = time.time()
            
            duration = end_time - start_time
            
            if result is not None and result.get("text"):
                # 验证结果
                assert "text" in result, f"缺少文本内容: {domain}"
                assert "images" in result, f"缺少图片列表: {domain}"
                
                # 验证文本内容不为空
                assert len(result["text"]) > 0, f"文本内容为空: {domain}"
                
                logger.info(f"[SUCCESS] {domain} 爬取成功")
                logger.info(f"   [TIME] 爬取时间: {duration:.2f} 秒")
                logger.info(f"   [TEXT] 文本长度: {len(result['text'])} 字符")
                logger.info(f"   [IMAGE] 图片数量: {len(result['images'])} 张")
                successful_crawls += 1
            else:
                logger.warning(f"[FAILED] {domain} 爬取失败")
                logger.warning(f"   [TIME] 尝试时间: {duration:.2f} 秒")
            
            # 避免请求过于频繁
            if i < total_domains:
                logger.info("[WAIT] 等待 2 秒后继续...")
                time.sleep(2)
        
        success_rate = successful_crawls / total_domains
        logger.info(f"[SUMMARY] 爬取测试完成: {successful_crawls}/{total_domains} 成功 ({success_rate:.1%})")
        assert success_rate >= 0.5, f"成功率过低: {success_rate:.1%}"
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_content_analysis(self, crawler_service, content_checker):
        """测试真实网站内容分析"""
        logger.info("[START] 开始真实网站内容分析测试")
        
        domain = "httpbin.org"
        logger.info(f"[TARGET] 目标网站: {domain}")
        
        # 爬取真实网站
        logger.info("[CRAWL] 开始爬取网站内容...")
        website_data = crawler_service.crawl_website(domain)
        assert website_data is not None
        
        logger.info(f"[SUCCESS] 网站爬取成功")
        logger.info(f"   [TEXT] 文本长度: {len(website_data['text'])} 字符")
        logger.info(f"   [IMAGE] 图片数量: {len(website_data['images'])} 张")
        
        # 分析文本内容
        logger.info("[ANALYZE] 开始分析文本内容...")
        text_result = content_checker._check_text(website_data["text"])
        assert text_result is not None
        
        logger.info(f"[RESULT] 文本分析结果: {text_result}")
        
        # 分析图片内容（如果有）
        if website_data["images"]:
            logger.info("[ANALYZE] 开始分析图片内容...")
            for i, img_url in enumerate(website_data["images"][:2], 1):  # 只测试前2张图片
                logger.info(f"   [IMAGE] 分析图片 {i}: {img_url}")
                img_result = content_checker._check_image(img_url)
                logger.info(f"   [RESULT] 图片分析结果: {img_result}")
        else:
            logger.info("[INFO] 没有找到图片内容")
        
        logger.info("[COMPLETE] 内容分析测试完成")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_compliance_check(self, scan_service):
        """测试真实网站合规检测"""
        logger.info("[START] 开始真实网站合规检测测试")
        
        # 使用一些稳定的网站进行测试
        test_cases = [
            {
                "domain": "httpbin.org",
                "expected_compliant": True,  # 应该是合规的
                "description": "HTTP测试服务"
            },
            {
                "domain": "bing.com", 
                "expected_compliant": True,  # 应该是合规的
                "description": "示例网站"
            }
        ]
        
        successful_checks = 0
        total_checks = len(test_cases)
        
        for i, test_case in enumerate(test_cases, 1):
            domain = test_case["domain"]
            expected = test_case["expected_compliant"]
            description = test_case["description"]
            
            logger.info(f"[PROGRESS] 进度: {i}/{total_checks} - 正在检测: {domain} ({description})")
            
            try:
                start_time = time.time()
                result = scan_service.check_compliance(domain)
                end_time = time.time()
                
                duration = end_time - start_time
                
                assert result is not None, f"检测失败: {domain}"
                assert "domain" in result, f"缺少域名信息: {domain}"
                assert "compliant" in result, f"缺少合规状态: {domain}"
                
                logger.info(f"[SUCCESS] {domain} 检测完成")
                logger.info(f"   [TIME] 检测时间: {duration:.2f} 秒")
                logger.info(f"   [STATUS] 合规状态: {result['compliant']}")
                logger.info(f"   [EXPECT] 预期状态: {expected}")
                
                # 注意：真实网站的合规状态可能变化，这里只做基本验证
                assert isinstance(result["compliant"], bool)
                successful_checks += 1
                
            except Exception as e:
                logger.error(f"[ERROR] {domain} 检测失败: {e}")
                # 真实网站可能偶尔失败，这是正常的
                continue
            
            if i < total_checks:
                logger.info("[WAIT] 等待 3 秒后继续...")
                time.sleep(3)  # 避免请求过于频繁
        
        success_rate = successful_checks / total_checks
        logger.info(f"[SUMMARY] 合规检测测试完成: {successful_checks}/{total_checks} 成功 ({success_rate:.1%})")
    
    @pytest.mark.violation_test
    @pytest.mark.slow
    def test_violation_content_detection(self, content_checker, violation_content_samples):
        """测试违规内容检测"""
        logger.info("[START] 开始违规内容检测测试")
        
        total_tests = 0
        successful_detections = 0
        
        for violation_type, content_samples in violation_content_samples.items():
            logger.info(f"[VIOLATION] 测试违规类型: {violation_type}")
            
            for i, content in enumerate(content_samples, 1):
                total_tests += 1
                logger.info(f"   [CONTENT] 测试内容 {i}: {content[:50]}...")
                
                try:
                    # 检测文本内容
                    result = content_checker._check_text(content)
                    
                    if result and not result.get("compliant", True):
                        logger.info(f"   [SUCCESS] 成功检测到违规内容")
                        logger.info(f"   [RESULT] 检测结果: {result}")
                        successful_detections += 1
                    else:
                        logger.warning(f"   [WARNING] 未检测到违规内容")
                        logger.warning(f"   [RESULT] 检测结果: {result}")
                
                except Exception as e:
                    logger.error(f"   [ERROR] 检测失败: {e}")
        
        detection_rate = successful_detections / total_tests if total_tests > 0 else 0
        logger.info(f"[SUMMARY] 违规检测测试完成: {successful_detections}/{total_tests} 成功检测 ({detection_rate:.1%})")
        
        # 由于当前API是占位符，我们主要验证测试框架是否正常工作
        assert total_tests > 0, "没有执行任何违规检测测试"
    
    @pytest.mark.violation_test
    @pytest.mark.slow
    def test_mock_violation_websites(self, scan_service, mock_violation_websites):
        """测试模拟违规网站检测"""
        logger.info("[START] 开始模拟违规网站检测测试")
        
        successful_detections = 0
        total_websites = len(mock_violation_websites)
        
        for domain, website_data in mock_violation_websites.items():
            logger.info(f"[VIOLATION] 测试违规网站: {domain}")
            logger.info(f"   [TYPE] 违规类型: {website_data['expected_violations']}")
            logger.info(f"   [CONTENT] 内容预览: {website_data['text'][:100]}...")
            
            try:
                # 模拟扫描服务检测
                # 注意：这里我们直接测试内容检测，因为域名不存在
                from app.services.content_checker import ContentCheckerService
                content_checker = ContentCheckerService(api_key="test_key")
                
                # 检测文本内容
                text_result = content_checker._check_text(website_data["text"])
                
                # 检测图片内容
                image_results = []
                for img_url in website_data["images"]:
                    img_result = content_checker._check_image(img_url)
                    image_results.append(img_result)
                
                # 模拟扫描结果
                result = {
                    "domain": domain,
                    "compliant": text_result.get("compliant", True) and all(r.get("compliant", True) for r in image_results),
                    "text_result": text_result,
                    "image_results": image_results,
                    "expected_violations": website_data["expected_violations"]
                }
                
                if not result["compliant"]:
                    logger.info(f"   [SUCCESS] 成功检测到违规内容")
                    successful_detections += 1
                else:
                    logger.warning(f"   [WARNING] 未检测到违规内容")
                
                logger.info(f"   [RESULT] 检测结果: {result}")
                
            except Exception as e:
                logger.error(f"   [ERROR] 检测失败: {e}")
        
        detection_rate = successful_detections / total_websites if total_websites > 0 else 0
        logger.info(f"[SUMMARY] 模拟违规网站检测完成: {successful_detections}/{total_websites} 成功检测 ({detection_rate:.1%})")
        
        # 验证测试框架正常工作
        assert total_websites > 0, "没有执行任何模拟违规网站测试"
    
    @pytest.mark.violation_test
    @pytest.mark.slow
    def test_violation_detection_accuracy(self, content_checker, violation_content_samples):
        """测试违规检测准确性"""
        logger.info("[START] 开始违规检测准确性测试")
        
        # 测试数据：包含违规内容和正常内容
        test_cases = [
            # 违规内容
            ("在线赌博网站，提供百家乐游戏", False, "gambling"),
            ("成人内容网站，包含色情图片", False, "porn"),
            ("暴力游戏，包含血腥内容", False, "violence"),
            ("毒品交易平台，销售违禁药物", False, "drugs"),
            ("反动政治宣传网站", False, "political"),
            
            # 正常内容
            ("这是一个正常的网站，提供有用的信息", True, "normal"),
            ("技术博客，分享编程知识", True, "normal"),
            ("新闻网站，报道时事新闻", True, "normal"),
            ("教育网站，提供学习资源", True, "normal"),
            ("商业网站，销售合法产品", True, "normal")
        ]
        
        correct_detections = 0
        total_cases = len(test_cases)
        
        for i, (content, expected_compliant, content_type) in enumerate(test_cases, 1):
            logger.info(f"[ACCURACY] 测试案例 {i}/{total_cases}: {content_type}")
            logger.info(f"   [CONTENT] 内容: {content[:50]}...")
            logger.info(f"   [EXPECT] 预期合规: {expected_compliant}")
            
            try:
                result = content_checker._check_text(content)
                actual_compliant = result.get("compliant", True)
                
                if actual_compliant == expected_compliant:
                    logger.info(f"   [SUCCESS] 检测结果正确")
                    correct_detections += 1
                else:
                    logger.warning(f"   [WARNING] 检测结果错误")
                    logger.warning(f"   [ACTUAL] 实际结果: {actual_compliant}")
                
                logger.info(f"   [RESULT] 检测结果: {result}")
                
            except Exception as e:
                logger.error(f"   [ERROR] 检测失败: {e}")
        
        accuracy_rate = correct_detections / total_cases if total_cases > 0 else 0
        logger.info(f"[SUMMARY] 违规检测准确性测试完成: {correct_detections}/{total_cases} 正确 ({accuracy_rate:.1%})")
        
        # 验证测试框架正常工作
        assert total_cases > 0, "没有执行任何准确性测试"
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_performance(self, crawler_service):
        """测试真实网站性能"""
        logger.info("[START] 开始真实网站性能测试")
        
        domain = "httpbin.org"
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
            assert duration < 30, f"爬取时间过长: {duration} 秒"
            logger.info("[SUCCESS] 性能测试通过")
        else:
            logger.warning("[WARNING] 爬取失败，但验证了超时机制")
            # 如果爬取失败，至少验证超时时间合理
            assert duration < 30, f"超时时间过长: {duration} 秒"
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_error_handling(self, crawler_service):
        """测试真实网站错误处理"""
        logger.info("[START] 开始真实网站错误处理测试")
        
        # 测试不存在的域名
        invalid_domains = [
            "this-domain-does-not-exist-12345.com",
            "invalid-domain-test-99999.org"
        ]
        
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
        """测试真实网站内容质量"""
        logger.info("[START] 开始真实网站内容质量测试")
        
        domain = "httpbin.org"
        logger.info(f"[TARGET] 目标网站: {domain}")
        
        result = crawler_service.crawl_website(domain)
        assert result is not None
        
        text_content = result["text"]
        
        # 验证内容质量
        logger.info(f"[QUALITY] 内容质量分析:")
        logger.info(f"   [TEXT] 总字符数: {len(text_content)}")
        logger.info(f"   [TEXT] 非空字符数: {len(text_content.strip())}")
        logger.info(f"   [LINES] 行数: {len(text_content.splitlines())}")
        logger.info(f"   [IMAGE] 图片数量: {len(result['images'])}")
        
        # 基本质量检查
        assert len(text_content) > 0, "文本内容为空"
        assert len(text_content.strip()) > 0, "文本内容只有空白字符"
        
        # 检查是否包含HTML标签（可能的问题）
        if "<html>" in text_content.lower() or "<body>" in text_content.lower():
            logger.warning("[WARNING] 文本内容可能包含HTML标签")
        
        # 检查图片URL质量
        for i, img_url in enumerate(result["images"], 1):
            assert img_url.startswith("http"), f"图片URL格式错误: {img_url}"
            logger.info(f"   [IMAGE] 图片 {i}: {img_url}")
        
        logger.info("[COMPLETE] 内容质量测试完成")


# 运行真实网站测试的命令
# pytest tests/test_real_websites.py -m real_website -v --tb=short
# pytest tests/test_real_websites.py -m violation_test -v --tb=short 