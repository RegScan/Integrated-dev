from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from typing import Dict

from ..services.scan_service import ScanService

router = APIRouter()

# 在实际应用中，API Key 应该从配置或环境变量中获取
API_KEY = "your_actual_api_key"

def get_scan_service():
    return ScanService(api_key=API_KEY)

@router.post("/scan/{domain}")
def scan_website(domain: str, background_tasks: BackgroundTasks, service: ScanService = Depends(get_scan_service)):
    """
    启动一个后台任务来扫描网站。
    """
    background_tasks.add_task(service.check_compliance, domain)
    return {"message": f"Scan for {domain} has been started in the background."}