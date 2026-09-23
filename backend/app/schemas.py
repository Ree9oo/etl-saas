"""Pydantic 请求/响应模型（统一 code/msg/data 返回由响应工具处理）"""
from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator


# ---------- 通用 ----------
class ResponseModel(BaseModel):
    code: int = 0
    msg: str = "ok"
    data: object = None


# ---------- 鉴权 ----------
class LoginRequest(BaseModel):
    username: str
    password: str


class LoginResponse(BaseModel):
    token: str
    username: str
    role: str
    plan: str


class RegisterRequest(BaseModel):
    username: str = Field(min_length=3, max_length=64)
    password: str = Field(min_length=6, max_length=128)


class UserOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    username: str
    role: str
    plan: str
    created_at: Optional[datetime] = None


# ---------- 数据源 ----------
class DatasourceCreate(BaseModel):
    name: str
    db_type: str
    host: str
    port: int
    username: str
    password: str = ""
    database: str
    charset: str = "utf8mb4"
    extra: str = ""


class DatasourceUpdate(BaseModel):
    name: Optional[str] = None
    db_type: Optional[str] = None
    host: Optional[str] = None
    port: Optional[int] = None
    username: Optional[str] = None
    password: Optional[str] = None
    database: Optional[str] = None
    charset: Optional[str] = None
    extra: Optional[str] = None


class DatasourceTest(BaseModel):
    db_type: str
    host: str
    port: int
    username: str
    password: str = ""
    database: str
    charset: str = "utf8mb4"
    extra: str = ""


class DatasourceOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    db_type: str
    host: str
    port: int
    username: str
    database: str
    charset: str
    extra: str
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


# ---------- 同步任务 ----------
class TaskCreate(BaseModel):
    name: str
    source_id: int
    target_id: int
    source_table: str
    target_table: str
    mode: str = "full"  # full / incremental
    write_mode: str = "append"  # append / truncate
    inc_field: str = ""
    where_condition: str = ""
    columns: str = ""
    batch_size: int = 5000
    cron: str = ""
    enabled: bool = False
    retry_count: int = 0
    timeout: int = 3600

    @field_validator("source_table")
    @classmethod
    def validate_table_name(cls, value: str) -> str:
        value = value.strip()
        if not value:
            raise ValueError("表名不能为空")
        return value

    @field_validator("target_table")
    @classmethod
    def normalize_target_table(cls, value: str) -> str:
        return value.strip()


class TaskUpdate(BaseModel):
    name: Optional[str] = None
    source_id: Optional[int] = None
    target_id: Optional[int] = None
    source_table: Optional[str] = None
    target_table: Optional[str] = None
    mode: Optional[str] = None
    write_mode: Optional[str] = None
    inc_field: Optional[str] = None
    where_condition: Optional[str] = None
    columns: Optional[str] = None
    batch_size: Optional[int] = None
    cron: Optional[str] = None
    enabled: Optional[bool] = None
    retry_count: Optional[int] = None
    timeout: Optional[int] = None

    @field_validator("source_table")
    @classmethod
    def validate_table_name(cls, value: Optional[str]) -> Optional[str]:
        if value is None:
            return value
        value = value.strip()
        if not value:
            raise ValueError("表名不能为空")
        return value

    @field_validator("target_table")
    @classmethod
    def normalize_target_table(cls, value: Optional[str]) -> Optional[str]:
        return value.strip() if value is not None else value


class TaskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    name: str
    source_id: int
    target_id: int
    source_table: str
    target_table: str
    mode: str
    write_mode: str
    inc_field: str
    where_condition: str
    columns: str
    batch_size: int
    cron: str
    enabled: bool
    status: str
    last_run_at: Optional[datetime] = None
    last_sync_value: str
    retry_count: int
    timeout: int
    last_rows: int
    last_duration: float
    created_at: Optional[datetime] = None


# ---------- 日志 ----------
class LogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    task_id: int
    task_name: str
    status: str
    rows: int
    duration: float
    error: str
    started_at: Optional[datetime] = None
    finished_at: Optional[datetime] = None


class OperationLogOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: int
    user_id: int
    username: str
    module: str
    action: str
    detail: str
    ip_address: str
    created_at: Optional[datetime] = None


# ---------- 系统配置 / 授权 ----------
class AlertConfigIn(BaseModel):
    dingtalk_webhook: str = ""
    wechat_webhook: str = ""


class AlertConfigOut(BaseModel):
    dingtalk_webhook: str = ""
    wechat_webhook: str = ""


class LicenseActivate(BaseModel):
    license_code: str


class LicenseInfo(BaseModel):
    plan: str
    max_datasources: int
    max_tasks: int
    datasources_used: int
    tasks_used: int
    activated: bool
    holder: str = ""
    expires_at: Optional[str] = None


class StatsOut(BaseModel):
    datasources: int
    tasks: int
    tasks_enabled: int
    logs_total: int
    logs_failed: int
    logs_success: int
