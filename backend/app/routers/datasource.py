"""数据源管理模块：CRUD、连接测试、表列表、额度校验"""
from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User, Datasource
from app.schemas import (
    DatasourceCreate, DatasourceUpdate, DatasourceOut, DatasourceTest,
)
from app.security import encrypt_secret, decrypt_secret
from app.services.db_engine import test_connection, list_tables, friendly_connection_error
from app.services.audit import record_action
from app.services.quota import check_create
from app.utils.response import resp

router = APIRouter(prefix="/api/datasources", tags=["数据源"])
SUPPORTED = ["mysql", "sqlserver", "postgresql", "oracle", "dm", "sqlite"]


@router.get("")
def list_datasources(db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    items = (
        db.query(Datasource)
        .filter(Datasource.user_id == user.id)
        .order_by(Datasource.created_at.desc())
        .all()
    )
    return resp(data=[DatasourceOut.model_validate(i).model_dump() for i in items])


@router.post("")
def create_datasource(body: DatasourceCreate, request: Request,
                      db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    if body.db_type not in SUPPORTED:
        return resp(code=400, msg=f"不支持的数据库类型，支持: {SUPPORTED}",
                     status_code=400)
    ok, msg = check_create(db, user, "datasource")
    if not ok:
        return resp(code=403, msg=msg, status_code=403)
    ds = Datasource(
        user_id=user.id,
        name=body.name,
        db_type=body.db_type,
        host=body.host,
        port=body.port,
        username=body.username,
        password=encrypt_secret(body.password),
        database=body.database,
        charset=body.charset,
        extra=body.extra,
    )
    db.add(ds)
    db.commit()
    db.refresh(ds)
    record_action(db, user, "数据源", "创建数据源", f"名称: {ds.name}", request)
    db.commit()
    return resp(data=DatasourceOut.model_validate(ds).model_dump(),
                msg="数据源创建成功")


@router.get("/{ds_id}")
def get_datasource(ds_id: int, db: Session = Depends(get_db),
                   user: User = Depends(get_current_user)):
    ds = db.query(Datasource).filter(
        Datasource.id == ds_id, Datasource.user_id == user.id).first()
    if not ds:
        return resp(code=404, msg="数据源不存在", status_code=404)
    return resp(data=DatasourceOut.model_validate(ds).model_dump())


@router.put("/{ds_id}")
def update_datasource(ds_id: int, body: DatasourceUpdate, request: Request,
                      db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    ds = db.query(Datasource).filter(
        Datasource.id == ds_id, Datasource.user_id == user.id).first()
    if not ds:
        return resp(code=404, msg="数据源不存在", status_code=404)
    data = body.model_dump(exclude_unset=True)
    if data.get("db_type") and data["db_type"] not in SUPPORTED:
        return resp(code=400, msg=f"不支持的数据库类型：{data['db_type']}", status_code=400)
    if "password" in data and data["password"] == "":
        data.pop("password")  # 空密码表示不修改
    for k, v in data.items():
        if k == "password":
            setattr(ds, k, encrypt_secret(v))
        else:
            setattr(ds, k, v)
    db.commit()
    db.refresh(ds)
    record_action(db, user, "数据源", "更新数据源", f"名称: {ds.name}", request)
    db.commit()
    return resp(data=DatasourceOut.model_validate(ds).model_dump(),
                msg="更新成功")


@router.delete("/{ds_id}")
def delete_datasource(ds_id: int, request: Request, db: Session = Depends(get_db),
                      user: User = Depends(get_current_user)):
    ds = db.query(Datasource).filter(
        Datasource.id == ds_id, Datasource.user_id == user.id).first()
    if not ds:
        return resp(code=404, msg="数据源不存在", status_code=404)
    # 检查是否被任务引用
    from app.models import SyncTask
    ref = db.query(SyncTask).filter(
        (SyncTask.source_id == ds_id) | (SyncTask.target_id == ds_id)).first()
    if ref:
        return resp(code=400, msg="该数据源已被同步任务引用，无法删除",
                     status_code=400)
    db.delete(ds)
    record_action(db, user, "数据源", "删除数据源", f"名称: {ds.name}", request)
    db.commit()
    return resp(msg="删除成功")


@router.post("/test")
def test_ds(body: DatasourceTest):
    if body.db_type not in SUPPORTED:
        return resp(code=400, msg=f"不支持的数据库类型，支持: {SUPPORTED}",
                     status_code=400)
    d = body.model_dump()
    d["password"] = encrypt_secret(body.password)  # 仅用于构造引擎
    # make_engine 接收对象属性，这里用简单对象包装
    class _D:
        pass
    obj = _D()
    for k, v in d.items():
        setattr(obj, k, v)
    obj.password = body.password  # 用明文测试
    result = test_connection(obj)
    if result["success"]:
        return resp(data=result, msg=result["message"])
    return resp(code=400, msg=result["message"], status_code=400, data=result)


@router.post("/{ds_id}/test")
def test_saved_ds(ds_id: int, db: Session = Depends(get_db),
                  user: User = Depends(get_current_user)):
    ds = db.query(Datasource).filter(
        Datasource.id == ds_id, Datasource.user_id == user.id).first()
    if not ds:
        return resp(code=404, msg="数据源不存在", status_code=404)
    obj = Datasource(
        user_id=ds.user_id, name=ds.name, db_type=ds.db_type,
        host=ds.host, port=ds.port, username=ds.username,
        password=decrypt_secret(ds.password), database=ds.database,
        charset=ds.charset, extra=ds.extra,
    )
    result = test_connection(obj)
    if result["success"]:
        return resp(data=result, msg=result["message"])
    return resp(code=400, msg=result["message"], status_code=400, data=result)


@router.get("/{ds_id}/tables")
def tables(ds_id: int, db: Session = Depends(get_db),
           user: User = Depends(get_current_user)):
    ds = db.query(Datasource).filter(
        Datasource.id == ds_id, Datasource.user_id == user.id).first()
    if not ds:
        return resp(code=404, msg="数据源不存在", status_code=404)
    try:
        obj = Datasource(
            user_id=ds.user_id, name=ds.name, db_type=ds.db_type,
            host=ds.host, port=ds.port, username=ds.username,
            password=decrypt_secret(ds.password), database=ds.database,
            charset=ds.charset, extra=ds.extra,
        )
        names = list_tables(obj)
        return resp(data=names)
    except Exception as e:
        return resp(
            code=400,
            msg=f"获取{ds.db_type}表列表失败：{friendly_connection_error(ds.db_type, e)}",
            status_code=400,
        )
