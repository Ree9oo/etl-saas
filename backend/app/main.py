"""FastAPI 应用入口：路由注册、CORS、生命周期管理"""
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.security import ensure_admin
from app.services.scheduler import init_scheduler, shutdown_scheduler
from app.routers import auth, datasource, task, log, system
from app.utils.response import resp


@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动：建表 + 默认管理员 + 调度器
    init_db()
    ensure_admin()
    init_scheduler()
    yield
    shutdown_scheduler()


app = FastAPI(
    title=settings.APP_NAME,
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(datasource.router)
app.include_router(task.router)
app.include_router(log.router)
app.include_router(system.router)


@app.get("/api/health")
def health():
    return resp(data={"status": "ok", "app": settings.APP_NAME})


if __name__ == "__main__":
    import uvicorn

    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=False)
