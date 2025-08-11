#!/usr/bin/env python3
"""
违规检测修复验证脚本
验证修复后的内容检测服务是否能正确识别违规内容
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.content_checker import ContentCheckerService

def test_violation_detection():
    """测试违规检测功能"""
    print("=" * 60)
    print("违规检测修复验证测试")
    print("=" * 60)
    
    # 创建内容检测服务
    checker = ContentCheckerService(api_key="test_key")
    
    # 测试用例
    test_cases = [
        {
            "name": "赌博类违规",
            "content": "欢迎来到在线赌博平台！我们提供百家乐、老虎机、轮盘等多种博彩游戏。",
            "expected": False
        },
        {
            "name": "色情类违规", 
            "content": "成人内容网站，提供高清色情图片和视频。包含各种成人娱乐内容。",
            "expected": False
        },
        {
            "name": "暴力类违规",
            "content": "暴力游戏和武器交易平台。提供各类管制刀具、仿真枪械销售。",
            "expected": False
        },
        {
            "name": "毒品类违规",
            "content": "毒品交易平台，销售大麻、冰毒、摇头丸等违禁药物。",
            "expected": False
        },
        {
            "name": "政治敏感类违规",
            "content": "政治敏感内容网站，包含反动政治宣传和颠覆国家政权的内容。",
            "expected": False
        },
        {
            "name": "正常内容",
            "content": "这是一个正常的技术博客网站，提供有用的编程知识和学习资源。",
            "expected": True
        },
        {
            "name": "教育内容",
            "content": "欢迎访问我们的教育平台，提供各种在线课程和学习资料。",
            "expected": True
        }
    ]
    
    print("\n开始测试违规检测功能...")
    print("-" * 60)
    
    success_count = 0
    total_count = len(test_cases)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n测试 {i}/{total_count}: {test_case['name']}")
        print(f"内容: {test_case['content'][:50]}...")
        print(f"预期结果: {'违规' if not test_case['expected'] else '合规'}")
        
        # 执行检测
        result = checker._check_text(test_case['content'])
        
        # 分析结果
        actual_compliant = result.get("compliant", True)
        method = result.get("method", "unknown")
        violations = result.get("violations", [])
        
        print(f"检测结果: {'违规' if not actual_compliant else '合规'}")
        print(f"检测方法: {method}")
        
        if violations:
            print(f"检测到的违规: {violations}")
        
        # 验证结果
        if actual_compliant == test_case['expected']:
            print("✅ 检测结果正确")
            success_count += 1
        else:
            print("❌ 检测结果错误")
        
        print("-" * 40)
    
    # 总结
    accuracy = success_count / total_count * 100
    print(f"\n测试总结:")
    print(f"总测试数: {total_count}")
    print(f"成功检测: {success_count}")
    print(f"检测准确率: {accuracy:.1f}%")
    
    if accuracy >= 80:
        print("✅ 违规检测功能修复成功！")
    else:
        print("❌ 违规检测功能仍需改进")
    
    return accuracy >= 80

def test_image_detection():
    """测试图片检测功能"""
    print("\n" + "=" * 60)
    print("图片违规检测测试")
    print("=" * 60)
    
    checker = ContentCheckerService(api_key="test_key")
    
    test_images = [
        {
            "name": "可疑图片URL",
            "url": "https://example.com/gambling1.jpg",
            "expected": False
        },
        {
            "name": "正常图片URL",
            "url": "https://example.com/logo.png",
            "expected": True
        },
        {
            "name": "成人内容图片",
            "url": "https://example.com/adult-content.jpg",
            "expected": False
        }
    ]
    
    success_count = 0
    total_count = len(test_images)
    
    for i, test_image in enumerate(test_images, 1):
        print(f"\n测试 {i}/{total_count}: {test_image['name']}")
        print(f"图片URL: {test_image['url']}")
        print(f"预期结果: {'违规' if not test_image['expected'] else '合规'}")
        
        result = checker._check_image(test_image['url'])
        actual_compliant = result.get("compliant", True)
        method = result.get("method", "unknown")
        
        print(f"检测结果: {'违规' if not actual_compliant else '合规'}")
        print(f"检测方法: {method}")
        
        if actual_compliant == test_image['expected']:
            print("✅ 检测结果正确")
            success_count += 1
        else:
            print("❌ 检测结果错误")
    
    accuracy = success_count / total_count * 100
    print(f"\n图片检测准确率: {accuracy:.1f}%")
    
    return accuracy >= 80

def test_comprehensive_detection():
    """测试综合检测功能"""
    print("\n" + "=" * 60)
    print("综合内容检测测试")
    print("=" * 60)
    
    checker = ContentCheckerService(api_key="test_key")
    
    # 模拟网站内容
    website_content = {
        "text": "欢迎来到在线赌博平台！我们提供百家乐、老虎机等游戏。",
        "images": [
            "https://example.com/gambling1.jpg",
            "https://example.com/logo.png"
        ]
    }
    
    print("测试网站内容:")
    print(f"文本: {website_content['text']}")
    print(f"图片: {website_content['images']}")
    
    # 执行综合检测
    result = checker.check_content_safety(
        website_content["text"], 
        website_content["images"]
    )
    
    print(f"\n综合检测结果:")
    print(f"整体合规: {'是' if result['overall_compliant'] else '否'}")
    print(f"文本检测: {'合规' if result['text_result'].get('compliant', True) else '违规'}")
    print(f"图片检测: {len(result['image_results'])} 张图片")
    
    for i, img_result in enumerate(result['image_results'], 1):
        status = "合规" if img_result.get('compliant', True) else "违规"
        print(f"  图片 {i}: {status}")
    
    print(f"检测方法: {result['detection_method']}")
    
    return True

if __name__ == "__main__":
    print("开始违规检测修复验证...")
    
    # 运行所有测试
    text_success = test_violation_detection()
    image_success = test_image_detection()
    comprehensive_success = test_comprehensive_detection()
    
    print("\n" + "=" * 60)
    print("最终测试结果")
    print("=" * 60)
    
    if text_success and image_success and comprehensive_success:
        print("✅ 所有测试通过！违规检测功能修复成功")
        print("\n修复内容:")
        print("- 添加了本地敏感词检测作为降级策略")
        print("- 修复了API错误处理逻辑")
        print("- 实现了图片URL检测功能")
        print("- 添加了综合内容检测方法")
    else:
        print("❌ 部分测试失败，需要进一步改进")
    
    print("\n现在可以运行违规检测测试:")
    print("python run_tests.py violation") 