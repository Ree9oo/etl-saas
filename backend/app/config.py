"""系统配置

通过环境变量覆盖默认值。
本地零配置启动默认使用 SQLite；生产/商用可设置 DATABASE_URL 指向 MySQL。
"""
import os
from datetime import timedelta
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    # 基础
    APP_NAME: str = "轻量多源数据同步 ETL SaaS 系统"
    API_PREFIX: str = "/api"
    DEBUG: bool = True

    # 数据库：默认 SQLite 以保证开箱即用，可切换为 MySQL
    # MySQL 示例: mysql+pymysql://user:pass@host:3306/etl_saas?charset=utf8mb4
    DATABASE_URL: str = os.getenv(
        "DATABASE_URL", "sqlite:///./etl_saas.db"
    )

    # JWT
    SECRET_KEY: str = os.getenv(
        "SECRET_KEY", "etl-saas-change-me-in-production-2024"
    )
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(
        os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440")
    )
    JWT_TOKEN_TTL: timedelta = timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    # 数据源密码加密密钥（Fernet）
    FERNET_KEY: str = os.getenv("FERNET_KEY", "")

    # 默认管理员（首次启动自动创建）
    INIT_ADMIN_USERNAME: str = os.getenv("INIT_ADMIN_USERNAME", "admin")
    INIT_ADMIN_PASSWORD: str = os.getenv("INIT_ADMIN_PASSWORD", "admin123")

    # 商业化免费额度
    FREE_MAX_DATASOURCES: int = int(os.getenv("FREE_MAX_DATASOURCES", "3"))
    FREE_MAX_TASKS: int = int(os.getenv("FREE_MAX_TASKS", "5"))

    # 同步引擎默认参数
    SYNC_BATCH_SIZE: int = int(os.getenv("SYNC_BATCH_SIZE", "5000"))
    SYNC_TASK_TIMEOUT: int = int(os.getenv("SYNC_TASK_TIMEOUT", "3600"))

    # 调度器
    SCHEDULER_TIMEZONE: str = os.getenv("SCHEDULER_TIMEZONE", "Asia/Shanghai")

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


settings = Settings()
