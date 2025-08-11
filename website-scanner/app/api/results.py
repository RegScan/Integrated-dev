from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from ..database import get_db
from ..models.scan_result import ScanResult, ScanTask
from ..schemas.scan_result import (
    ScanResultResponse,
    ScanResultListResponse,
    ScanStatisticsResponse,
    ScanHistoryResponse
)
from ..services.auth import get_current_user
from ..models.user import User
import logging

router = APIRouter(prefix="/results", tags=["scan-results"])
logger = logging.getLogger(__name__)


@router.get("/", response_model=ScanResultListResponse)
async def get_scan_results(
    page: int = Query(1, ge=1, description="页码"),
    page_size: int = Query(20, ge=1, le=100, description="每页数量"),
    task_id: Optional[str] = Query(None, description="任务ID"),
    url: Optional[str] = Query(None, description="网站URL"),
    status: Optional[str] = Query(None, description="扫描状态"),
    compliance_status: Optional[str] = Query(None, description="合规状态"),
    start_date: Optional[datetime] = Query(None, description="开始日期"),
    end_date: Optional[datetime] = Query(None, description="结束日期"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取扫描结果列表
    """
    try:
        # 构建查询条件
        query = db.query(ScanResult)
        
        if task_id:
            query = query.filter(ScanResult.task_id == task_id)
        
        if url:
            query = query.filter(ScanResult.url.ilike(f"%{url}%"))
        
        if status:
            query = query.filter(ScanResult.status == status)
        
        if compliance_status:
            query = query.filter(ScanResult.compliance_status == compliance_status)
        
        if start_date:
            query = query.filter(ScanResult.created_at >= start_date)
        
        if end_date:
            query = query.filter(ScanResult.created_at <= end_date)
        
        # 按创建时间倒序排列
        query = query.order_by(ScanResult.created_at.desc())
        
        # 计算总数
        total = query.count()
        
        # 分页查询
        offset = (page - 1) * page_size
        results = query.offset(offset).limit(page_size).all()
        
        return ScanResultListResponse(
            code=0,
            message="获取成功",
            data={
                "results": results,
                "total": total,
                "page": page,
                "page_size": page_size,
                "total_pages": (total + page_size - 1) // page_size
            }
        )
        
    except Exception as e:
        logger.error(f"获取扫描结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取扫描结果失败")


@router.get("/{result_id}", response_model=ScanResultResponse)
async def get_scan_result(
    result_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取单个扫描结果详情
    """
    try:
        result = db.query(ScanResult).filter(ScanResult.id == result_id).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="扫描结果不存在")
        
        return ScanResultResponse(
            code=0,
            message="获取成功",
            data=result
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"获取扫描结果详情失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取扫描结果详情失败")


@router.get("/statistics/overview", response_model=ScanStatisticsResponse)
async def get_scan_statistics(
    days: int = Query(7, ge=1, le=365, description="统计天数"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取扫描统计信息
    """
    try:
        # 计算时间范围
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        # 基础查询
        base_query = db.query(ScanResult).filter(
            ScanResult.created_at >= start_date,
            ScanResult.created_at <= end_date
        )
        
        # 总扫描数
        total_scans = base_query.count()
        
        # 按状态统计
        status_stats = {}
        for status in ['completed', 'failed', 'running', 'pending']:
            count = base_query.filter(ScanResult.status == status).count()
            status_stats[status] = count
        
        # 按合规状态统计
        compliance_stats = {}
        for compliance in ['compliant', 'non_compliant', 'unknown']:
            count = base_query.filter(ScanResult.compliance_status == compliance).count()
            compliance_stats[compliance] = count
        
        # 按日期统计（最近7天）
        daily_stats = []
        for i in range(days):
            day_start = start_date + timedelta(days=i)
            day_end = day_start + timedelta(days=1)
            
            day_count = base_query.filter(
                ScanResult.created_at >= day_start,
                ScanResult.created_at < day_end
            ).count()
            
            daily_stats.append({
                "date": day_start.strftime("%Y-%m-%d"),
                "count": day_count
            })
        
        # 风险等级统计
        risk_stats = {}
        for risk in ['low', 'medium', 'high', 'critical']:
            count = base_query.filter(ScanResult.risk_level == risk).count()
            risk_stats[risk] = count
        
        # 平均扫描时间
        completed_results = base_query.filter(
            ScanResult.status == 'completed',
            ScanResult.scan_duration.isnot(None)
        ).all()
        
        avg_scan_time = 0
        if completed_results:
            total_time = sum(r.scan_duration for r in completed_results)
            avg_scan_time = total_time / len(completed_results)
        
        statistics = {
            "total_scans": total_scans,
            "status_distribution": status_stats,
            "compliance_distribution": compliance_stats,
            "risk_distribution": risk_stats,
            "daily_statistics": daily_stats,
            "average_scan_time": round(avg_scan_time, 2),
            "period": {
                "start_date": start_date.isoformat(),
                "end_date": end_date.isoformat(),
                "days": days
            }
        }
        
        return ScanStatisticsResponse(
            code=0,
            message="获取统计信息成功",
            data=statistics
        )
        
    except Exception as e:
        logger.error(f"获取扫描统计信息失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")


@router.get("/history/{url:path}", response_model=ScanHistoryResponse)
async def get_scan_history(
    url: str,
    limit: int = Query(10, ge=1, le=50, description="历史记录数量"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    获取指定URL的扫描历史记录
    """
    try:
        # 查询该URL的历史扫描记录
        history_results = db.query(ScanResult).filter(
            ScanResult.url == url
        ).order_by(
            ScanResult.created_at.desc()
        ).limit(limit).all()
        
        if not history_results:
            return ScanHistoryResponse(
                code=0,
                message="暂无历史记录",
                data={
                    "url": url,
                    "history": [],
                    "total_scans": 0,
                    "latest_scan": None
                }
            )
        
        # 统计信息
        total_scans = db.query(ScanResult).filter(ScanResult.url == url).count()
        latest_scan = history_results[0] if history_results else None
        
        # 合规状态变化趋势
        compliance_trend = []
        for result in history_results:
            compliance_trend.append({
                "date": result.created_at.isoformat(),
                "status": result.compliance_status,
                "risk_level": result.risk_level,
                "score": result.compliance_score
            })
        
        return ScanHistoryResponse(
            code=0,
            message="获取历史记录成功",
            data={
                "url": url,
                "history": history_results,
                "total_scans": total_scans,
                "latest_scan": latest_scan,
                "compliance_trend": compliance_trend
            }
        )
        
    except Exception as e:
        logger.error(f"获取扫描历史记录失败: {str(e)}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")


@router.delete("/{result_id}")
async def delete_scan_result(
    result_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    删除扫描结果
    """
    try:
        # 检查用户权限（只有管理员可以删除）
        if current_user.role != 'admin':
            raise HTTPException(status_code=403, detail="权限不足")
        
        result = db.query(ScanResult).filter(ScanResult.id == result_id).first()
        
        if not result:
            raise HTTPException(status_code=404, detail="扫描结果不存在")
        
        db.delete(result)
        db.commit()
        
        return {
            "code": 0,
            "message": "删除成功"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除扫描结果失败: {str(e)}")
        db.rollback()
        raise HTTPException(status_code=500, detail="删除失败")


@router.post("/export")
async def export_scan_results(
    export_params: Dict[str, Any],
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    导出扫描结果
    """
    try:
        # 构建查询条件（与get_scan_results类似）
        query = db.query(ScanResult)
        
        # 应用过滤条件
        if export_params.get('task_id'):
            query = query.filter(ScanResult.task_id == export_params['task_id'])
        
        if export_params.get('url'):
            query = query.filter(ScanResult.url.ilike(f"%{export_params['url']}%"))
        
        if export_params.get('status'):
            query = query.filter(ScanResult.status == export_params['status'])
        
        if export_params.get('start_date'):
            query = query.filter(ScanResult.created_at >= export_params['start_date'])
        
        if export_params.get('end_date'):
            query = query.filter(ScanResult.created_at <= export_params['end_date'])
        
        results = query.order_by(ScanResult.created_at.desc()).all()
        
        # 生成导出文件（这里简化处理，实际可以生成Excel或CSV）
        export_data = []
        for result in results:
            export_data.append({
                "id": result.id,
                "url": result.url,
                "status": result.status,
                "compliance_status": result.compliance_status,
                "risk_level": result.risk_level,
                "compliance_score": result.compliance_score,
                "created_at": result.created_at.isoformat(),
                "scan_duration": result.scan_duration
            })
        
        return {
            "code": 0,
            "message": "导出成功",
            "data": {
                "export_data": export_data,
                "total_records": len(export_data),
                "export_time": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"导出扫描结果失败: {str(e)}")
        raise HTTPException(status_code=500, detail="导出失败")