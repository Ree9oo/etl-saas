"""同步任务模块：CRUD、手动执行、启停、额度校验"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, SyncTask
from app.schemas import TaskCreate, TaskUpdate, TaskOut
from app.services.quota import check_create
from app.services.scheduler import add_task_job, remove_task_job
from app.services.sync import run_task_once
from app.services.audit import record_action
from app.utils.response import resp

router = APIRouter(prefix="/api/tasks", tags=["同步任务"])


@router.get("")
def list_tasks(db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    items = (
        db.query(SyncTask)
        .filter(SyncTask.user_id == user.id)
        .order_by(SyncTask.created_at.desc())
        .all()
    )
    return resp(data=[TaskOut.model_validate(i).model_dump() for i in items])


@router.post("")
def create_task(body: TaskCreate, request: Request, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    ok, msg = check_create(db, user, "task")
    if not ok:
        return resp(code=403, msg=msg, status_code=403)
    data = body.model_dump()
    data["target_table"] = data["target_table"] or data["source_table"]
    task = SyncTask(user_id=user.id, **data)
    db.add(task)
    db.commit()
    db.refresh(task)
    if task.enabled and task.cron.strip():
        add_task_job(task)
    record_action(db, user, "同步任务", "创建任务", f"名称: {task.name}", request)
    db.commit()
    return resp(data=TaskOut.model_validate(task).model_dump(),
                msg="任务创建成功")


@router.get("/{task_id}")
def get_task(task_id: int, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    task = db.query(SyncTask).filter(
        SyncTask.id == task_id, SyncTask.user_id == user.id).first()
    if not task:
        return resp(code=404, msg="任务不存在", status_code=404)
    return resp(data=TaskOut.model_validate(task).model_dump())


@router.put("/{task_id}")
def update_task(task_id: int, body: TaskUpdate, request: Request,
                db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    task = db.query(SyncTask).filter(
        SyncTask.id == task_id, SyncTask.user_id == user.id).first()
    if not task:
        return resp(code=404, msg="任务不存在", status_code=404)
    data = body.model_dump(exclude_unset=True)
    if data.get("target_table") == "":
        data["target_table"] = data.get("source_table", task.source_table)
    for k, v in data.items():
        setattr(task, k, v)
    db.commit()
    db.refresh(task)
    # 重新注册调度
    remove_task_job(task_id)
    if task.enabled and task.cron.strip():
        add_task_job(task)
    record_action(db, user, "同步任务", "更新任务", f"名称: {task.name}", request)
    db.commit()
    return resp(data=TaskOut.model_validate(task).model_dump(), msg="更新成功")


@router.delete("/{task_id}")
def delete_task(task_id: int, request: Request, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    task = db.query(SyncTask).filter(
        SyncTask.id == task_id, SyncTask.user_id == user.id).first()
    if not task:
        return resp(code=404, msg="任务不存在", status_code=404)
    remove_task_job(task_id)
    record_action(db, user, "同步任务", "删除任务", f"名称: {task.name}", request)
    db.delete(task)
    db.commit()
    return resp(msg="删除成功")


@router.post("/{task_id}/run")
def run_task(task_id: int, request: Request, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    task = db.query(SyncTask).filter(
        SyncTask.id == task_id, SyncTask.user_id == user.id).first()
    if not task:
        return resp(code=404, msg="任务不存在", status_code=404)
    if task.status == "running":
        return resp(code=409, msg="任务正在执行中", status_code=409)
    result = run_task_once(db, task)
    record_action(db, user, "同步任务", "手动执行任务", f"名称: {task.name}", request)
    db.commit()
    if result["status"] == "success":
        return resp(data=result, msg=f"同步成功，共 {result['rows']} 行")
    return resp(code=400, msg=f"同步失败: {result['error'][:200]}",
                status_code=400, data=result)


@router.post("/{task_id}/toggle")
def toggle_task(task_id: int, request: Request, db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    task = db.query(SyncTask).filter(
        SyncTask.id == task_id, SyncTask.user_id == user.id).first()
    if not task:
        return resp(code=404, msg="任务不存在", status_code=404)
    task.enabled = not task.enabled
    db.commit()
    remove_task_job(task_id)
    if task.enabled and task.cron.strip():
        add_task_job(task)
    record_action(db, user, "同步任务", "切换任务状态", f"名称: {task.name}", request)
    db.commit()
    return resp(data={"enabled": task.enabled},
                msg="已" + ("启用" if task.enabled else "禁用"))
