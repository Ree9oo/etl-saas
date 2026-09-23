"""安全工具：密码哈希、JWT、数据源密码加解密"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import base64

from jose import JWTError, jwt
import bcrypt
from cryptography.fernet import Fernet
from sqlalchemy.orm import Session

from app.config import settings
from app.database import SessionLocal
from app import models

# 数据源密码加解密
_fernet: Optional[Fernet] = None


def _get_fernet() -> Fernet:
    global _fernet
    if _fernet is None:
        key = settings.FERNET_KEY
        if not key:
            # 由 SECRET_KEY 派生一个稳定密钥
            import hashlib
            digest = hashlib.sha256(settings.SECRET_KEY.encode()).digest()
            key = base64.urlsafe_b64encode(digest)
        _fernet = Fernet(key)
    return _fernet


# ---------- 用户密码 ----------
def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    try:
        return bcrypt.checkpw(plain.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False


# ---------- JWT ----------
def create_access_token(subject: str | int) -> str:
    expire = datetime.now(timezone.utc) + settings.JWT_TOKEN_TTL
    payload = {"sub": str(subject), "exp": expire}
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> Optional[int]:
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        sub = payload.get("sub")
        return int(sub) if sub is not None else None
    except JWTError:
        return None


# ---------- 数据源密码加解密 ----------
def encrypt_secret(plain: str) -> str:
    if not plain:
        return ""
    return _get_fernet().encrypt(plain.encode()).decode()


def decrypt_secret(token: str) -> str:
    if not token:
        return ""
    try:
        return _get_fernet().decrypt(token.encode()).decode()
    except Exception:
        return token  # 兼容未加密的遗留数据


# ---------- 默认管理员初始化 ----------
def ensure_admin():
    db: Session = SessionLocal()
    try:
        existing = (
            db.query(models.User)
            .filter(models.User.username == settings.INIT_ADMIN_USERNAME)
            .first()
        )
        if existing is None:
            admin = models.User(
                username=settings.INIT_ADMIN_USERNAME,
                password_hash=hash_password(settings.INIT_ADMIN_PASSWORD),
                role="admin",
                plan="paid",  # 管理员默认付费权限，无额度限制
            )
            db.add(admin)
            db.commit()
            print(
                f"[init] 已创建默认管理员账号: "
                f"{settings.INIT_ADMIN_USERNAME} / {settings.INIT_ADMIN_PASSWORD}"
            )
    finally:
        db.close()
