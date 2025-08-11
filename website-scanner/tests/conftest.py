import pytest
import os
from unittest.mock import Mock, patch


@pytest.fixture(scope="session")
def test_settings():
    """测试环境配置"""
    return {
        "MONGODB_URL": "mongodb://localhost:27017/test_scanner",
        "DEBUG": True,
        "ENVIRONMENT": "testing",
        "LOG_LEVEL": "DEBUG",
        "MAX_CONCURRENT_SCANS": 5,
        "SCAN_TIMEOUT": 30
    }


@pytest.fixture
def real_website_list():
    """真实网站列表用于测试"""
    return [
        {
            "domain": "bing.com",
            "description": "示例网站",
            "expected_compliant": True
        },
        {
            "domain": "httpbin.org", 
            "description": "HTTP测试服务",
            "expected_compliant": True
        },
        {
            "domain": "jsonplaceholder.typicode.com",
            "description": "API测试服务", 
            "expected_compliant": True
        },
        {
            "domain": "github.com",
            "description": "GitHub",
            "expected_compliant": True
        },
        {
            "domain": "stackoverflow.com",
            "description": "Stack Overflow",
            "expected_compliant": True
        }
    ]



@pytest.fixture
def violation_website_list():
    """违规网站列表用于测试"""
    return [
        {
            "domain": "example-violation-gambling.com",
            "description": "模拟赌博网站",
            "expected_compliant": False,
            "violation_type": "gambling",
            "test_content": "在线赌博 博彩 赌场 老虎机 百家乐"
        },
        {
            "domain": "example-violation-porn.com", 
            "description": "模拟色情网站",
            "expected_compliant": False,
            "violation_type": "porn",
            "test_content": "成人内容 色情 情色 裸体 性爱"
        },
        {
            "domain": "example-violation-violence.com",
            "description": "模拟暴力网站", 
            "expected_compliant": False,
            "violation_type": "violence",
            "test_content": "暴力 血腥 恐怖 杀人 武器"
        },
        {
            "domain": "example-violation-drugs.com",
            "description": "模拟毒品网站",
            "expected_compliant": False,
            "violation_type": "drugs",
            "test_content": "毒品 大麻 冰毒 摇头丸 可卡因"
        },
        {
            "domain": "example-violation-political.com",
            "description": "模拟政治敏感网站",
            "expected_compliant": False,
            "violation_type": "political",
            "test_content": "反动 颠覆 政治敏感 非法组织"
        }
    ]


@pytest.fixture
def test_domains():
    """测试域名列表"""
    return [
        "bing.com",
        "httpbin.org",
        "jsonplaceholder.typicode.com",
        "github.com",
        "stackoverflow.com"
    ]


@pytest.fixture
def violation_test_domains():
    """违规测试域名列表"""
    return [
        "example-violation-gambling.com",
        "example-violation-porn.com", 
        "example-violation-violence.com",
        "example-violation-drugs.com",
        "example-violation-political.com"
    ]


@pytest.fixture
def invalid_domains():
    """无效域名列表用于错误测试"""
    return [
        "this-domain-does-not-exist-12345.com",
        "invalid-domain-test-99999.org",
        "not-a-real-domain-xyz.com"
    ]


@pytest.fixture
def sensitive_words_list():
    """敏感词列表"""
    return [
        "赌博", "色情", "暴力", "毒品", "反动",
        "gambling", "porn", "violence", "drugs"
    ]


@pytest.fixture
def violation_content_samples():
    """违规内容样本"""
    return {
        "gambling": [
            "在线赌博网站，提供百家乐、老虎机等游戏",
            "博彩平台，支持在线投注和实时开奖",
            "赌场游戏，包括轮盘、扑克、骰子等"
        ],
        "porn": [
            "成人内容网站，包含色情图片和视频",
            "情色网站，提供成人娱乐内容",
            "裸体艺术摄影作品展示"
        ],
        "violence": [
            "暴力游戏网站，包含血腥和恐怖内容",
            "武器交易平台，销售各类管制刀具",
            "恐怖组织宣传网站"
        ],
        "drugs": [
            "毒品交易网站，销售各类违禁药物",
            "大麻种植技术交流论坛",
            "冰毒制作方法分享平台"
        ],
        "political": [
            "反动政治宣传网站",
            "颠覆国家政权的内容",
            "非法政治组织活动信息"
        ]
    }


@pytest.fixture
def mock_violation_websites():
    """模拟违规网站内容"""
    return {
        "example-violation-gambling.com": {
            "text": "欢迎来到在线赌博平台！我们提供百家乐、老虎机、轮盘等多种博彩游戏。24小时在线服务，支持多种支付方式。立即注册，享受刺激的赌博体验！",
            "images": [
                "https://example.com/gambling1.jpg",
                "https://example.com/gambling2.jpg"
            ],
            "expected_violations": ["gambling", "betting"]
        },
        "example-violation-porn.com": {
            "text": "成人内容网站，提供高清色情图片和视频。包含各种成人娱乐内容，满足您的需求。18岁以上用户专用。",
            "images": [
                "https://example.com/porn1.jpg",
                "https://example.com/porn2.jpg"
            ],
            "expected_violations": ["porn", "adult"]
        },
        "example-violation-violence.com": {
            "text": "暴力游戏和武器交易平台。提供各类管制刀具、仿真枪械销售。包含血腥暴力内容，未成年人禁止访问。",
            "images": [
                "https://example.com/violence1.jpg",
                "https://example.com/violence2.jpg"
            ],
            "expected_violations": ["violence", "weapons"]
        },
        "example-violation-drugs.com": {
            "text": "毒品交易平台，销售大麻、冰毒、摇头丸等违禁药物。提供毒品制作方法和种植技术。",
            "images": [
                "https://example.com/drugs1.jpg",
                "https://example.com/drugs2.jpg"
            ],
            "expected_violations": ["drugs", "illegal"]
        },
        "example-violation-political.com": {
            "text": "政治敏感内容网站，包含反动政治宣传和颠覆国家政权的内容。非法政治组织活动信息。",
            "images": [
                "https://example.com/political1.jpg",
                "https://example.com/political2.jpg"
            ],
            "expected_violations": ["political", "illegal"]
        }
    }


# 测试标记
def pytest_configure(config):
    """pytest配置"""
    config.addinivalue_line(
        "markers", "real_website: 真实网站测试"
    )
    config.addinivalue_line(
        "markers", "violation_test: 违规检测测试"
    )
    config.addinivalue_line(
        "markers", "slow: 慢速测试"
    )
    config.addinivalue_line(
        "markers", "integration: 集成测试"
    )


# 测试环境变量设置
os.environ["TESTING"] = "1"
os.environ["MONGODB_URL"] = "mongodb://localhost:27017/test_scanner"
os.environ["DEBUG"] = "true"