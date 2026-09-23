"""定时调度：基于 APScheduler 的 Cron 调度、启停、失败重试"""
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

from app.config import settings
from app.database import SessionLocal
from app.models import SyncTask
from app.services.sync import run_task_once
from app import models  # noqa: F401 确保模型已注册

_scheduler: BackgroundScheduler | None = None


def _job_id(task_id: int) -> str:
    return f"sync_task_{task_id}"


def _execute(task_id: int):
    """调度执行入口：带失败重试"""
    db = SessionLocal()
    try:
        task = db.query(SyncTask).filter(SyncTask.id == task_id).first()
        if not task or not task.enabled:
            return
        task.status = "running"
        db.commit()
        retries = max(0, task.retry_count or 0)
        attempt = 0
        result = None
        while attempt <= retries:
            result = run_task_once(db, task)
            if result["status"] == "success":
                break
            attempt += 1
    finally:
        db.close()


def _parse_cron(cron: str) -> CronTrigger | None:
    cron = (cron or "").strip()
    if not cron:
        return None
    try:
        return CronTrigger.from_crontab(cron, timezone=settings.SCHEDULER_TIMEZONE)
    except Exception:
        return None


def add_task_job(task: SyncTask):
    """注册/更新任务的定时作业"""
    if _scheduler is None:
        return
    trigger = _parse_cron(task.cron)
    if trigger is None:
        return
    _scheduler.add_job(
        _execute,
        trigger=trigger,
        id=_job_id(task.id),
        args=[task.id],
        replace_existing=True,
        max_instances=1,
        coalesce=True,
        misfire_grace_time=300,
    )


def remove_task_job(task_id: int):
    if _scheduler is None:
        return
    try:
        _scheduler.remove_job(_job_id(task_id))
    except Exception:
        pass


def sync_task_jobs(db):
    """根据数据库中的启用任务同步调度作业（启动时使用）"""
    if _scheduler is None:
        return
    for task in db.query(SyncTask).filter(SyncTask.enabled.is_(True)).all():
        add_task_job(task)


def init_scheduler():
    """初始化并启动调度器，加载所有启用任务"""
    global _scheduler
    if _scheduler is not None:
        return
    _scheduler = BackgroundScheduler(timezone=settings.SCHEDULER_TIMEZONE)
    _scheduler.start()
    db = SessionLocal()
    try:
        sync_task_jobs(db)
    finally:
        db.close()


def shutdown_scheduler():
    global _scheduler
    if _scheduler is not None:
        _scheduler.shutdown(wait=False)
        _scheduler = None
