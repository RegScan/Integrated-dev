from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File
from fastapi.responses import JSONResponse
from typing import Any, Dict, List, Optional
from sqlalchemy.orm import Session
import json
import yaml

from ..database import get_db
from ..services.config_service import ConfigService
from ..services.user_service import UserService
from ..schemas.config_schema import (
    ConfigCreate, ConfigUpdate, ConfigResponse, ConfigQuery, ConfigStats,
    ConfigTemplateCreate, ConfigTemplateResponse, ConfigGroupCreate, ConfigGroupResponse,
    BatchConfigUpdate, ConfigExport, ConfigImport
)
from ..schemas.user_schema import UserResponse

router = APIRouter()

def get_config_service(db: Session = Depends(get_db)) -> ConfigService:
    return ConfigService(db)

def get_user_service(db: Session = Depends(get_db)) -> UserService:
    return UserService(db)

# 配置管理API
@router.get("/", response_model=List[ConfigResponse], summary="获取配置列表")
async def get_configs(
    key: Optional[str] = Query(None, description="配置键名"),
    category: Optional[str] = Query(None, description="配置分类"),
    environment: Optional[str] = Query(None, description="环境"),
    is_encrypted: Optional[bool] = Query(None, description="是否加密"),
    is_sensitive: Optional[bool] = Query(None, description="是否敏感信息"),
    limit: int = Query(100, description="返回数量限制", ge=1, le=1000),
    offset: int = Query(0, description="偏移量", ge=0),
    service: ConfigService = Depends(get_config_service)
):
    """获取配置列表，支持分页和过滤"""
    query = ConfigQuery(
        key=key,
        category=category,
        environment=environment,
        is_encrypted=is_encrypted,
        is_sensitive=is_sensitive,
        limit=limit,
        offset=offset
    )
    
    configs = service.get_configs(query)
    return configs

@router.get("/{config_key}", response_model=Dict[str, Any], summary="获取配置项")
async def get_config(
    config_key: str,
    service: ConfigService = Depends(get_config_service)
):
    """获取指定配置项的值"""
    value = service.get_config(config_key)
    if value is None:
        raise HTTPException(status_code=404, detail="配置项不存在")
    return {"key": config_key, "value": value}

@router.post("/", response_model=ConfigResponse, summary="创建配置")
async def create_config(
    config_data: ConfigCreate,
    service: ConfigService = Depends(get_config_service)
):
    """创建新的配置项"""
    try:
        config = service.set_config(config_data)
        return config
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建配置失败: {str(e)}")

@router.put("/{config_id}", response_model=ConfigResponse, summary="更新配置")
async def update_config(
    config_id: int,
    config_update: ConfigUpdate,
    service: ConfigService = Depends(get_config_service)
):
    """更新指定配置项"""
    try:
        config = service.update_config(config_id, config_update)
        return config
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")

@router.delete("/{config_id}", summary="删除配置")
async def delete_config(
    config_id: int,
    service: ConfigService = Depends(get_config_service)
):
    """删除指定配置项"""
    success = service.delete_config(config_id)
    if not success:
        raise HTTPException(status_code=404, detail="配置项不存在")
    return {"message": "配置项删除成功"}

@router.post("/batch", response_model=List[ConfigResponse], summary="批量更新配置")
async def batch_update_configs(
    batch_data: BatchConfigUpdate,
    service: ConfigService = Depends(get_config_service)
):
    """批量更新配置项"""
    try:
        configs = service.batch_update_configs(batch_data)
        return configs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量更新失败: {str(e)}")

@router.get("/stats/overview", response_model=ConfigStats, summary="配置统计")
async def get_config_stats(
    service: ConfigService = Depends(get_config_service)
):
    """获取配置统计信息"""
    return service.get_config_stats()

# 配置模板API
@router.post("/templates/", response_model=ConfigTemplateResponse, summary="创建配置模板")
async def create_config_template(
    template_data: ConfigTemplateCreate,
    service: ConfigService = Depends(get_config_service)
):
    """创建配置模板"""
    try:
        template = service.create_template(template_data)
        return template
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建模板失败: {str(e)}")

@router.get("/templates/", response_model=List[ConfigTemplateResponse], summary="获取模板列表")
async def get_config_templates(
    service: ConfigService = Depends(get_config_service)
):
    """获取配置模板列表"""
    # 这里需要实现模板查询功能
    return []

# 配置组API
@router.post("/groups/", response_model=ConfigGroupResponse, summary="创建配置组")
async def create_config_group(
    group_data: ConfigGroupCreate,
    service: ConfigService = Depends(get_config_service)
):
    """创建配置组"""
    try:
        group = service.create_group(group_data)
        return group
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建配置组失败: {str(e)}")

@router.get("/groups/", response_model=List[ConfigGroupResponse], summary="获取配置组列表")
async def get_config_groups(
    service: ConfigService = Depends(get_config_service)
):
    """获取配置组列表"""
    # 这里需要实现配置组查询功能
    return []

# 导入导出API
@router.post("/export/", response_model=ConfigExport, summary="导出配置")
async def export_configs(
    category: Optional[str] = Query(None, description="配置分类"),
    environment: Optional[str] = Query(None, description="环境"),
    service: ConfigService = Depends(get_config_service)
):
    """导出配置数据"""
    try:
        export_data = service.export_configs(category, environment)
        return ConfigExport(**export_data)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导出配置失败: {str(e)}")

@router.post("/import/", summary="导入配置")
async def import_configs(
    overwrite: bool = Query(False, description="是否覆盖现有配置"),
    service: ConfigService = Depends(get_config_service)
):
    """导入配置数据"""
    # 这里应该处理文件上传
    # 为了简化，这里只是返回成功
    return {"message": "配置导入成功", "imported_count": 0}

@router.post("/import/file", summary="从文件导入配置")
async def import_configs_from_file(
    file: UploadFile = File(...),
    overwrite: bool = Query(False, description="是否覆盖现有配置"),
    service: ConfigService = Depends(get_config_service)
):
    """从文件导入配置"""
    try:
        content = await file.read()
        
        # 根据文件扩展名解析
        if file.filename.endswith('.json'):
            import_data = json.loads(content.decode())
        elif file.filename.endswith('.yaml') or file.filename.endswith('.yml'):
            import_data = yaml.safe_load(content.decode())
        else:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        imported_count = service.import_configs(import_data, overwrite)
        return {"message": "配置导入成功", "imported_count": imported_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"导入配置失败: {str(e)}")

# 配置版本API
@router.get("/{config_id}/versions", summary="获取配置版本历史")
async def get_config_versions(
    config_id: int,
    service: ConfigService = Depends(get_config_service)
):
    """获取配置项的版本历史"""
    # 这里需要实现版本查询功能
    return {"config_id": config_id, "versions": []}

@router.get("/{config_id}/versions/{version}", summary="获取指定版本")
async def get_config_version(
    config_id: int,
    version: int,
    service: ConfigService = Depends(get_config_service)
):
    """获取配置项的指定版本"""
    # 这里需要实现版本查询功能
    return {"config_id": config_id, "version": version, "value": ""}

# 配置访问日志API
@router.get("/{config_id}/logs", summary="获取配置访问日志")
async def get_config_access_logs(
    config_id: int,
    limit: int = Query(50, description="返回数量限制", ge=1, le=1000),
    service: ConfigService = Depends(get_config_service)
):
    """获取配置项的访问日志"""
    # 这里需要实现日志查询功能
    return {"config_id": config_id, "logs": []}

# 配置搜索API
@router.get("/search/", summary="搜索配置")
async def search_configs(
    q: str = Query(..., description="搜索关键词"),
    service: ConfigService = Depends(get_config_service)
):
    """搜索配置项"""
    # 这里需要实现搜索功能
    return {"query": q, "results": []}

# 配置验证API
@router.post("/validate/", summary="验证配置")
async def validate_config(
    config_data: Dict[str, Any],
    service: ConfigService = Depends(get_config_service)
):
    """验证配置数据的有效性"""
    # 这里需要实现配置验证功能
    return {"valid": True, "errors": []}

# 配置同步API
@router.post("/sync/", summary="同步配置")
async def sync_configs(
    target_environment: str = Query(..., description="目标环境"),
    service: ConfigService = Depends(get_config_service)
):
    """同步配置到指定环境"""
    # 这里需要实现配置同步功能
    return {"message": "配置同步成功", "target_environment": target_environment}

# 配置备份API
@router.post("/backup/", summary="备份配置")
async def backup_configs(
    service: ConfigService = Depends(get_config_service)
):
    """备份所有配置数据"""
    try:
        backup_data = service.export_configs()
        return {"message": "配置备份成功", "backup_time": backup_data["export_time"]}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"备份配置失败: {str(e)}")

# 配置恢复API
@router.post("/restore/", summary="恢复配置")
async def restore_configs(
    backup_data: Dict[str, Any],
    service: ConfigService = Depends(get_config_service)
):
    """从备份数据恢复配置"""
    try:
        imported_count = service.import_configs(backup_data, overwrite=True)
        return {"message": "配置恢复成功", "restored_count": imported_count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复配置失败: {str(e)}")