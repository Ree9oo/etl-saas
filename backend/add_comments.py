#!/usr/bin/env python3
"""为【已存在】的数据库表 / 字段补充中文注释（MySQL）

本系统表结构由 SQLAlchemy ORM 定义，字段注释写在 app/models.py 的 Column(comment=...)。
若你之前已经建表（未带注释），可运行本脚本，把 models.py 中定义的
表注释 / 字段注释同步到现有数据库（通过 ALTER TABLE ... MODIFY / COMMENT 实现）。

用法:
  cd backend
  export DATABASE_URL="mysql+pymysql://root:你的密码@127.0.0.1:3306/etl_saas?charset=utf8mb4"

  python add_comments.py           # 仅打印将执行的 SQL（dry-run，安全）
  python add_comments.py --apply   # 真正执行，把注释写进数据库

说明:
  * 注释单一来源 = models.py，改模型即同步改写脚本行为，无需维护两份映射。
  * 对字段使用 MODIFY COLUMN 重建并附加 COMMENT；会自动保留 NOT NULL / AUTO_INCREMENT。
  * 主键整型列会补回 AUTO_INCREMENT，避免自增属性丢失。
  * 默认仅打印 SQL，加 --apply 才真正改库；生产库请先 dry-run 核对。
"""
import argparse
import os
import sys

# 将 backend/ 加入路径，允许以脚本方式直接运行
BACKEND_DIR = os.path.dirname(os.path.abspath(__file__))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from sqlalchemy import create_engine, inspect, text
from app.database import Base
from app import models  # noqa: F401  注册所有 ORM 模型
from app.config import settings


def _esc(s: str) -> str:
    """转义 SQL 单引号（MySQL 用两个单引号表示一个）。"""
    return (s or "").replace("'", "''")


def _format_default(d):
    """把 Python 默认值转成可拼进 DDL 的片段（None 表示不写 DEFAULT）。"""
    if d is None:
        return ""
    if isinstance(d, (int, float)):
        return f" DEFAULT {d}"
    return f" DEFAULT '{_esc(str(d))}'"


def collect_comments():
    """从 ORM 模型收集 (表注释, {列名: 注释})。"""
    table_comments = {}
    column_comments = {}
    for tname, table in Base.metadata.tables.items():
        table_comments[tname] = getattr(table, "comment", None)
        column_comments[tname] = {
            c.name: c.comment for c in table.columns if c.comment
        }
    return table_comments, column_comments


def build_alters(engine):
    insp = inspect(engine)
    table_comments, column_comments = collect_comments()
    existing_tables = set(insp.get_table_names())
    sqls = []

    for tname, cols in column_comments.items():
        if tname not in existing_tables:
            print(f"[skip] 表不存在，跳过: {tname}")
            continue

        # 表级注释
        tcomment = table_comments.get(tname)
        if tcomment:
            sqls.append(f"ALTER TABLE `{tname}` COMMENT '{_esc(tcomment)}';")

        # 字段注释：读取现有列定义，重建 MODIFY 语句并附加 COMMENT
        db_cols = {c["name"]: c for c in insp.get_columns(tname)}
        pk_cols = set(
            (insp.get_pk_constraint(tname) or {}).get("constrained_columns") or []
        )
        for col_name, comment in cols.items():
            if col_name not in db_cols:
                print(f"[skip] 字段不存在，跳过: {tname}.{col_name}")
                continue
            col = db_cols[col_name]
            col_type = str(col["type"])
            null_clause = "NULL" if col.get("nullable", True) else "NOT NULL"
            autoinc = ""
            if col_name in pk_cols and "int" in col_type.lower():
                autoinc = " AUTO_INCREMENT"
            default_clause = _format_default(col.get("default"))
            sqls.append(
                f"ALTER TABLE `{tname}` MODIFY COLUMN `{col_name}` "
                f"{col_type} {null_clause}{autoinc}{default_clause} "
                f"COMMENT '{_esc(comment)}';"
            )
    return sqls


def main():
    ap = argparse.ArgumentParser(description="为已存在表补充中文注释 (MySQL)")
    ap.add_argument("--apply", action="store_true", help="真正执行；默认仅打印 SQL (dry-run)")
    args = ap.parse_args()

    print(f"DATABASE_URL = {settings.DATABASE_URL}\n")
    engine = create_engine(settings.DATABASE_URL, pool_pre_ping=True, future=True)
    sqls = build_alters(engine)

    if not sqls:
        print("没有需要补充的注释（或目标表不存在）。")
        return

    print(f"将执行 {len(sqls)} 条 ALTER 语句：\n")
    for s in sqls:
        print("  " + s)

    if not args.apply:
        print("\n[dry-run] 未改动数据库。加 --apply 参数以真正写入。")
        return

    with engine.begin() as conn:
        for s in sqls:
            conn.execute(text(s))
    print(f"\n✅ 已为 {len(sqls)} 个对象补充注释。")


if __name__ == "__main__":
    main()
