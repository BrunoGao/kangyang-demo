#!/bin/bash

echo "🛑 停止康养跌倒检测系统演示"

# 停止前端服务
if [ -f "frontend/admin/admin.pid" ]; then
    echo "停止管理界面..."
    kill $(cat frontend/admin/admin.pid) 2>/dev/null
    rm frontend/admin/admin.pid
fi

if [ -f "frontend/monitor/monitor.pid" ]; then
    echo "停止监控大屏..."
    kill $(cat frontend/monitor/monitor.pid) 2>/dev/null
    rm frontend/monitor/monitor.pid
fi

# 停止后端服务
if [ -f "backend/backend.pid" ]; then
    echo "停止后端服务..."
    kill $(cat backend/backend.pid) 2>/dev/null
    rm backend/backend.pid
fi

# 停止AI检测服务
if [ -f "ai-detection/ai-detection.pid" ]; then
    echo "停止AI检测服务..."
    kill $(cat ai-detection/ai-detection.pid) 2>/dev/null
    rm ai-detection/ai-detection.pid
fi

# 停止Docker服务
echo "停止Docker服务..."
docker-compose down

# 清理残留进程
echo "清理残留进程..."
pkill -f "python app.py"
pkill -f "java -jar target/fall-detection-backend"
pkill -f "npm run dev"

echo "✅ 所有服务已停止"