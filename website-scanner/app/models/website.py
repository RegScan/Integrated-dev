from sqlalchemy import Column, String, Integer, DateTime, Boolean, Text, JSON, Float
from sqlalchemy.ext.declarative import declarative_base
from datetime import datetime
import uuid

Base = declarative_base()


class WebsiteInfo(Base):
    """
    网站信息模型
    """
    __tablename__ = "website_info"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    domain = Column(String(255), unique=True, nullable=False, comment="域名")
    url = Column(String(500), nullable=False, comment="网站URL")
    
    # 基本信息
    title = Column(String(500), comment="网站标题")
    description = Column(Text, comment="网站描述")
    keywords = Column(Text, comment="关键词")
    
    # 备案信息
    icp_number = Column(String(50), comment="ICP备案号")
    icp_status = Column(String(20), comment="备案状态：valid, invalid, unknown")
    icp_company = Column(String(200), comment="备案公司")
    icp_checked_at = Column(DateTime, comment="备案查询时间")
    
    # 技术信息
    server_info = Column(JSON, comment="服务器信息")
    cms_info = Column(JSON, comment="CMS信息")
    technology_stack = Column(JSON, comment="技术栈")
    
    # 安全信息
    ssl_info = Column(JSON, comment="SSL证书信息")
    security_headers = Column(JSON, comment="安全头信息")
    
    # 性能信息
    response_time = Column(Float, comment="响应时间(ms)")
    page_size = Column(Integer, comment="页面大小(bytes)")
    load_time = Column(Float, comment="加载时间(s)")
    
    # 内容信息
    page_count = Column(Integer, default=0, comment="页面数量")
    image_count = Column(Integer, default=0, comment="图片数量")
    link_count = Column(Integer, default=0, comment="链接数量")
    
    # 状态信息
    status = Column(String(20), default="active", comment="状态：active, inactive, blocked")
    last_scan_at = Column(DateTime, comment="最后扫描时间")
    scan_count = Column(Integer, default=0, comment="扫描次数")
    
    # 风险评估
    risk_level = Column(String(20), comment="风险等级：low, medium, high, critical")
    risk_score = Column(Float, comment="风险评分(0-100)")
    compliance_status = Column(String(20), comment="合规状态：compliant, non_compliant, unknown")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    # 其他信息
    tags = Column(JSON, comment="标签")
    notes = Column(Text, comment="备注")
    contact_info = Column(JSON, comment="联系信息")
    
    def __repr__(self):
        return f"<WebsiteInfo(id={self.id}, domain={self.domain}, status={self.status})>"
    
    def update_scan_info(self, scan_result=None):
        """更新扫描信息"""
        self.last_scan_at = datetime.utcnow()
        self.scan_count += 1
        
        if scan_result:
            self.risk_level = scan_result.get("risk_level")
            self.risk_score = scan_result.get("risk_score")
            self.compliance_status = scan_result.get("compliance_status")
    
    def is_compliant(self) -> bool:
        """是否合规"""
        return self.compliance_status == "compliant"
    
    def is_high_risk(self) -> bool:
        """是否高风险"""
        return self.risk_level in ["high", "critical"]
    
    def get_risk_score_level(self) -> str:
        """获取风险等级"""
        if not self.risk_score:
            return "unknown"
        
        if self.risk_score >= 80:
            return "critical"
        elif self.risk_score >= 60:
            return "high"
        elif self.risk_score >= 30:
            return "medium"
        else:
            return "low"
    
    def to_dict(self, include_details=False):
        """转换为字典"""
        data = {
            "id": self.id,
            "domain": self.domain,
            "url": self.url,
            "title": self.title,
            "description": self.description,
            "icp_number": self.icp_number,
            "icp_status": self.icp_status,
            "icp_company": self.icp_company,
            "status": self.status,
            "risk_level": self.risk_level,
            "risk_score": self.risk_score,
            "compliance_status": self.compliance_status,
            "last_scan_at": self.last_scan_at.isoformat() if self.last_scan_at else None,
            "scan_count": self.scan_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }
        
        if include_details:
            data.update({
                "keywords": self.keywords,
                "server_info": self.server_info,
                "cms_info": self.cms_info,
                "technology_stack": self.technology_stack,
                "ssl_info": self.ssl_info,
                "security_headers": self.security_headers,
                "response_time": self.response_time,
                "page_size": self.page_size,
                "load_time": self.load_time,
                "page_count": self.page_count,
                "image_count": self.image_count,
                "link_count": self.link_count,
                "tags": self.tags,
                "notes": self.notes,
                "contact_info": self.contact_info,
                "icp_checked_at": self.icp_checked_at.isoformat() if self.icp_checked_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None
            })
        
        return data


class WebsitePage(Base):
    """
    网站页面模型
    """
    __tablename__ = "website_pages"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    website_id = Column(String(36), nullable=False, comment="网站ID")
    url = Column(String(1000), nullable=False, comment="页面URL")
    
    # 页面信息
    title = Column(String(500), comment="页面标题")
    content_hash = Column(String(64), comment="内容哈希")
    content_length = Column(Integer, comment="内容长度")
    
    # HTTP信息
    status_code = Column(Integer, comment="HTTP状态码")
    response_time = Column(Float, comment="响应时间(ms)")
    content_type = Column(String(100), comment="内容类型")
    
    # 页面分析
    text_content = Column(Text, comment="文本内容")
    links = Column(JSON, comment="链接列表")
    images = Column(JSON, comment="图片列表")
    forms = Column(JSON, comment="表单列表")
    
    # 风险信息
    risk_items = Column(JSON, comment="风险项")
    sensitive_words = Column(JSON, comment="敏感词")
    external_links = Column(JSON, comment="外部链接")
    
    # 状态信息
    scan_status = Column(String(20), default="pending", comment="扫描状态")
    last_scanned_at = Column(DateTime, comment="最后扫描时间")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f"<WebsitePage(id={self.id}, url={self.url}, status={self.scan_status})>"
    
    def has_risks(self) -> bool:
        """是否有风险"""
        return bool(self.risk_items and len(self.risk_items) > 0)
    
    def get_risk_count(self) -> int:
        """获取风险数量"""
        return len(self.risk_items) if self.risk_items else 0
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "website_id": self.website_id,
            "url": self.url,
            "title": self.title,
            "status_code": self.status_code,
            "response_time": self.response_time,
            "content_type": self.content_type,
            "content_length": self.content_length,
            "scan_status": self.scan_status,
            "risk_count": self.get_risk_count(),
            "has_risks": self.has_risks(),
            "last_scanned_at": self.last_scanned_at.isoformat() if self.last_scanned_at else None,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }


class WebsiteCategory(Base):
    """
    网站分类模型
    """
    __tablename__ = "website_categories"
    
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), unique=True, nullable=False, comment="分类名称")
    description = Column(Text, comment="分类描述")
    
    # 分类配置
    parent_id = Column(String(36), comment="父分类ID")
    level = Column(Integer, default=1, comment="分类层级")
    sort_order = Column(Integer, default=0, comment="排序")
    
    # 检测规则
    detection_rules = Column(JSON, comment="检测规则")
    risk_weight = Column(Float, default=1.0, comment="风险权重")
    
    # 状态信息
    is_active = Column(Boolean, default=True, comment="是否激活")
    website_count = Column(Integer, default=0, comment="网站数量")
    
    # 时间信息
    created_at = Column(DateTime, default=datetime.utcnow, comment="创建时间")
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, comment="更新时间")
    
    def __repr__(self):
        return f"<WebsiteCategory(id={self.id}, name={self.name}, level={self.level})>"
    
    def to_dict(self):
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "parent_id": self.parent_id,
            "level": self.level,
            "sort_order": self.sort_order,
            "risk_weight": self.risk_weight,
            "is_active": self.is_active,
            "website_count": self.website_count,
            "created_at": self.created_at.isoformat() if self.created_at else None
        }