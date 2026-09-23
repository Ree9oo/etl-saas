"""多数据库连接引擎工厂：统一封装 MySQL/SQLServer/PostgreSQL/Oracle/达梦"""
from sqlalchemy import create_engine, inspect, select
from sqlalchemy.exc import SQLAlchemyError

from app.models import Datasource


def friendly_connection_error(db_type: str, error: Exception) -> str:
    """将驱动异常转换为面向用户的连接诊断提示。"""
    message = str(error)
    lowered = message.lower()
    label = {
        "mysql": "MySQL", "postgresql": "PostgreSQL", "sqlserver": "SQL Server",
        "oracle": "Oracle", "dm": "达梦", "sqlite": "SQLite",
    }.get(db_type, "数据库")
    if db_type == "dm" and (
        "can't load plugin" in lowered
        or "nosuchmoduleerror" in lowered
        or "dmpython" in lowered
    ):
        return "达梦驱动未安装或 SQLAlchemy 方言未加载，请在运行后端的 Python 环境安装官方 dmPython 驱动。"
    if "10061" in lowered or "connection refused" in lowered or "cannot connect" in lowered:
        return f"无法连接{label}，请检查主机地址、端口，以及数据库服务是否已启动。"
    if "timeout" in lowered or "timed out" in lowered:
        return f"连接{label}超时，请检查网络、防火墙和数据库服务状态。"
    if "password" in lowered or "authentication" in lowered or "ora-01017" in lowered:
        return f"{label}账号或密码不正确，请检查登录凭据。"
    if "does not exist" in lowered or "unknown database" in lowered or "ora-12514" in lowered:
        return f"{label}实例或数据库名称不存在，请检查数据库名或 Service Name。"
    return f"连接{label}失败，请检查连接配置后重试。"


def build_url(ds) -> str:
    """根据数据源类型构造 SQLAlchemy URL"""
    pwd = ds.password  # 调用方应传入已解密的密码
    host = ds.host
    port = ds.port
    db = ds.database
    if ds.db_type == "mysql":
        charset = ds.charset or "utf8mb4"
        return f"mysql+pymysql://{ds.username}:{pwd}@{host}:{port}/{db}?charset={charset}"
    if ds.db_type == "postgresql":
        return f"postgresql+psycopg2://{ds.username}:{pwd}@{host}:{port}/{db}"
    if ds.db_type == "sqlserver":
        return (
            f"mssql+pyodbc://{ds.username}:{pwd}@{host}:{port}/{db}"
            f"?driver=ODBC+Driver+17+for+SQL+Server"
        )
    if ds.db_type == "oracle":
        # 达梦/ Oracle easy connect：host:port/service_name
        service = db if db else "ORCL"
        return f"oracle+oracledb://{ds.username}:{pwd}@{host}:{port}/?service_name={service}"
    if ds.db_type == "sqlite":
        # 本地开发/演示：database 字段填入 sqlite 文件路径
        return f"sqlite:///{db}"
    if ds.db_type == "dm":
        # 达梦 SQLAlchemy dialect 使用 dmPython 驱动名。
        return f"dm+dmPython://{ds.username}:{pwd}@{host}:{port}/{db}"
    raise ValueError(f"不支持的数据库类型: {ds.db_type}")


def make_engine(ds, pool_size: int = 5):
    """创建带连接池的连接引擎。ds 可为 Datasource 对象或字典"""
    if isinstance(ds, dict):
        class _D:
            pass
        d = _D()
        for k, v in ds.items():
            setattr(d, k, v)
        ds = d
    url = build_url(ds)
    kwargs = dict(pool_pre_ping=True, pool_recycle=1800, future=True)
    if ds.db_type == "sqlite":
        kwargs["connect_args"] = {"check_same_thread": False}
    return create_engine(url, **kwargs)


def test_connection(ds) -> dict:
    """测试连通性，返回 {success, message}"""
    try:
        engine = make_engine(ds)
        with engine.connect() as conn:
            conn.execute(select(1))
        engine.dispose()
        return {"success": True, "message": "连接成功"}
    except SQLAlchemyError as e:
        return {"success": False, "message": friendly_connection_error(ds.db_type, e)}
    except Exception as e:
        return {"success": False, "message": friendly_connection_error(ds.db_type, e)}


def list_tables(ds) -> list:
    """列出数据源中的业务表"""
    engine = make_engine(ds)
    try:
        inspector = inspect(engine)
        return inspector.get_table_names()
    finally:
        engine.dispose()


def resolve_datasource(db, ds_id: int, user_id: int) -> Datasource:
    """按 id 与用户归属解析数据源"""
    from sqlalchemy.orm import Session
    ds = (
        db.query(Datasource)
        .filter(Datasource.id == ds_id, Datasource.user_id == user_id)
        .first()
    )
    if not ds:
        raise ValueError("数据源不存在或无权限")
    return ds
