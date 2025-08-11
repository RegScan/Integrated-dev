from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from typing import Generator
import os
from urllib.parse import quote_plus

# 数据库配置
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "sqlite:///./alert_handler.db"  # 默认使用SQLite数据库
)

# 如果使用MySQL，可以使用以下格式：
# DATABASE_URL = "mysql+pymysql://username:password@localhost:3306/alert_handler"

# 如果使用PostgreSQL，可以使用以下格式：
# DATABASE_URL = "postgresql://username:password@localhost:5432/alert_handler"

# 创建数据库引擎
if DATABASE_URL.startswith("sqlite"):
    # SQLite配置
    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},  # SQLite特有配置
        echo=False  # 设置为True可以看到SQL语句
    )
else:
    # MySQL/PostgreSQL配置
    engine = create_engine(
        DATABASE_URL,
        pool_size=20,  # 连接池大小
        max_overflow=30,  # 连接池溢出大小
        pool_pre_ping=True,  # 连接前ping检查
        pool_recycle=3600,  # 连接回收时间（秒）
        echo=False  # 设置为True可以看到SQL语句
    )

# 创建会话工厂
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine
)

# 创建基础模型类
Base = declarative_base()

# 创建元数据对象
metadata = MetaData()

def get_db() -> Generator[Session, None, None]:
    """
    获取数据库会话
    
    Yields:
        Session: 数据库会话对象
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        db.rollback()
        raise e
    finally:
        db.close()

def create_tables():
    """
    创建所有数据库表
    """
    try:
        Base.metadata.create_all(bind=engine)
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")
        raise e

def drop_tables():
    """
    删除所有数据库表
    """
    try:
        Base.metadata.drop_all(bind=engine)
        print("Database tables dropped successfully")
    except Exception as e:
        print(f"Error dropping database tables: {str(e)}")
        raise e

def init_db():
    """
    初始化数据库
    """
    try:
        # 导入所有模型以确保它们被注册
        from .models import alert, action
        
        # 创建表
        create_tables()
        
        print("Database initialized successfully")
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        raise e

def get_db_info():
    """
    获取数据库信息
    
    Returns:
        dict: 数据库信息
    """
    try:
        with engine.connect() as connection:
            # 获取数据库版本信息
            if DATABASE_URL.startswith("sqlite"):
                result = connection.execute("SELECT sqlite_version()")
                version = result.fetchone()[0]
                db_type = "SQLite"
            elif DATABASE_URL.startswith("mysql"):
                result = connection.execute("SELECT VERSION()")
                version = result.fetchone()[0]
                db_type = "MySQL"
            elif DATABASE_URL.startswith("postgresql"):
                result = connection.execute("SELECT version()")
                version = result.fetchone()[0]
                db_type = "PostgreSQL"
            else:
                version = "Unknown"
                db_type = "Unknown"
            
            return {
                "database_type": db_type,
                "database_version": version,
                "database_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL,
                "connection_pool_size": engine.pool.size() if hasattr(engine.pool, 'size') else "N/A",
                "connection_pool_checked_in": engine.pool.checkedin() if hasattr(engine.pool, 'checkedin') else "N/A",
                "connection_pool_checked_out": engine.pool.checkedout() if hasattr(engine.pool, 'checkedout') else "N/A"
            }
    except Exception as e:
        return {
            "error": str(e),
            "database_url": DATABASE_URL.split("@")[-1] if "@" in DATABASE_URL else DATABASE_URL
        }

class DatabaseManager:
    """
    数据库管理器类
    """
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def get_session(self) -> Session:
        """
        获取数据库会话
        
        Returns:
            Session: 数据库会话对象
        """
        return self.SessionLocal()
    
    def close_session(self, session: Session):
        """
        关闭数据库会话
        
        Args:
            session: 数据库会话对象
        """
        try:
            session.close()
        except Exception as e:
            print(f"Error closing database session: {str(e)}")
    
    def execute_query(self, query: str, params: dict = None):
        """
        执行SQL查询
        
        Args:
            query: SQL查询语句
            params: 查询参数
            
        Returns:
            查询结果
        """
        session = self.get_session()
        try:
            if params:
                result = session.execute(query, params)
            else:
                result = session.execute(query)
            session.commit()
            return result.fetchall()
        except Exception as e:
            session.rollback()
            raise e
        finally:
            self.close_session(session)
    
    def check_connection(self) -> bool:
        """
        检查数据库连接
        
        Returns:
            bool: 连接状态
        """
        try:
            with self.engine.connect() as connection:
                connection.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def get_table_info(self) -> dict:
        """
        获取表信息
        
        Returns:
            dict: 表信息
        """
        try:
            inspector = engine.inspect(self.engine)
            tables = inspector.get_table_names()
            
            table_info = {}
            for table in tables:
                columns = inspector.get_columns(table)
                table_info[table] = {
                    "columns": [col['name'] for col in columns],
                    "column_count": len(columns)
                }
            
            return table_info
        except Exception as e:
            return {"error": str(e)}

# 创建数据库管理器实例
db_manager = DatabaseManager()

if __name__ == "__main__":
    # 如果直接运行此文件，则初始化数据库
    print("Initializing database...")
    init_db()
    print("Database initialization completed.")
    
    # 显示数据库信息
    info = get_db_info()
    print(f"Database info: {info}")