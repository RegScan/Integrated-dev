from sqlalchemy import Column, String, Integer, DateTime, Text, Float, Boolean, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid

Base = declarative_base()


class ScanTask(Base):
    """
    扫描任务模型
    """
    __tablename__ = "scan_tasks"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    url = Column(String(500), nullable=False, comment="目标网站URL")
    task_name = Column(String(200), comment="任务名称")
    task_type = Column(String(50), default="full_scan", comment="任务类型：full_scan, quick_scan, deep_scan")
    
    # 扫描配置
    scan_config = Column(JSON, comment="扫描配置参数")
    max_depth = Column(Integer, default=3, comment="最大爬取深度")
    max_pages = Column(Integer, default=100, comment="最大页面数")
    concurrent_limit = Column(Integer, default=5, comment="并发限制")
    
    # 任务状态
    status = Column(String(20), default="pending", comment="任务状态：pending, running, completed, failed, cancelled")
    progress = Column(Float, default=0.0, comment="任务进度百分比")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    started_at = Column(DateTime, comment="开始时间")
    completed_at = Column(DateTime, comment="完成时间")
    
    # 执行信息
    created_by = Column(String(36), comment="创建用户ID")
    executor_id = Column(String(100), comment="执行器ID")
    error_message = Column(Text, comment="错误信息")
    
    # 统计信息
    total_pages = Column(Integer, default=0, comment="总页面数")
    scanned_pages = Column(Integer, default=0, comment="已扫描页面数")
    found_issues = Column(Integer, default=0, comment="发现问题数")
    
    # 关联关系
    results = relationship("ScanResult", back_populates="task", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<ScanTask(id={self.id}, url={self.url}, status={self.status})>"


class ScanResult(Base):
    """
    扫描结果模型
    """
    __tablename__ = "scan_results"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String(36), ForeignKey("scan_tasks.id"), nullable=False, comment="关联任务ID")
    
    # 基本信息
    url = Column(String(1000), nullable=False, comment="检测页面URL")
    page_title = Column(String(500), comment="页面标题")
    domain = Column(String(200), comment="域名")
    
    # 扫描状态
    status = Column(String(20), default="pending", comment="扫描状态：pending, running, completed, failed")
    scan_duration = Column(Float, comment="扫描耗时（秒）")
    
    # 合规检测结果
    compliance_status = Column(String(20), comment="合规状态：compliant, non_compliant, unknown")
    compliance_score = Column(Float, comment="合规评分（0-100）")
    risk_level = Column(String(20), comment="风险等级：low, medium, high, critical")
    
    # 检测详情
    text_issues = Column(JSON, comment="文本内容问题")
    image_issues = Column(JSON, comment="图片内容问题")
    link_issues = Column(JSON, comment="链接问题")
    structure_issues = Column(JSON, comment="结构问题")
    
    # 备案信息
    beian_info = Column(JSON, comment="备案信息")
    beian_status = Column(String(20), comment="备案状态：valid, invalid, unknown")
    
    # 技术信息
    response_code = Column(Integer, comment="HTTP响应码")
    response_time = Column(Float, comment="响应时间（毫秒）")
    page_size = Column(Integer, comment="页面大小（字节）")
    
    # 内容摘要
    content_summary = Column(Text, comment="内容摘要")
    keywords = Column(JSON, comment="关键词列表")
    
    # 截图和证据
    screenshot_path = Column(String(500), comment="截图文件路径")
    evidence_files = Column(JSON, comment="证据文件列表")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    scanned_at = Column(DateTime, comment="扫描时间")
    
    # 处理状态
    is_processed = Column(Boolean, default=False, comment="是否已处理")
    processed_at = Column(DateTime, comment="处理时间")
    processed_by = Column(String(36), comment="处理人ID")
    
    # 关联关系
    task = relationship("ScanTask", back_populates="results")
    
    def __repr__(self):
        return f"<ScanResult(id={self.id}, url={self.url}, compliance_status={self.compliance_status})>"
    
    @property
    def is_compliant(self):
        """是否合规"""
        return self.compliance_status == "compliant"
    
    @property
    def has_high_risk(self):
        """是否高风险"""
        return self.risk_level in ["high", "critical"]
    
    def get_issue_summary(self):
        """获取问题摘要"""
        issues = []
        
        if self.text_issues:
            issues.extend(self.text_issues.get("issues", []))
        
        if self.image_issues:
            issues.extend(self.image_issues.get("issues", []))
        
        if self.link_issues:
            issues.extend(self.link_issues.get("issues", []))
        
        if self.structure_issues:
            issues.extend(self.structure_issues.get("issues", []))
        
        return issues
    
    def get_risk_score(self):
        """计算风险评分"""
        if self.compliance_score is not None:
            return 100 - self.compliance_score
        return 0


class ScanStatistics(Base):
    """
    扫描统计模型
    """
    __tablename__ = "scan_statistics"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    date = Column(DateTime, nullable=False, comment="统计日期")
    
    # 任务统计
    total_tasks = Column(Integer, default=0, comment="总任务数")
    completed_tasks = Column(Integer, default=0, comment="完成任务数")
    failed_tasks = Column(Integer, default=0, comment="失败任务数")
    
    # 结果统计
    total_pages = Column(Integer, default=0, comment="总页面数")
    compliant_pages = Column(Integer, default=0, comment="合规页面数")
    non_compliant_pages = Column(Integer, default=0, comment="不合规页面数")
    
    # 风险统计
    low_risk_count = Column(Integer, default=0, comment="低风险数量")
    medium_risk_count = Column(Integer, default=0, comment="中风险数量")
    high_risk_count = Column(Integer, default=0, comment="高风险数量")
    critical_risk_count = Column(Integer, default=0, comment="严重风险数量")
    
    # 性能统计
    avg_scan_time = Column(Float, comment="平均扫描时间")
    avg_response_time = Column(Float, comment="平均响应时间")
    
    # 备案统计
    beian_valid_count = Column(Integer, default=0, comment="备案有效数量")
    beian_invalid_count = Column(Integer, default=0, comment="备案无效数量")
    beian_unknown_count = Column(Integer, default=0, comment="备案未知数量")
    
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f"<ScanStatistics(date={self.date}, total_tasks={self.total_tasks})>"