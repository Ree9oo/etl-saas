"""ORM 数据模型：用户、数据源、同步任务、任务日志、系统配置、授权记录

所有表与字段均带中文注释（comment），由 SQLAlchemy 在建表时写入，
便于在 MySQL 中直接查看字段含义。已存在的库可用 backend/add_comments.py 补注释。
"""
from datetime import datetime

from sqlalchemy import (
    Column, Integer, String, Text, Boolean, DateTime, ForeignKey, Float, UniqueConstraint,
)
from sqlalchemy.sql import func

from app.database import Base


class TimestampMixin:
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="创建时间")
    updated_at = Column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False, comment="更新时间"
    )


class User(Base, TimestampMixin):
    __tablename__ = "users"
    __comment__ = "平台用户"

    id = Column(Integer, primary_key=True, index=True, comment="用户ID")
    username = Column(String(64), unique=True, index=True, nullable=False, comment="用户名")
    password_hash = Column(String(255), nullable=False, comment="密码哈希值")
    role = Column(String(16), default="user", nullable=False, comment="角色(admin/user)")
    plan = Column(String(16), default="free", nullable=False, comment="套餐(free/paid)")


class Datasource(Base, TimestampMixin):
    __tablename__ = "datasources"
    __comment__ = "数据源配置"
    __table_args__ = (UniqueConstraint("user_id", "name", name="uq_ds_user_name"),)

    id = Column(Integer, primary_key=True, index=True, comment="数据源ID")
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False, comment="所属用户ID")
    name = Column(String(128), nullable=False, comment="数据源名称")
    db_type = Column(String(32), nullable=False, comment="数据库类型(mysql/sqlserver/postgresql/oracle/dm/sqlite)")
    host = Column(String(255), nullable=False, comment="主机地址")
    port = Column(Integer, nullable=False, comment="端口")
    username = Column(String(128), nullable=False, comment="连接用户名")
    password = Column(Text, nullable=False, comment="连接密码(已加密)")
    database = Column(String(128), nullable=False, comment="数据库名/SID")
    charset = Column(String(32), default="utf8mb4", comment="字符集")
    extra = Column(Text, default="", comment="扩展参数(JSON)")


class SyncTask(Base, TimestampMixin):
    __tablename__ = "sync_tasks"
    __comment__ = "同步任务"

    id = Column(Integer, primary_key=True, index=True, comment="任务ID")
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False, comment="所属用户ID")
    name = Column(String(128), nullable=False, comment="任务名称")
    source_id = Column(Integer, ForeignKey("datasources.id"), nullable=False, comment="源数据源ID")
    target_id = Column(Integer, ForeignKey("datasources.id"), nullable=False, comment="目标数据源ID")
    source_table = Column(String(128), nullable=False, comment="源表名")
    target_table = Column(String(128), nullable=False, comment="目标表名")
    mode = Column(String(16), default="full", nullable=False, comment="同步模式(full/incremental)")
    write_mode = Column(String(16), default="append", nullable=False, comment="写入模式(append/truncate)")
    inc_field = Column(String(64), default="", comment="增量字段名(update_time等)")
    where_condition = Column(Text, default="", comment="自定义WHERE条件")
    columns = Column(Text, default="", comment="指定字段(逗号分隔,空=全部)")
    batch_size = Column(Integer, default=5000, nullable=False, comment="每批读取/写入行数")
    cron = Column(String(64), default="", nullable=False, comment="Cron表达式(空=不定时)")
    enabled = Column(Boolean, default=False, nullable=False, comment="是否启用调度")
    status = Column(String(16), default="idle", nullable=False, comment="任务状态(idle/running/success/failed)")
    last_run_at = Column(DateTime, nullable=True, comment="上次运行时间")
    last_sync_value = Column(String(64), default="", comment="上次增量水位值")
    retry_count = Column(Integer, default=0, nullable=False, comment="失败重试次数")
    timeout = Column(Integer, default=3600, nullable=False, comment="超时秒数")
    last_rows = Column(Integer, default=0, nullable=False, comment="上次同步行数")
    last_duration = Column(Float, default=0.0, nullable=False, comment="上次同步耗时(秒)")


class TaskLog(Base, TimestampMixin):
    __tablename__ = "task_logs"
    __comment__ = "任务执行日志"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False, comment="所属用户ID")
    task_id = Column(Integer, ForeignKey("sync_tasks.id"), index=True, nullable=False, comment="任务ID")
    task_name = Column(String(128), default="", comment="任务名称")
    status = Column(String(16), default="running", nullable=False, comment="执行状态(running/success/failed)")
    rows = Column(Integer, default=0, nullable=False, comment="同步行数")
    duration = Column(Float, default=0.0, nullable=False, comment="耗时(秒)")
    error = Column(Text, default="", comment="错误信息")
    started_at = Column(DateTime, default=func.now(), nullable=False, comment="开始时间")
    finished_at = Column(DateTime, nullable=True, comment="完成时间")


class OperationLog(Base):
    __tablename__ = "user_action_logs"
    __comment__ = "系统操作日志"

    id = Column(Integer, primary_key=True, index=True, comment="日志ID")
    user_id = Column(Integer, ForeignKey("users.id"), index=True, nullable=False, comment="操作人ID")
    username = Column(String(64), nullable=False, comment="操作人用户名")
    module = Column(String(64), nullable=False, comment="功能模块")
    action = Column(String(64), nullable=False, comment="操作动作")
    detail = Column(Text, default="", comment="操作详情")
    ip_address = Column(String(64), default="", nullable=False, comment="访问IP")
    created_at = Column(DateTime, default=func.now(), nullable=False, comment="操作时间")


class SystemConfig(Base, TimestampMixin):
    __tablename__ = "system_configs"
    __comment__ = "系统配置"
    __table_args__ = (UniqueConstraint("key", name="uq_syscfg_key"),)

    id = Column(Integer, primary_key=True, index=True, comment="配置ID")
    key = Column(String(64), unique=True, index=True, nullable=False, comment="配置键")
    value = Column(Text, default="", comment="配置值")


class License(Base, TimestampMixin):
    __tablename__ = "licenses"
    __comment__ = "授权记录"

    id = Column(Integer, primary_key=True, index=True, comment="授权ID")
    license_code = Column(String(128), unique=True, index=True, nullable=False, comment="授权码")
    plan = Column(String(16), default="paid", nullable=False, comment="套餐(paid)")
    status = Column(String(16), default="active", nullable=False, comment="状态(active/invalid)")
    holder = Column(String(128), default="", comment="持有者")
    activated_at = Column(DateTime, nullable=True, comment="激活时间")
    expires_at = Column(DateTime, nullable=True, comment="过期时间")
    remark = Column(Text, default="", comment="备注")
