# 康养AI检测系统 - 边缘控制器 Dockerfile (轻量快速版)
FROM python:3.11-slim

# 设置代理环境变量
ARG HTTP_PROXY
ARG HTTPS_PROXY
ENV http_proxy=${HTTP_PROXY}
ENV https_proxy=${HTTPS_PROXY}

# 设置构建环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app

WORKDIR /app

# 跳过系统依赖，直接使用Python环境

# 复制精简版requirements文件
COPY requirements-minimal.txt requirements.txt

# 使用默认pip源安装Python依赖 
RUN --mount=type=cache,target=/root/.cache/pip \
    env -u http_proxy -u https_proxy -u HTTP_PROXY -u HTTPS_PROXY \
    pip install --no-cache-dir -r requirements.txt

# 复制源代码（最后复制以最大化缓存利用）
COPY src/ ./src/
COPY config/ ./config/

# 创建运行时必需目录
RUN mkdir -p /data/edge-controller/snapshots /data/edge-controller/videos /app/logs

# 健康检查
HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD curl -f http://localhost:8084/api/health || exit 1

# 暴露端口
EXPOSE 8084 9090

# 切换到源码目录并启动
WORKDIR /app/src
CMD ["python", "-u", "main.py"]