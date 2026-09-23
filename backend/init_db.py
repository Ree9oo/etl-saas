#!/usr/bin/env python3
"""轻量多源数据同步 ETL SaaS 系统 — 数据库初始化脚本

本系统使用 SQLAlchemy ORM 自动建表，无需手写 DDL。本脚本提供一个【独立的初始化入口】，
支持以下能力（均幂等，可重复执行）：

  * MySQL 自动建库           --create-database
  * 创建所有数据表           （已存在则跳过）
  * 创建默认管理员账号       （读取 INIT_ADMIN_USERNAME / INIT_ADMIN_PASSWORD）
  * 仅导出建表 SQL 到文件     --export-sql schema.sql（不连接数据库）

============================ 典型用法（本地指定 MySQL）============================
  cd backend

  # 方式 A：一条命令搞定建库 + 建表 + 管理员
  export DATABASE_URL="mysql+pymysql://root:你的密码@127.0.0.1:3306/etl_saas?charset=utf8mb4"
  python init_db.py --create-database --init

  # 方式 B：先看一眼表结构 SQL，再手动去 MySQL 客户端执行
  python init_db.py --export-sql schema.sql
  mysql -uroot -p etl_saas < schema.sql

  # 方式 C：什么都不做，直接启动后端，启动时也会自动建表
  uvicorn app.main:app --host 0.0.0.0 --port 8000
====================================================================================
"""
import argparse
import os
import sys

# 将 backend/ 加入路径，便于以脚本方式直接运行（python init_db.py）
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from app.database import Base
from app import models  # noqa: F401  注册所有 ORM 模型
from app.config import settings


def make_engine():
    from sqlalchemy import create_engine
    return create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)


def create_database_if_mysql():
    """仅 MySQL：若目标库不存在则创建（需要连接账号具备 CREATE 权限）。"""
    url = settings.DATABASE_URL
    if not url.startswith("mysql"):
        print("[skip] 非 MySQL 数据源，跳过『建库』步骤（请自行创建数据库）。")
        return
    try:
        from urllib.parse import urlparse
        from sqlalchemy import create_engine, text
    except ImportError as e:
        print(f"[error] 缺少依赖: {e}")
        sys.exit(1)

    parsed = urlparse(url)
    db_name = parsed.path.lstrip("/").split("?")[0]
    if not db_name:
        print("[error] DATABASE_URL 中未指定数据库名，例如 .../etl_saas")
        sys.exit(1)
    # 连接到一个『不指定库』的地址，用于执行 CREATE DATABASE
    base_url = url.replace(parsed.path, "") if parsed.path else url
    engine = create_engine(base_url, pool_pre_ping=True)
    with engine.connect() as conn:
        conn.execute(text(
            f"CREATE DATABASE IF NOT EXISTS `{db_name}` "
            "CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
        ))
        print(f"[ok] 数据库已就绪: {db_name}")
    engine.dispose()


def create_tables():
    engine = make_engine()
    Base.metadata.create_all(bind=engine)
    tables = ", ".join(sorted(Base.metadata.tables.keys()))
    print(f"[ok] 已创建数据表({len(Base.metadata.tables)}张): {tables}")


def create_admin():
    # ensure_admin() 内部自行管理会话，读取 .env 中的管理员账号配置
    from app.security import ensure_admin
    ensure_admin()
    print(f"[ok] 默认管理员已就绪: {settings.INIT_ADMIN_USERNAME}")


def _pick_dialect():
    url = settings.DATABASE_URL
    if url.startswith("sqlite"):
        from sqlalchemy.dialects.sqlite import dialect as d
    else:
        from sqlalchemy.dialects.mysql import dialect as d
    return d()


def export_sql(path):
    """生成建表 DDL（根据 DATABASE_URL 选择方言），不连接数据库。"""
    from sqlalchemy.schema import CreateTable
    dialect = _pick_dialect()
    header = [
        "-- 轻量多源数据同步 ETL SaaS 系统 建表 SQL",
        f"-- 由 SQLAlchemy ORM 自动生成（dialect={dialect.name}），可直接在对应数据库中执行",
        "",
        "SET NAMES utf8mb4;" if dialect.name == "mysql" else "",
        "",
    ]
    parts = [ln for ln in header if ln != ""]
    for t in Base.metadata.sorted_tables:
        ddl = str(CreateTable(t).compile(dialect=dialect))
        parts.append(ddl.rstrip(";") + ";")
        parts.append("")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(parts))
    print(f"[ok] 建表 SQL 已导出到: {path}")


def main():
    ap = argparse.ArgumentParser(description="ETL SaaS 数据库初始化脚本")
    ap.add_argument("--create-database", action="store_true",
                    help="（仅 MySQL）若目标数据库不存在则自动创建")
    ap.add_argument("--init", action="store_true",
                    help="创建数据表 + 默认管理员（缺省即执行此步骤）")
    ap.add_argument("--export-sql", metavar="FILE",
                    help="仅导出建表 SQL 到文件，不连接数据库")
    args = ap.parse_args()

    print(f"DATABASE_URL = {settings.DATABASE_URL}\n")

    if args.export_sql:
        export_sql(args.export_sql)
        return

    if args.create_database:
        create_database_if_mysql()

    # 默认行为：建表 + 管理员（幂等）
    create_tables()
    create_admin()
    print("\n✅ 数据库初始化完成。")


if __name__ == "__main__":
    main()
