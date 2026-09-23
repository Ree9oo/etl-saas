"""执行日志监控模块：日志列表查询"""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, TaskLog
from app.schemas import LogOut
from app.utils.response import resp

router = APIRouter(prefix="/api/logs", tags=["日志"])


@router.get("")
def list_logs(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
    task_id: int = Query(None),
    status: str = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    q = db.query(TaskLog).filter(TaskLog.user_id == user.id)
    if task_id:
        q = q.filter(TaskLog.task_id == task_id)
    if status:
        q = q.filter(TaskLog.status == status)
    total = q.count()
    items = (
        q.order_by(TaskLog.started_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
        .all()
    )
    return resp(data={
        "total": total,
        "page": page,
        "page_size": page_size,
        "list": [LogOut.model_validate(i).model_dump() for i in items],
    })
