// MongoDB 测试环境初始化脚本
db = db.getSiblingDB('test_scanner');

// 创建测试集合
db.createCollection('website_checks');
db.createCollection('scan_results');
db.createCollection('beian_records');

// 创建索引
db.website_checks.createIndex({ "domain": 1 });
db.website_checks.createIndex({ "timestamp": -1 });
db.scan_results.createIndex({ "domain": 1 });
db.scan_results.createIndex({ "status": 1 });
db.beian_records.createIndex({ "domain": 1 });
db.beian_records.createIndex({ "check_time": -1 });

// 插入测试数据
db.website_checks.insertMany([
  {
    "domain": "bing.com",
    "compliant": true,
    "text_result": {
      "compliant": true,
      "confidence": 0.95
    },
    "image_results": [
      {
        "url": "https://bing.com/logo.jpg",
        "compliant": true,
        "confidence": 0.90
      }
    ],
    "timestamp": new Date("2024-01-01T10:00:00Z")
  },
  {
    "domain": "test-violation.com",
    "compliant": false,
    "text_result": {
      "compliant": false,
      "confidence": 0.85,
      "violations": ["敏感词汇"]
    },
    "image_results": [
      {
        "url": "https://test-violation.com/image.jpg",
        "compliant": false,
        "confidence": 0.80,
        "violations": ["不当内容"]
      }
    ],
    "timestamp": new Date("2024-01-01T11:00:00Z")
  }
]);

db.scan_results.insertMany([
  {
    "domain": "bing.com",
    "status": "completed",
    "pages_scanned": 5,
    "violations_found": 0,
    "scan_time": new Date("2024-01-01T10:00:00Z"),
    "scan_duration": 15.5
  },
  {
    "domain": "test-violation.com",
    "status": "completed",
    "pages_scanned": 3,
    "violations_found": 2,
    "scan_time": new Date("2024-01-01T11:00:00Z"),
    "scan_duration": 12.3
  }
]);

db.beian_records.insertMany([
  {
    "domain": "bing.com",
    "has_beian": true,
    "beian_number": "京ICP备12345678号",
    "company_name": "示例公司",
    "check_time": new Date("2024-01-01T10:00:00Z"),
    "status": "valid"
  },
  {
    "domain": "no-beian.com",
    "has_beian": false,
    "beian_number": null,
    "company_name": null,
    "check_time": new Date("2024-01-01T11:00:00Z"),
    "status": "invalid"
  }
]);

print("MongoDB 测试环境初始化完成"); 