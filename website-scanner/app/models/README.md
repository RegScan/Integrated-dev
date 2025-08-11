# 数据库模型模块

**功能职责：**

本模块使用SQLAlchemy ORM定义了与`website-scanner`服务相关的所有数据库表结构。这些模型是业务逻辑与数据库之间的桥梁，确保了数据的一致性和完整性。

## 文件说明

- `__init__.py`: Python包标识文件。
- `base.py`: 定义所有模型的基类`Base`，并可能包含一些通用的字段或方法（如`id`, `created_at`, `updated_at`）。
- `scan.py`: 定义与扫描任务相关的模型。
  - **`ScanTask`**: 存储扫描任务的基本信息，如目标网站URL、扫描配置、任务状态（等待、进行中、完成、失败）、创建时间等。
- `result.py`: 定义与扫描结果相关的模型。
  - **`ScanResult`**: 存储具体的扫描发现。每个实例代表一个违规项，包含所属的`ScanTask` ID、风险URL、风险类型（如敏感词、非法外链）、违规内容摘要、截图路径、发现时间等。
- `website.py`: 定义与网站信息相关的模型。
  - **`WebsiteInfo`**: 存储网站的基本信息，如域名、ICP备案号、主体信息等。

## 开发规范

- **单一模型文件**: 每个核心业务实体（如`ScanTask`, `ScanResult`）应有其独立的模型文件，保持结构清晰。
- **明确的关系**: 使用SQLAlchemy的`relationship`和`ForeignKey`来明确定义模型之间的关系（如`ScanTask`与`ScanResult`之间的一对多关系）。
- **索引**: 为经常用于查询和排序的字段（如`status`, `created_at`, `risk_type`）添加数据库索引（`index=True`），以优化查询性能。
- **约束**: 使用`CheckConstraint`或`UniqueConstraint`来强制执行数据层面的业务规则（如状态枚举值、唯一性要求）。
- **懒加载与预加载**: 明确指定关系加载策略（如使用`lazy='joined'`或`selectinload`），避免N+1查询问题。
- **Alembic集成**: 所有的模型变更都必须通过Alembic生成和管理数据库迁移脚本，禁止手动修改数据库结构。