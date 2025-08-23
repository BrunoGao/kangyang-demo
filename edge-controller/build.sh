#!/bin/bash

# 边缘控制器优化构建脚本

set -e

echo "🚀 开始构建边缘控制器Docker镜像..."
echo "📦 使用阿里云加速源优化构建速度"

# 记录开始时间
start_time=$(date +%s)

# 构建镜像
docker build -t kangyang-edge-controller .

# 计算构建时间
end_time=$(date +%s)
build_time=$((end_time - start_time))

echo ""
echo "✅ 构建完成！"
echo "⏱️  构建用时: ${build_time}秒"
echo "📊 镜像信息:"
docker images kangyang-edge-controller:latest

echo ""
echo "🔧 使用方式:"
echo "  测试运行: docker run --rm -p 8084:8084 kangyang-edge-controller"
echo "  查看日志: docker logs [容器ID]"