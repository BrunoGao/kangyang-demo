#!/bin/bash

# 边缘控制器Docker启动脚本 - 连接本地MySQL和Redis

set -e

echo "🚀 启动边缘控制器Docker服务..."

# 检查本地服务状态
echo "🔍 检查本地服务状态..."
if ! lsof -i :3306 > /dev/null 2>&1; then
    echo "❌ MySQL服务未启动，请先启动MySQL服务"
    exit 1
fi

if ! lsof -i :6379 > /dev/null 2>&1; then
    echo "❌ Redis服务未启动，请先启动Redis服务"
    exit 1
fi

echo "✅ 本地MySQL和Redis服务正在运行"

# 获取宿主机IP (Docker内部访问宿主机)
HOST_IP="host.docker.internal"

echo "🐳 启动边缘控制器Docker容器..."

# 停止已存在的容器
docker rm -f kangyang-edge-controller 2>/dev/null || true

# 启动容器，映射端口并连接到宿主机网络
docker run -d \
    --name kangyang-edge-controller \
    --add-host=host.docker.internal:host-gateway \
    -p 8084:8084 \
    -p 9090:9090 \
    -e CONTROLLER_ID=edge_controller_1 \
    -e CONTROLLER_NAME="边缘控制器#1" \
    -e MANAGEMENT_PLATFORM_URL="http://localhost:8080/api" \
    -e EDGE_API_KEY="default_key" \
    -v $(pwd)/config:/app/config \
    -v $(pwd)/logs:/app/logs \
    -v $(pwd)/src:/app/src \
    --restart unless-stopped \
    deployment-edge-controller-1 \
    sh -c "pip install aiofiles aiosqlite psutil && cd /app/src && python main.py"

echo ""
echo "✅ 边缘控制器启动成功！"
echo "📊 容器状态:"
docker ps --filter name=kangyang-edge-controller

echo ""
echo "🔗 访问地址:"
echo "  API接口: http://localhost:8084"
echo "  健康检查: http://localhost:8084/api/health"
echo "  API文档: http://localhost:8084/docs"

echo ""
echo "📋 常用命令:"
echo "  查看日志: docker logs -f kangyang-edge-controller"
echo "  停止服务: docker stop kangyang-edge-controller"
echo "  重启服务: docker restart kangyang-edge-controller"