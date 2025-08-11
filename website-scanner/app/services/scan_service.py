from typing import Dict
import time
from pymongo import MongoClient
from .crawler import CrawlerService
from .content_checker import ContentCheckerService

class ScanService:
    def __init__(self, api_key: str, db_url: str = "mongodb://localhost:27017/"):
        self.crawler = CrawlerService()
        self.content_checker = ContentCheckerService(api_key=api_key)
        self.db = MongoClient(db_url)["compliance"]

    def check_compliance(self, domain: str) -> Dict:
        """检测网站合规性"""
        website_data = self.crawler.crawl_website(domain)
        if not website_data:
            return {"status": "error", "message": "爬取失败"}

        # 1. 文本合规检测
        text_result = self.content_checker._check_text(website_data["text"])

        # 2. 图片合规检测
        image_results = []
        for img_url in website_data["images"]:
            img_result = self.content_checker._check_image(img_url)
            image_results.append(img_result)

        # 3. 汇总结果
        is_compliant = all([
            text_result.get("compliant", False),
            all([r.get("compliant", False) for r in image_results])
        ])

        result = {
            "domain": domain,
            "compliant": is_compliant,
            "text_result": text_result,
            "image_results": image_results,
            "timestamp": time.time()
        }

        # 存储结果到数据库
        self.db.website_checks.insert_one(result)
        return result