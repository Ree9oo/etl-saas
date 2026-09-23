"""商业化额度控制：免费版 3 数据源 / 5 任务，付费版不限"""
from app.config import settings
from app.models import Datasource, SyncTask


def is_unlimited(user) -> bool:
    """付费用户 / 有效授权 无额度限制"""
    return user.plan == "paid"


def quota_max(user) -> tuple[int, int]:
    """返回 (最大数据源数, 最大任务数)，-1 表示不限"""
    if user.plan == "paid":
        return (-1, -1)
    return (settings.FREE_MAX_DATASOURCES, settings.FREE_MAX_TASKS)


def used_counts(db, user_id: int) -> tuple[int, int]:
    ds = db.query(Datasource).filter(Datasource.user_id == user_id).count()
    tasks = db.query(SyncTask).filter(SyncTask.user_id == user_id).count()
    return (ds, tasks)


def check_create(db, user, kind: str) -> tuple[bool, str]:
    """kind: 'datasource' | 'task'"""
    max_ds, max_tasks = quota_max(user)
    ds, tasks = used_counts(db, user.id)
    if kind == "datasource" and max_ds != -1 and ds >= max_ds:
        return (False, f"已达免费版数据源上限({max_ds})，请升级付费版或删除多余数据源")
    if kind == "task" and max_tasks != -1 and tasks >= max_tasks:
        return (False, f"已达免费版同步任务上限({max_tasks})，请升级付费版或删除多余任务")
    return (True, "ok")
