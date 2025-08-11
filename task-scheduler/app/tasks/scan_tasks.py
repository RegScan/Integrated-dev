from app.celery_app import celery_app
import requests

@celery_app.task
def run_single_scan(domain: str):
    """调用 website-scanner 服务来扫描单个网站"""
    try:
        # 假设 website-scanner 服务运行在 localhost:8001
        response = requests.post(f"http://localhost:8001/api/v1/scan/{domain}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"扫描失败: {domain}, 错误: {e}")
        # 可以在这里添加重试逻辑
        raise

@celery_app.task
def run_batch_scan(domains: list):
    """批量扫描网站"""
    for domain in domains:
        run_single_scan.delay(domain)