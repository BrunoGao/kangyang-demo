# 康养AI检测系统 - NVIDIA DeepStream优化版 Dockerfile
FROM nvcr.io/nvidia/deepstream:6.4-triton-multiarch

# 设置环境变量
ENV DEBIAN_FRONTEND=noninteractive \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    CUDA_CACHE_MAXSIZE=2147483648 \
    GST_PLUGIN_PATH=/opt/nvidia/deepstream/deepstream/lib/gst-plugins \
    LD_LIBRARY_PATH=/opt/nvidia/deepstream/deepstream/lib \
    PATH=/opt/nvidia/deepstream/deepstream/bin:$PATH

WORKDIR /opt/nvidia/deepstream/deepstream

# 使用清华源加速并安装必要的系统依赖
RUN sed -i 's@//.*archive.ubuntu.com@//mirrors.tuna.tsinghua.edu.cn@g' /etc/apt/sources.list && \
    apt-get update && apt-get install -y --no-install-recommends \
    # Python环境和开发工具
    python3.11 \
    python3-pip \
    python3.11-dev \
    # 网络和监控工具
    curl \
    wget \
    vim \
    htop \
    # 媒体处理库
    libgstreamer1.0-dev \
    libgstreamer-plugins-base1.0-dev \
    libgstreamer-plugins-bad1.0-dev \
    gstreamer1.0-plugins-base \
    gstreamer1.0-plugins-good \
    gstreamer1.0-plugins-bad \
    gstreamer1.0-plugins-ugly \
    gstreamer1.0-libav \
    # 清理缓存
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/* \
    && rm -rf /tmp/* \
    && rm -rf /var/tmp/*

# 升级pip并安装Python依赖
COPY requirements.txt /tmp/
RUN python3 -m pip install --upgrade pip && \
    pip3 config set global.index-url https://pypi.tuna.tsinghua.edu.cn/simple/ && \
    pip3 install --no-cache-dir -r /tmp/requirements.txt && \
    rm /tmp/requirements.txt

# 创建项目目录结构
RUN mkdir -p /opt/kangyang/{configs,models,logs,data,payloads,tracker/NvDCF,lib,labels}

# 复制DeepStream配置文件
COPY configs/deepstream_app.txt /opt/kangyang/configs/
COPY configs/nvdcf_tracker.txt /opt/kangyang/configs/
COPY configs/kafka_schema.json /opt/kangyang/configs/

# 复制模型文件占位符（生产环境需替换为真实模型）
RUN touch /opt/kangyang/models/fall_fast_int8.engine && \
    touch /opt/kangyang/models/fall_refine_fp16.engine && \
    touch /opt/kangyang/models/smoke_fire_int8.engine

# 复制DeepStream应用配置
COPY scripts/deepstream_kangyang_app.py /opt/kangyang/
COPY scripts/model_optimization.py /opt/kangyang/

# 设置权限和工作目录
RUN chmod +x /opt/kangyang/deepstream_kangyang_app.py
WORKDIR /opt/kangyang

# 健康检查（检查DeepStream应用是否运行）
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD pgrep -f deepstream_kangyang_app || exit 1

# 暴露端口
EXPOSE 8554 9400 5000

# 启动DeepStream应用
CMD ["python3", "deepstream_kangyang_app.py"]