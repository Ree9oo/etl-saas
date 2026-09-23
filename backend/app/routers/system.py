"""系统配置与商业化授权模块：告警Webhook、授权信息、额度查询、激活"""
from fastapi import APIRouter, Depends, Query, Request
from datetime import datetime
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user, require_admin
from app.models import User, SystemConfig, License, Datasource, SyncTask, OperationLog
from app.schemas import (
    AlertConfigIn, AlertConfigOut, LicenseActivate, LicenseInfo, StatsOut,
    OperationLogOut,
)
from app.services.audit import record_action
from app.services.quota import quota_max, used_counts
from app.utils.response import resp

router = APIRouter(prefix="/api", tags=["系统"])


def _get(db, key: str) -> str:
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    return row.value if row else ""


def _set(db, key: str, value: str):
    row = db.query(SystemConfig).filter(SystemConfig.key == key).first()
    if row:
        row.value = value
    else:
        db.add(SystemConfig(key=key, value=value))


@router.get("/system/alert")
def get_alert(user: User = Depends(require_admin),
              db: Session = Depends(get_db)):
    return resp(data=AlertConfigOut(
        dingtalk_webhook=_get(db, "dingtalk_webhook"),
        wechat_webhook=_get(db, "wechat_webhook"),
    ).model_dump())


@router.get("/system/action-logs")
def action_logs(
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    user: User = Depends(require_admin),
):
    q = db.query(OperationLog)
    total = q.count()
    items = (
        q.order_by(OperationLog.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(min(page_size, 100))
        .all()
    )
    return resp(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [OperationLogOut.model_validate(i).model_dump() for i in items],
    })


@router.put("/system/alert")
def save_alert(body: AlertConfigIn, request: Request, db: Session = Depends(get_db),
               user: User = Depends(require_admin)):
    _set(db, "dingtalk_webhook", body.dingtalk_webhook)
    _set(db, "wechat_webhook", body.wechat_webhook)
    record_action(db, user, "系统设置", "保存告警配置", request=request)
    db.commit()
    return resp(msg="告警配置已保存")


@router.get("/license/info")
def license_info(user: User = Depends(get_current_user),
                 db: Session = Depends(get_db)):
    max_ds, max_tasks = quota_max(user)
    ds, tasks = used_counts(db, user.id)
    lic = db.query(License).filter(License.status == "active").first()
    return resp(data=LicenseInfo(
        plan=user.plan,
        max_datasources=max_ds,
        max_tasks=max_tasks,
        datasources_used=ds,
        tasks_used=tasks,
        activated=lic is not None,
        holder=lic.holder if lic else "",
        expires_at=lic.expires_at.strftime("%Y-%m-%d") if lic and lic.expires_at else None,
    ).model_dump())


@router.post("/license/activate")
def activate(body: LicenseActivate, request: Request, db: Session = Depends(get_db),
             user: User = Depends(require_admin)):
    # 私有化授权码校验：简单规则（生产可替换为服务端校验）
    code = (body.license_code or "").strip()
    if not code:
        return resp(code=400, msg="授权码不能为空", status_code=400)
    lic = db.query(License).filter(License.license_code == code).first()
    if lic and lic.status == "active":
        user.plan = lic.plan
        record_action(db, user, "系统设置", "激活授权", f"套餐: {user.plan}", request)
        db.commit()
        return resp(msg="授权已生效，已解锁付费权限", data={"plan": user.plan})
    # 未预置则按规则生成并激活（演示用：以 ETL- 开头即视为有效）
    if code.startswith("ETL-"):
        lic = License(
            license_code=code, plan="paid", status="active",
            holder=user.username, activated_at=datetime.now(),
        )
        db.add(lic)
        user.plan = "paid"
        record_action(db, user, "系统设置", "激活授权", f"授权码: {code}", request)
        db.commit()
        return resp(msg="授权码激活成功，已解锁付费权限", data={"plan": user.plan})
    return resp(code=400, msg="授权码无效", status_code=400)


@router.get("/stats")
def stats(user: User = Depends(get_current_user),
          db: Session = Depends(get_db)):
    ds = db.query(Datasource).filter(Datasource.user_id == user.id).count()
    tasks = db.query(SyncTask).filter(SyncTask.user_id == user.id).count()
    tasks_enabled = db.query(SyncTask).filter(
        SyncTask.user_id == user.id, SyncTask.enabled.is_(True)).count()
    from app.models import TaskLog
    logs_total = db.query(TaskLog).filter(TaskLog.user_id == user.id).count()
    logs_failed = db.query(TaskLog).filter(
        TaskLog.user_id == user.id, TaskLog.status == "failed").count()
    logs_success = db.query(TaskLog).filter(
        TaskLog.user_id == user.id, TaskLog.status == "success").count()
    return resp(data=StatsOut(
        datasources=ds, tasks=tasks, tasks_enabled=tasks_enabled,
        logs_total=logs_total, logs_failed=logs_failed,
        logs_success=logs_success,
    ).model_dump())
