"""系统操作日志写入工具。"""
from typing import Optional

from fastapi import Request
from sqlalchemy.orm import Session

from app.models import OperationLog, User


def record_action(
    db: Session, user: User, module: str, action: str, detail: str = "",
    request: Optional[Request] = None,
) -> None:
    ip_address = ""
    if request is not None:
        forwarded_for = request.headers.get("x-forwarded-for", "")
        ip_address = forwarded_for.split(",", 1)[0].strip()
        if not ip_address:
            ip_address = request.headers.get("x-real-ip", "").strip()
        if not ip_address and request.client:
            ip_address = request.client.host
    db.add(OperationLog(
        user_id=user.id,
        username=user.username,
        module=module,
        action=action,
        detail=detail,
        ip_address=ip_address,
    ))