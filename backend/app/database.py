"""数据库连接与会话管理"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

from app.config import settings

# SQLite 需开启单连接 + 检查同线程关闭
connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

engine = create_engine(
    settings.DATABASE_URL,
    connect_args=connect_args,
    pool_pre_ping=True,
    pool_recycle=3600,
    future=True,
)

SessionLocal = sessionmaker(
    bind=engine, autoflush=False, autocommit=False, future=True
)


class Base(DeclarativeBase):
    pass


def get_db():
    """FastAPI 依赖：提供数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """创建所有表（幂等）"""
    import app.models  # noqa: F401 确保模型已注册
    Base.metadata.create_all(bind=engine)
    with engine.begin() as connection:
        columns = {
            column["name"] for column in connection.dialect.get_columns(
                connection, "user_action_logs"
            )
        }
        if "ip_address" not in columns:
            connection.exec_driver_sql(
                "ALTER TABLE user_action_logs "
                "ADD COLUMN ip_address VARCHAR(64) NOT NULL DEFAULT ''"
            )
