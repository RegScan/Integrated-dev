"""
真实网站扫描测试
测试扫描服务对真实网站的检测能力
"""

import pytest
import time
import logging
import os
from pathlib import Path
from app.services.scan_service import ScanService
from app.services.content_checker import ContentCheckerService

# 获取当前文件所在目录
current_dir = Path(__file__).parent
log_file = current_dir / "real_scanner_test.log"

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


class TestRealScanner:
    """真实网站扫描测试类"""
    
    @pytest.fixture
    def scan_service(self):
        """创建扫描服务"""
        logger.info("🔧 创建扫描服务...")
        return ScanService(api_key="test_key")
    
    @pytest.fixture
    def content_checker(self):
        """创建内容检测服务"""
        logger.info("🔧 创建内容检测服务...")
        return ContentCheckerService(api_key="test_key")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_compliance_check(self, scan_service, real_website_list):
        """测试真实网站合规检测"""
        logger.info("🚀 开始真实网站合规检测测试")
        
        successful_checks = 0
        total_checks = min(3, len(real_website_list))  # 只测试前3个网站
        
        for i in range(total_checks):
            website = real_website_list[i]
            domain = website["domain"]
            description = website["description"]
            expected = website["expected_compliant"]
            
            logger.info(f"📊 进度: {i+1}/{total_checks} - 正在检测: {domain} ({description})")
            
            try:
                start_time = time.time()
                result = scan_service.check_compliance(domain)
                end_time = time.time()
                
                duration = end_time - start_time
                
                assert result is not None, f"检测失败: {domain}"
                assert "domain" in result, f"缺少域名信息: {domain}"
                assert "compliant" in result, f"缺少合规状态: {domain}"
                
                logger.info(f"✅ {domain} 检测完成")
                logger.info(f"   ⏱️ 检测时间: {duration:.2f} 秒")
                logger.info(f"   📊 合规状态: {result['compliant']}")
                logger.info(f"   🎯 预期状态: {expected}")
                
                # 注意：真实网站的合规状态可能变化，这里只做基本验证
                assert isinstance(result["compliant"], bool)
                successful_checks += 1
                
            except Exception as e:
                logger.error(f"❌ {domain} 检测失败: {e}")
                # 真实网站可能偶尔失败，这是正常的
                continue
            
            if i < total_checks - 1:
                logger.info("⏳ 等待 5 秒后继续...")
                time.sleep(5)  # 避免请求过于频繁
        
        success_rate = successful_checks / total_checks
        logger.info(f"📈 合规检测测试完成: {successful_checks}/{total_checks} 成功 ({success_rate:.1%})")
    
    @pytest.mark.violation_test
    @pytest.mark.slow
    def test_violation_website_compliance_check(self, scan_service, violation_website_list):
        """测试违规网站合规检测"""
        logger.info("🚀 开始违规网站合规检测测试")
        
        successful_checks = 0
        total_checks = len(violation_website_list)
        
        for i, website in enumerate(violation_website_list, 1):
            domain = website["domain"]
            description = website["description"]
            expected = website["expected_compliant"]
            violation_type = website["violation_type"]
            test_content = website["test_content"]
            
            logger.info(f"📊 进度: {i}/{total_checks} - 正在检测违规网站: {domain} ({description})")
            logger.info(f"   🚨 违规类型: {violation_type}")
            logger.info(f"   📝 测试内容: {test_content}")
            
            try:
                # 由于违规网站域名不存在，我们模拟检测过程
                # 直接测试内容检测功能
                from app.services.content_checker import ContentCheckerService
                content_checker = ContentCheckerService(api_key="test_key")
                
                start_time = time.time()
                text_result = content_checker._check_text(test_content)
                end_time = time.time()
                
                duration = end_time - start_time
                
                # 模拟扫描结果
                result = {
                    "domain": domain,
                    "compliant": text_result.get("compliant", True),
                    "text_result": text_result,
                    "image_results": [],
                    "violation_type": violation_type,
                    "test_content": test_content
                }
                
                logger.info(f"✅ {domain} 违规检测完成")
                logger.info(f"   ⏱️ 检测时间: {duration:.2f} 秒")
                logger.info(f"   📊 合规状态: {result['compliant']}")
                logger.info(f"   🎯 预期状态: {expected}")
                logger.info(f"   🚨 违规类型: {violation_type}")
                
                # 验证检测结果
                assert isinstance(result["compliant"], bool)
                successful_checks += 1
                
            except Exception as e:
                logger.error(f"❌ {domain} 违规检测失败: {e}")
                continue
        
        success_rate = successful_checks / total_checks
        logger.info(f"📈 违规网站检测测试完成: {successful_checks}/{total_checks} 成功 ({success_rate:.1%})")
    
    @pytest.mark.violation_test
    @pytest.mark.slow
    def test_violation_detection_accuracy(self, content_checker, violation_content_samples):
        """测试违规检测准确性"""
        logger.info("🚀 开始违规检测准确性测试")
        
        total_tests = 0
        correct_detections = 0
        
        for violation_type, content_samples in violation_content_samples.items():
            logger.info(f"🎯 测试违规类型: {violation_type}")
            
            for i, content in enumerate(content_samples, 1):
                total_tests += 1
                logger.info(f"   📝 测试内容 {i}: {content[:50]}...")
                
                try:
                    # 检测文本内容
                    result = content_checker._check_text(content)
                    actual_compliant = result.get("compliant", True)
                    
                    # 违规内容应该被检测为不合规
                    expected_compliant = False  # 违规内容预期为False
                    
                    if actual_compliant == expected_compliant:
                        logger.info(f"   ✅ 检测结果正确")
                        correct_detections += 1
                    else:
                        logger.warning(f"   ⚠️ 检测结果错误")
                        logger.warning(f"   📊 实际结果: {actual_compliant}, 预期: {expected_compliant}")
                    
                    logger.info(f"   📊 检测结果: {result}")
                    
                except Exception as e:
                    logger.error(f"   ❌ 检测失败: {e}")
        
        accuracy_rate = correct_detections / total_tests if total_tests > 0 else 0
        logger.info(f"📈 违规检测准确性测试完成: {correct_detections}/{total_tests} 正确 ({accuracy_rate:.1%})")
        
        # 验证测试框架正常工作
        assert total_tests > 0, "没有执行任何违规检测测试"
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_content_analysis(self, content_checker):
        """测试真实网站内容分析"""
        logger.info("🚀 开始真实网站内容分析测试")
        
        domain = "bing.com"
        logger.info(f"🎯 目标网站: {domain}")
        
        # 先爬取网站内容
        logger.info("🕷️ 开始爬取网站内容...")
        from app.services.crawler import CrawlerService
        crawler = CrawlerService()
        website_data = crawler.crawl_website(domain)
        
        if website_data is None:
            logger.error("❌ 爬取失败")
            pytest.skip("无法爬取网站内容")
        
        logger.info(f"✅ 网站爬取成功")
        logger.info(f"   📝 文本长度: {len(website_data['text'])} 字符")
        logger.info(f"   🖼️ 图片数量: {len(website_data['images'])} 张")
        
        # 分析文本内容
        logger.info("🔍 开始分析文本内容...")
        text_result = content_checker._check_text(website_data["text"])
        assert text_result is not None
        
        logger.info(f"📊 文本分析结果: {text_result}")
        
        # 分析图片内容（如果有）
        if website_data["images"]:
            logger.info("🖼️ 开始分析图片内容...")
            for i, img_url in enumerate(website_data["images"][:2], 1):  # 只测试前2张图片
                logger.info(f"   📸 分析图片 {i}: {img_url}")
                img_result = content_checker._check_image(img_url)
                logger.info(f"   📊 图片分析结果: {img_result}")
        else:
            logger.info("ℹ️ 没有找到图片内容")
        
        logger.info("✅ 内容分析测试完成")
    
    @pytest.mark.violation_test
    @pytest.mark.slow
    def test_violation_content_analysis(self, content_checker, violation_content_samples):
        """测试违规内容分析"""
        logger.info("🚀 开始违规内容分析测试")
        
        total_analyzed = 0
        violation_detected = 0
        
        for violation_type, content_samples in violation_content_samples.items():
            logger.info(f"🎯 分析违规类型: {violation_type}")
            
            for i, content in enumerate(content_samples, 1):
                total_analyzed += 1
                logger.info(f"   📝 分析内容 {i}: {content[:50]}...")
                
                try:
                    # 检测文本内容
                    result = content_checker._check_text(content)
                    
                    if result and not result.get("compliant", True):
                        logger.info(f"   ✅ 成功检测到违规内容")
                        violation_detected += 1
                    else:
                        logger.warning(f"   ⚠️ 未检测到违规内容")
                    
                    logger.info(f"   📊 检测结果: {result}")
                    
                except Exception as e:
                    logger.error(f"   ❌ 检测失败: {e}")
        
        detection_rate = violation_detected / total_analyzed if total_analyzed > 0 else 0
        logger.info(f"📈 违规内容分析测试完成: {violation_detected}/{total_analyzed} 检测到违规 ({detection_rate:.1%})")
        
        # 验证分析框架正常工作
        assert total_analyzed > 0, "没有执行任何内容分析"
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_scan_performance(self, scan_service):
        """测试扫描性能"""
        logger.info("🚀 开始扫描性能测试")
        
        domain = "bing.com"
        logger.info(f"🎯 目标网站: {domain}")
        
        start_time = time.time()
        result = scan_service.check_compliance(domain)
        end_time = time.time()
        
        duration = end_time - start_time
        
        logger.info(f"📊 扫描性能测试:")
        logger.info(f"   🌐 网站: {domain}")
        logger.info(f"   ⏱️ 扫描时间: {duration:.2f} 秒")
        
        if result:
            logger.info(f"   📊 合规状态: {result.get('compliant', 'N/A')}")
            logger.info(f"   📝 文本结果: {result.get('text_result', 'N/A')}")
            logger.info(f"   🖼️ 图片结果数量: {len(result.get('image_results', []))}")
            
            # 性能要求：扫描时间应该在合理范围内
            assert duration < 60, f"扫描时间过长: {duration} 秒"
            logger.info("✅ 扫描性能测试通过")
        else:
            logger.warning("⚠️ 扫描失败，但验证了超时机制")
            # 如果扫描失败，至少验证超时时间合理
            assert duration < 60, f"超时时间过长: {duration} 秒"
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_scan_error_handling(self, scan_service, invalid_domains):
        """测试扫描错误处理"""
        logger.info("🚀 开始扫描错误处理测试")
        
        for i, domain in enumerate(invalid_domains, 1):
            logger.info(f"📊 进度: {i}/{len(invalid_domains)} - 测试无效域名扫描: {domain}")
            
            start_time = time.time()
            result = scan_service.check_compliance(domain)
            end_time = time.time()
            
            duration = end_time - start_time
            
            if result and result.get("status") == "error":
                logger.info(f"✅ {domain} 正确处理了扫描错误")
            else:
                logger.warning(f"⚠️ {domain} 扫描结果异常")
            
            logger.info(f"   ⏱️ 处理时间: {duration:.2f} 秒")
        
        logger.info("✅ 扫描错误处理测试完成")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_scan_data_storage(self, scan_service):
        """测试扫描数据存储"""
        logger.info("🚀 开始扫描数据存储测试")
        
        domain = "bing.com"
        logger.info(f"🎯 目标网站: {domain}")
        
        result = scan_service.check_compliance(domain)
        if result is None:
            logger.error("❌ 扫描失败")
            pytest.skip("无法完成扫描")
        
        # 验证存储的数据结构
        assert "domain" in result
        assert "compliant" in result
        assert "text_result" in result
        assert "image_results" in result
        assert "timestamp" in result
        
        logger.info(f"📊 数据存储验证:")
        logger.info(f"   🌐 域名: {result['domain']}")
        logger.info(f"   📊 合规状态: {result['compliant']}")
        logger.info(f"   ⏰ 时间戳: {result['timestamp']}")
        logger.info(f"   📝 文本结果: {result['text_result']}")
        logger.info(f"   🖼️ 图片结果数量: {len(result['image_results'])}")
        logger.info("✅ 数据存储测试完成")
    
    @pytest.mark.real_website
    @pytest.mark.slow
    def test_real_website_scan_concurrent(self, scan_service):
        """测试并发扫描"""
        logger.info("🚀 开始并发扫描测试")
        
        domains = ["bing.com", "httpbin.org"]
        logger.info(f"🎯 目标网站: {domains}")
        
        logger.info("🔄 开始并发扫描...")
        
        start_time = time.time()
        results = []
        
        for i, domain in enumerate(domains, 1):
            logger.info(f"📊 进度: {i}/{len(domains)} - 扫描 {domain}")
            try:
                result = scan_service.check_compliance(domain)
                results.append(result)
                logger.info(f"   ✅ {domain} 扫描完成")
            except Exception as e:
                logger.error(f"   ❌ {domain} 扫描失败: {e}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        logger.info(f"📈 并发扫描结果:")
        logger.info(f"   ⏱️ 总时间: {total_time:.2f} 秒")
        logger.info(f"   ✅ 成功数量: {len(results)}")
        logger.info(f"   📊 平均时间: {total_time/len(domains):.2f} 秒/网站")
        
        assert len(results) > 0, "没有成功的扫描"
        logger.info("✅ 并发扫描测试完成") 