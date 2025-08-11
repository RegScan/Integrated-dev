# 7-21-demo 初版项目规划书 2025年7月21日

从开发者视角出发，实现内容合规检测系统需关注**技术可行性、快速迭代能力、资源复用**，以下是可落地的技术方案与实施路径：


### 一、架构设计：从“MVP”到“可扩展”
#### 1. 最小可行产品（MVP）架构
```
┌───────────────────────────────────────────────────────────────┐
│                         用户界面层                              │
│  (Web管理后台、CLI工具、API接口)                              │
└───────────────────┬────────────────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────────────────┐
│                         核心服务层                              │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐     │
│  │ 网站检测服务   │  │ 流量检测服务   │  │ 告警处置服务    │     │
│  │ (定时爬取+API) │  │ (流量镜像+分析)│  │ (分级通知+工单)│     │
│  └───────────────┘  └───────────────┘  └─────────────────┘     │
└───────────────────┬────────────────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────────────────┐
│                         数据存储层                              │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐     │
│  │ MongoDB       │  │ Redis         │  │ Elasticsearch   │     │
│  │ (检测结果)    │  │ (缓存)        │  │ (日志检索)      │     │
│  └───────────────┘  └───────────────┘  └─────────────────┘     │
└───────────────────┬────────────────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────────────────┐
│                         外部服务层                              │
│  ┌───────────────┐  ┌───────────────┐  ┌─────────────────┐     │
│  │ 内容审核API    │  │ 备案查询API    │  │ 流量特征库      │     │
│  │ (百度/阿里)    │  │ (工信部接口)  │  │ (开源/商用)     │     │
│  └───────────────┘  └───────────────┘  └─────────────────┘     │
└───────────────────────────────────────────────────────────────┘
```

#### 2. 技术选型（务实方案）
| 领域         | 工具/框架                     | 理由                                                                 |
|--------------|------------------------------|----------------------------------------------------------------------|
| 后端开发     | FastAPI + Python 3.9         | 开发效率高，支持异步IO（应对大量API调用），社区活跃                 |
| 爬虫         | Scrapy + Playwright          | Scrapy管理爬取流程，Playwright处理JS渲染页面（如React/Vue网站）      |
| 流量分析     | Suricata + nDPI              | 开源IDS工具，支持实时流量检测和协议识别（如识别VPN、P2P流量）       |
| 数据存储     | MongoDB + Redis              | MongoDB灵活存储非结构化检测结果，Redis缓存高频访问数据（如备案信息） |
| 任务队列     | Celery + RabbitMQ            | 分布式任务调度，处理大量爬取和检测任务（如夜间批量扫描）             |
| 可视化       | Grafana + Prometheus         | 监控系统性能和检测指标（如每日违规数、处理耗时）                     |


### 二、核心功能实现：从“能跑”到“能打”
#### 1. 网站合规检测（核心代码片段）
```python
# 网站合规检测核心逻辑
import requests
from playwright.sync_api import sync_playwright
from pymongo import MongoClient
import time

class WebsiteScanner:
    def __init__(self, api_key):
        self.content_api = "https://api.xxx.com/content/scan"  # 第三方内容审核API
        self.api_key = api_key
        self.db = MongoClient("mongodb://localhost:27017/")["compliance"]
    
    def crawl_website(self, domain, max_pages=10):
        """爬取网站内容（首页+随机10个内页）"""
        with sync_playwright() as p:
            browser = p.chromium.launch()
            page = browser.new_page()
            try:
                page.goto(f"https://{domain}", timeout=10000)
                time.sleep(2)  # 等待页面加载
                html_content = page.content()
                # 提取页面文本和图片URL
                text_content = page.inner_text("body")
                image_urls = [img.get_attribute("src") for img in page.query_selector_all("img")]
                return {
                    "html": html_content,
                    "text": text_content,
                    "images": image_urls[:5]  # 限制处理图片数量
                }
            except Exception as e:
                print(f"爬取失败: {domain}, 错误: {e}")
                return None
            finally:
                browser.close()
    
    def check_compliance(self, domain):
        """检测网站合规性"""
        website_data = self.crawl_website(domain)
        if not website_data:
            return {"status": "error", "message": "爬取失败"}
        
        # 1. 文本合规检测（调用第三方API）
        text_result = self._check_text(website_data["text"])
        
        # 2. 图片合规检测（调用第三方API）
        image_results = []
        for img_url in website_data["images"]:
            if img_url.startswith("http"):  # 过滤非HTTP链接
                img_result = self._check_image(img_url)
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
    
    def _check_text(self, text):
        """调用第三方文本审核API"""
        response = requests.post(
            self.content_api,
            json={"text": text, "type": "text"},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()
    
    def _check_image(self, image_url):
        """调用第三方图片审核API"""
        response = requests.post(
            self.content_api,
            json={"url": image_url, "type": "image"},
            headers={"Authorization": f"Bearer {self.api_key}"}
        )
        return response.json()

# 使用示例
if __name__ == "__main__":
    scanner = WebsiteScanner(api_key="your_api_key")
    result = scanner.check_compliance("example.com")
    print(result)
```

#### 2. 流量合规检测（核心配置）
```yaml
# Suricata流量检测规则示例（detect.rules）
# 1. 检测疑似DDoS攻击流量
alert tcp any any -> any 80 (msg:"疑似HTTP洪水攻击"; flow:stateless; threshold: type limit, track by_src, count 500, seconds 1; sid:100001; rev:1;)

# 2. 检测未授权VPN流量（OpenVPN特征）
alert tcp any any -> any 1194 (msg:"疑似未授权OpenVPN流量"; content:"\x38\x81\x00\x00\x00\x00\x00\x00"; depth:8; sid:100002; rev:1;)

# 3. 检测端口扫描行为
alert tcp any any -> any any (msg:"疑似端口扫描"; flow:stateless; threshold: type limit, track by_src, count 100, seconds 10; sid:100003; rev:1;)
```

#### 3. 告警与处置流程
```python
# 告警处置服务
from fastapi import FastAPI
from pydantic import BaseModel
import smtplib
from email.mime.text import MIMEText
import requests

app = FastAPI()

class Alert(BaseModel):
    alert_id: str
    domain: str
    severity: str  # "low", "medium", "high"
    description: str
    evidence: dict

# 配置信息
EMAIL_CONFIG = {
    "smtp_server": "smtp.example.com",
    "smtp_port": 587,
    "username": "alert@example.com",
    "password": "your_password"
}

IDC_API = "https://idc-api.example.com/servers"  # IDC服务器管理API

@app.post("/alerts/")
async def handle_alert(alert: Alert):
    """处理告警并执行相应动作"""
    # 1. 记录告警到数据库
    # ... 数据库操作代码 ...
    
    # 2. 根据严重程度发送通知
    if alert.severity == "high":
        # 高风险：立即发送邮件+短信
        send_email(alert)
        send_sms(alert)
        
        # 自动暂停服务器（可选，需谨慎使用）
        if should_auto_suspend(alert):
            suspend_server(alert.domain)
    
    elif alert.severity == "medium":
        # 中风险：发送邮件
        send_email(alert)
    
    # 3. 生成处置工单
    create_ticket(alert)
    
    return {"status": "success", "message": "告警已处理"}

def send_email(alert: Alert):
    """发送告警邮件"""
    msg = MIMEText(f"""
    严重级别: {alert.severity}
    域名: {alert.domain}
    描述: {alert.description}
    证据: {alert.evidence}
    
    请立即处理！
    """, "plain", "utf-8")
    
    msg["Subject"] = f"[合规告警] {alert.severity.upper()} - {alert.domain}"
    msg["From"] = EMAIL_CONFIG["username"]
    msg["To"] = "compliance-team@example.com"
    
    with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
        server.starttls()
        server.login(EMAIL_CONFIG["username"], EMAIL_CONFIG["password"])
        server.send_message(msg)

def suspend_server(domain: str):
    """暂停违规服务器（通过IDC API）"""
    # 查询域名对应的服务器IP
    server_ip = lookup_server_ip(domain)
    if not server_ip:
        return
    
    # 调用IDC API暂停服务器
    response = requests.post(
        f"{IDC_API}/{server_ip}/suspend",
        headers={"Authorization": "Bearer your_token"},
        json={"reason": "内容合规违规"}
    )
    
    if response.status_code == 200:
        print(f"服务器 {server_ip} 已暂停")
    else:
        print(f"暂停服务器失败: {response.text}")
```


### 三、部署与运维：从“单节点”到“分布式”
#### 1. 单节点部署方案（适合小机房）
```bash
# 一键部署脚本（示例）
#!/bin/bash

# 1. 安装依赖
apt-get update
apt-get install -y python3.9 python3.9-venv mongodb redis-server suricata

# 2. 创建虚拟环境
python3.9 -m venv compliance-env
source compliance-env/bin/activate

# 3. 安装Python包
pip install fastapi[all] pymongo redis requests playwright celery

# 4. 配置Suricata
cp /etc/suricata/suricata.yaml /etc/suricata/suricata.yaml.bak
# 添加自定义规则
echo 'alert tcp any any -> any 80 (msg:"疑似HTTP洪水攻击"; ...)' > /etc/suricata/rules/compliance.rules

# 5. 启动服务
systemctl start mongodb redis suricata

# 6. 启动应用
uvicorn main:app --host 0.0.0.0 --port 8000 &
celery -A tasks worker --loglevel=info &
```

#### 2. 分布式部署架构（适合大规模IDC）
```
┌───────────────────────────────────────────────────────────────┐
│                         负载均衡层                              │
│                     (Nginx/LVS)                                │
└───────────────────┬────────────────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────────────────┐
│                         API服务集群                             │
│  (Web管理后台 + 检测API)                                        │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                         │
│  │ 节点1   │  │ 节点2   │  │ 节点3   │                         │
│  └─────────┘  └─────────┘  └─────────┘                         │
└───────────────────┬────────────────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────────────────┐
│                         消息队列层                              │
│                      (RabbitMQ集群)                             │
└───────────────────┬────────────────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────────────────┐
│                         任务处理集群                             │
│  (爬虫任务 + 检测任务 + 告警任务)                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐                         │
│  │ 节点A   │  │ 节点B   │  │ 节点C   │                         │
│  └─────────┘  └─────────┘  └─────────┘                         │
└───────────────────┬────────────────────────────────────────────┘
                    │
┌───────────────────▼────────────────────────────────────────────┐
│                         数据存储集群                             │
│  ┌───────────┐  ┌───────────┐  ┌────────────┐                    │
│  │ MongoDB   │  │ Redis     │  │ Elasticsearch│                    │
│  │ 集群      │  │ 集群      │  │ 集群        │                    │
│  └───────────┘  └───────────┘  └────────────┘                    │
└───────────────────────────────────────────────────────────────┘
```


### 四、开发节奏：分阶段迭代
#### 1. 第一阶段（1-2个月）：验证核心功能
- 实现网站文本/图片合规检测（调用第三方API）
- 对接备案查询API，检测未备案网站
- 基础告警通知（邮件+短信）

#### 2. 第二阶段（2-4个月）：增强检测能力
- 部署流量分析模块（Suricata+自定义规则）
- 实现网站全量爬取（含子域名）
- 完善处置流程（自动暂停服务器、生成合规报告）

#### 3. 第三阶段（4-6个月）：提升可用性
- 分布式部署架构
- 自动化测试与CI/CD
- 数据可视化仪表盘（展示违规趋势、TOP风险用户）


### 五、避坑指南
1. **合规性风险**：
   - 避免存储用户完整内容（如网页HTML），只存检测结果和关键证据
   - 定期审计数据访问日志，符合《网络安全法》要求

2. **性能优化**：
   - 爬取频率限制（每域名每天不超过2次）
   - 流量镜像采用抽样（如10%流量）降低负载

3. **成本控制**：
   - 第三方API用量优化（如合并文本请求、图片批量处理）
   - 非核心功能优先用开源方案（如Suricata替代商用IDS）


### 六、工具推荐
1. **第三方API服务**：
   - 百度AI内容审核：https://ai.baidu.com/tech/contentcensoring
   - 阿里云内容安全：https://www.aliyun.com/product/cs
   - 工信部ICP备案查询：https://beian.miit.gov.cn/（需申请接口）

2. **开源工具**：
   - Suricata：https://suricata.io/（网络流量检测）
   - Scrapy：https://scrapy.org/（网站爬取）
   - Playwright：https://playwright.dev/（浏览器自动化）

3. **监控告警**：
   - Grafana：https://grafana.com/（可视化）
   - Prometheus：https://prometheus.io/（指标收集）

---
