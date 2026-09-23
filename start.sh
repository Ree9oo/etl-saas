#!/bin/bash
# 轻量多源数据同步 ETL SaaS 系统 - 本地一键启动（默认 SQLite，零外部依赖）
set -e

echo "==> 安装后端依赖并启动 API (http://localhost:8000)"
cd backend
pip install -r requirements.txt -q
uvicorn app.main:app --host 0.0.0.0 --port 8000 > /tmp/etl_backend.log 2>&1 &
BACKEND_PID=$!
echo "   后端 PID: $BACKEND_PID"

echo "==> 安装前端依赖并启动 (http://localhost:5173)"
cd ../frontend
npm install -q
npm run dev > /tmp/etl_frontend.log 2>&1 &
FRONTEND_PID=$!
echo "   前端 PID: $FRONTEND_PID"

echo ""
echo "访问地址: http://localhost:5173   (前端开发服务器，已代理 /api -> :8000)"
echo "默认账号: admin / admin123"
echo "停止: kill $BACKEND_PID $FRONTEND_PID"
wait
