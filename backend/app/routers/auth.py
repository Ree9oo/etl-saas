"""用户权限模块：登录、注册、当前用户"""
from fastapi import APIRouter, Depends, Header, Request
from sqlalchemy.orm import Session

from app.database import get_db
from app.deps import get_current_user
from app.models import User
from app.schemas import (
    LoginRequest, LoginResponse, RegisterRequest, UserOut,
)
from app.security import (
    hash_password, verify_password, create_access_token, ensure_admin,
)
from app.services.audit import record_action
from app.utils.response import resp

router = APIRouter(prefix="/api/auth", tags=["鉴权"])


@router.post("/login")
def login(body: LoginRequest, request: Request, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.username == body.username).first()
    if not user or not verify_password(body.password, user.password_hash):
        return resp(code=401, msg="用户名或密码错误", status_code=401)
    token = create_access_token(user.id)
    record_action(db, user, "鉴权", "登录系统", request=request)
    db.commit()
    return resp(data=LoginResponse(
        token=token, username=user.username, role=user.role, plan=user.plan
    ).model_dump())


@router.post("/register")
def register(body: RegisterRequest, request: Request, db: Session = Depends(get_db)):
    exists = db.query(User).filter(User.username == body.username).first()
    if exists:
        return resp(code=400, msg="用户名已存在", status_code=400)
    user = User(
        username=body.username,
        password_hash=hash_password(body.password),
        role="user",
        plan="free",
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    record_action(db, user, "鉴权", "注册账号", request=request)
    db.commit()
    token = create_access_token(user.id)
    return resp(data=LoginResponse(
        token=token, username=user.username, role=user.role, plan=user.plan
    ).model_dump())


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return resp(data=UserOut.model_validate(user).model_dump())
