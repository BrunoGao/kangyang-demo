#!/bin/bash

# 简化的边缘控制器启动脚本

echo "🚀 简化启动边缘控制器..."

# 停止已存在的容器
docker rm -f kangyang-edge-simple 2>/dev/null || true

# 使用Python base镜像直接运行，避免构建时间
docker run -d \
    --name kangyang-edge-simple \
    --network host \
    -v $(pwd):/app \
    -w /app/src \
    -e PYTHONPATH=/app/src:/app \
    -e CONTROLLER_ID=edge_controller_1 \
    -e CONTROLLER_NAME="边缘控制器#1" \
    python:3.11-slim \
    sh -c "pip install fastapi uvicorn pydantic python-multipart aiohttp pyyaml structlog && python main.py"

echo "✅ 简化版边缘控制器启动中..."
echo "📊 容器状态:"
docker ps --filter name=kangyang-edge-simple

echo ""
echo "🔗 访问地址:"
echo "  API接口: http://localhost:8084"
echo "  健康检查: http://localhost:8084/api/health"

echo ""
echo "📋 查看日志: docker logs -f kangyang-edge-simple"