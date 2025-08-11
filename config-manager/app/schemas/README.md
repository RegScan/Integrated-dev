# 数据校验模型模块 (Schemas)

**功能职责：**

本模块使用Pydantic定义了用于API数据校验和序列化的模型（Schema）。它作为API层和服务层之间的数据传输对象（DTO），确保了接口数据的规范性和安全性。

## 文件说明

- `__init__.py`: Python包标识文件。
- `config_schema.py`: 定义与配置相关的Pydantic模型，例如：
  - `ConfigCreate`: 创建配置时请求体的数据模型。
  - `ConfigUpdate`: 更新配置时请求体的数据模型。
  - `ConfigInDB`: 从数据库读取配置后，用于API响应的数据模型。
- `user_schema.py`: 定义与用户相关的Pydantic模型，例如：
  - `UserCreate`: 创建用户时的请求体模型，包含密码字段。
  - `UserUpdate`: 更新用户时的请求体模型。
  - `UserInDB`: 用于API响应的用户信息模型，**不应包含密码哈希**。

## 开发规范

- **请求与响应分离**：为创建（Create）、更新（Update）、读取（InDB/Response）等不同操作创建不同的Schema，精确控制字段的暴露。
- **数据校验**：充分利用Pydantic的校验功能，如`EmailStr`、`HttpUrl`、字段长度限制、正则表达式等，对输入数据进行严格校验。
- **密码字段处理**：在用于创建用户的Schema中包含密码字段，但在用于API响应的Schema中必须将其排除，防止密码泄露。
- **ORM模式**：可以启用Pydantic模型的`orm_mode`（在新版本中为`from_attributes=True`），使其能够方便地从SQLAlchemy等ORM对象创建实例。