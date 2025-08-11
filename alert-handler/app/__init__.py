"""告警处理模块

智能告警处理系统的核心模块，提供：
- 告警接收和处理
- 多渠道通知服务
- 自动化处置动作
- 工单系统集成
- 异步任务处理
"""

__version__ = "1.0.0"
__author__ = "Alert Handler Team"
__description__ = "智能告警处理系统"

from .database import Base, engine, get_db, db_manager
from .models import *
from .services import *
from .api import *
from .tasks import *

__all__ = [
    'Base',
    'engine', 
    'get_db',
    'db_manager'
]