# 康养AI检测系统 - 边缘控制器 Dockerfile (完整功能优化版)
FROM python:3.11-slim

# 设置构建环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src:/app

WORKDIR /app

# 使用阿里云源加速并安装系统依赖
RUN echo "deb http://mirrors.aliyun.com/debian/ trixie main" > /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian/ trixie-updates main" >> /etc/apt/sources.list && \
    echo "deb http://mirrors.aliyun.com/debian-security/ trixie-security main" >> /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV和AI检测必需的系统库
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender1 \
    libgomp1 \
    libgtk-3-0 \
    libgl1-mesa-dri \
    libgthread-2.0-0 \
    # 网络和监控工具
    curl \
    # 清理缓存减小镜像大小
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 复制requirements文件（优先复制以利用Docker层缓存）
COPY requirements.txt .

# 使用阿里云pip源加速安装Python依赖
RUN pip config set global.index-url https://mirrors.aliyun.com/pypi/simple/ && \
    pip config set install.trusted-host mirrors.aliyun.com && \
    # 使用缓存挂载避免重复下载
    --mount=type=cache,target=/root/.cache/pip \
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