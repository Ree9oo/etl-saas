"""统一响应封装：code / msg / data（自动序列化 datetime、Pydantic 模型等）"""
from fastapi.encoders import jsonable_encoder
from fastapi.responses import JSONResponse


def resp(code: int = 0, msg: str = "ok", data=None, status_code: int = 200):
    return JSONResponse(
        status_code=status_code,
        content={"code": code, "msg": msg, "data": jsonable_encoder(data)},
    )
