"""同步引擎：全量/增量离线同步、字段自动映射、自动建表、批量分页读取"""
import time
from datetime import datetime
from sqlalchemy import (
    MetaData, Table, Column, text, select, insert, func, inspect,
)
from sqlalchemy.exc import SQLAlchemyError

from app.models import Datasource, TaskLog, SyncTask
from app.security import decrypt_secret
from app.services.db_engine import make_engine


def _build_where(task: SyncTask) -> str:
    parts = []
    if task.where_condition and task.where_condition.strip():
        parts.append(task.where_condition.strip())
    if task.mode == "incremental" and task.inc_field:
        last = task.last_sync_value
        if last:
            parts.append(f"{task.inc_field} > '{last}'")
        else:
            parts.append(f"{task.inc_field} IS NOT NULL")
    return " AND ".join(parts)


def _same_database(source, target) -> bool:
    """判断两个数据源是否指向同一个可执行 INSERT...SELECT 的数据库。"""
    return all([
        source.db_type == target.db_type,
        source.host == target.host,
        source.port == target.port,
        source.database == target.database,
        source.username == target.username,
    ])


def _quoted_columns(table, cols, dialect) -> str:
    preparer = dialect.identifier_preparer
    return ", ".join(preparer.quote(table.c[col].name) for col in cols)


def run_task_once(db, task: SyncTask) -> dict:
    """执行一次同步任务，返回 {status, rows, duration, error}"""
    started = time.time()
    log = TaskLog(
        user_id=task.user_id, task_id=task.id, task_name=task.name, status="running"
    )
    db.add(log)
    db.commit()

    src_engine = tgt_engine = None
    src_conn = tgt_conn = None
    try:
        source_table = (task.source_table or "").strip()
        target_table = (task.target_table or "").strip() or source_table
        if not source_table:
            raise ValueError("源表名不能为空")

        src = db.query(Datasource).get(task.source_id)
        tgt = db.query(Datasource).get(task.target_id)
        if not src or not tgt:
            raise ValueError("源或目标数据源不存在")

        # 解密密码
        src.password = decrypt_secret(src.password)
        tgt.password = decrypt_secret(tgt.password)
        src_engine = make_engine(src)
        tgt_engine = make_engine(tgt)
        src_conn = src_engine.connect()
        tgt_conn = tgt_engine.connect()

        # 读取源表结构
        src_meta = MetaData()
        if not inspect(src_engine).has_table(source_table):
            raise ValueError(f"源表不存在: {source_table}")
        src_table = Table(source_table, src_meta, autoload_with=src_engine)

        # 字段（自动映射 / 手动指定）
        if task.columns and task.columns.strip():
            cols = [c.strip() for c in task.columns.split(",") if c.strip()]
        else:
            cols = [c.name for c in src_table.columns]
        missing = [c for c in cols if c not in src_table.c]
        if missing:
            raise ValueError(f"字段在源表中不存在: {missing}")

        # 确保目标表存在（自动建表）
        tgt_meta = MetaData()
        if not inspect(tgt_engine).has_table(target_table):
            new_cols = [Column(c.name, c.type) for c in src_table.columns
                        if c.name in cols]
            tgt_table = Table(target_table, tgt_meta, *new_cols)
            tgt_meta.create_all(tgt_engine)
        else:
            tgt_table = Table(target_table, tgt_meta, autoload_with=tgt_engine)

        where_expr = _build_where(task)
        order_col = (
            list(src_table.primary_key.columns)[0].name
            if src_table.primary_key.columns
            else cols[0]
        )

        # 一个目标事务覆盖整个同步，减少每批连接、事务提交和 fsync 开销。
        target_transaction = tgt_conn.begin()
        total = 0
        max_inc = None
        batch = max(1, task.batch_size or 5000)
        try:
            # 清空也纳入同一事务，失败时可完整回滚。
            if task.mode == "full" and task.write_mode == "truncate":
                tgt_conn.execute(text(f"DELETE FROM {target_table}"))

            # 同一数据库内直接 INSERT...SELECT，避免数据经过 Python 内存和网络往返。
            if _same_database(src, tgt) and source_table != target_table:
                preparer = tgt_engine.dialect.identifier_preparer
                quoted_source = preparer.quote(source_table)
                quoted_target = preparer.quote(target_table)
                quoted_cols = _quoted_columns(src_table, cols, tgt_engine.dialect)
                select_sql = (
                    f"INSERT INTO {quoted_target} ({quoted_cols}) "
                    f"SELECT {quoted_cols} FROM {quoted_source}"
                )
                if where_expr:
                    select_sql += f" WHERE {where_expr}"

                count_sql = f"SELECT COUNT(*) FROM {quoted_source}"
                if where_expr:
                    count_sql += f" WHERE {where_expr}"
                total = int(tgt_conn.execute(text(count_sql)).scalar_one())
                if task.inc_field:
                    quoted_inc = preparer.quote(task.inc_field)
                    max_sql = f"SELECT MAX({quoted_inc}) FROM {quoted_source}"
                    if where_expr:
                        max_sql += f" WHERE {where_expr}"
                    max_inc = tgt_conn.execute(text(max_sql)).scalar_one()
                tgt_conn.execute(text(select_sql))
            else:
                # 跨数据库时使用一次流式查询，避免重复 OFFSET 查询。
                sel = select(*[src_table.c[c] for c in cols])
                if where_expr:
                    sel = sel.where(text(where_expr))
                sel = sel.order_by(src_table.c[order_col])
                result = src_conn.execution_options(stream_results=True).execute(sel)
                mapping_result = result.mappings()
                while True:
                    rows = mapping_result.fetchmany(batch)
                    if not rows:
                        break

                    payload = [dict(r) for r in rows]
                    tgt_conn.execution_options(
                        insertmanyvalues_page_size=batch
                    ).execute(insert(tgt_table), payload)

                    total += len(payload)
                    if task.inc_field:
                        for r in payload:
                            v = r.get(task.inc_field)
                            if v is not None and (max_inc is None or v > max_inc):
                                max_inc = v

                    # 超时保护
                    if task.timeout and (time.time() - started) > task.timeout:
                        raise TimeoutError("同步超过设定的超时时间，已终止")

            if task.timeout and (time.time() - started) > task.timeout:
                raise TimeoutError("同步超过设定的超时时间，已终止")
            target_transaction.commit()
        except Exception:
            target_transaction.rollback()
            raise

        # 更新任务状态
        task.status = "success"
        task.last_run_at = datetime.now()
        task.last_rows = total
        task.last_duration = round(time.time() - started, 2)
        if max_inc is not None:
            # 全量/增量均记录增量水位，供下次增量同步续传
            task.last_sync_value = str(max_inc)
        db.commit()

        duration = round(time.time() - started, 2)
        log.status = "success"
        log.rows = total
        log.duration = duration
        log.finished_at = datetime.now()
        db.commit()

        _after_sync(db, task, success=True, error="")
        return {"status": "success", "rows": total, "duration": duration, "error": ""}

    except Exception as e:
        err = str(e)
        duration = round(time.time() - started, 2)
        task.status = "failed"
        task.last_run_at = datetime.now()
        task.last_rows = 0
        task.last_duration = duration
        db.commit()

        log.status = "failed"
        log.error = err[:2000]
        log.duration = duration
        log.finished_at = datetime.now()
        db.commit()

        _after_sync(db, task, success=False, error=err)
        return {"status": "failed", "rows": 0, "duration": duration, "error": err}

    finally:
        if src_conn:
            src_conn.close()
        if tgt_conn:
            tgt_conn.close()
        if src_engine:
            src_engine.dispose()
        if tgt_engine:
            tgt_engine.dispose()


def _after_sync(db, task: SyncTask, success: bool, error: str):
    """同步后处理：失败告警"""
    if not success:
        try:
            from app.services.alert import notify_failure
            notify_failure(db, task, error)
        except Exception:
            pass
