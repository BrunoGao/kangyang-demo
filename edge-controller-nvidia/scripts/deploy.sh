#!/bin/bash
# 康养AI检测系统 - NVIDIA L4优化版一键部署脚本
# 自动检查环境、构建镜像、启动服务

set -e

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 日志函数
log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_step() {
    echo -e "${BLUE}[STEP]${NC} $1"
}

# 脚本目录
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"
DOCKER_DIR="$PROJECT_DIR/docker"

# 配置文件
ENV_FILE="$PROJECT_DIR/.env"
COMPOSE_FILE="$DOCKER_DIR/docker-compose.nvidia.yml"

# 创建环境变量文件
create_env_file() {
    log_step "创建环境配置文件..."
    
    cat > "$ENV_FILE" << EOF
# 康养AI检测系统 - NVIDIA版本配置
COMPOSE_PROJECT_NAME=kangyang-nvidia
COMPOSE_FILE=$COMPOSE_FILE

# GPU配置
NVIDIA_VISIBLE_DEVICES=all
CUDA_CACHE_MAXSIZE=2147483648

# 服务端口配置
DEEPSTREAM_PORT=8554
DCGM_EXPORTER_PORT=9400
KAFKA_PORT=9092
REDIS_PORT=6379
PROMETHEUS_PORT=9090
GRAFANA_PORT=3000

# Kafka配置
KAFKA_TOPIC_EVENTS=edge-events
KAFKA_TOPIC_ALERTS=edge-alerts
KAFKA_RETENTION_HOURS=24

# 时区配置
TZ=Asia/Shanghai

# 日志配置
LOG_LEVEL=INFO
LOG_MAX_SIZE=100m
LOG_MAX_FILES=10
EOF
    
    log_info "环境配置文件创建完成: $ENV_FILE"
}

# 检查前置条件
check_prerequisites() {
    log_step "检查系统前置条件..."
    
    # 检查是否为Linux系统
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        log_error "此脚本仅支持Linux系统"
        exit 1
    fi
    
    # 检查是否有sudo权限
    if ! sudo -n true 2>/dev/null; then
        log_error "需要sudo权限来安装依赖"
        exit 1
    fi
    
    # 检查NVIDIA驱动
    if ! command -v nvidia-smi &> /dev/null; then
        log_error "未检测到NVIDIA驱动，请先安装NVIDIA驱动"
        exit 1
    fi
    
    # 检查GPU可用性
    log_info "检测到的GPU信息:"
    nvidia-smi --query-gpu=name,driver_version,memory.total --format=csv,noheader
    
    # 检查Docker
    if ! command -v docker &> /dev/null; then
        log_warn "Docker未安装，正在安装..."
        install_docker
    else
        log_info "Docker已安装: $(docker --version)"
    fi
    
    # 检查Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_warn "Docker Compose未安装，正在安装..."
        install_docker_compose
    else
        log_info "Docker Compose已安装: $(docker-compose --version)"
    fi
    
    # 检查nvidia-container-toolkit
    if ! docker info 2>/dev/null | grep -q "nvidia"; then
        log_warn "NVIDIA Container Toolkit未安装，正在安装..."
        install_nvidia_container_toolkit
    else
        log_info "NVIDIA Container Toolkit已安装"
    fi
    
    # 验证GPU在Docker中可用
    log_info "验证GPU在Docker中的可用性..."
    if docker run --rm --gpus all nvidia/cuda:11.8-runtime-ubuntu20.04 nvidia-smi > /dev/null 2>&1; then
        log_info "GPU在Docker中可正常使用"
    else
        log_error "GPU在Docker中不可用，请检查nvidia-container-toolkit配置"
        exit 1
    fi
}

# 安装Docker
install_docker() {
    log_info "开始安装Docker..."
    
    # 更新包索引
    sudo apt-get update
    
    # 安装必要依赖
    sudo apt-get install -y apt-transport-https ca-certificates curl gnupg lsb-release
    
    # 添加Docker官方GPG密钥
    curl -fsSL https://download.docker.com/linux/ubuntu/gpg | sudo gpg --dearmor -o /usr/share/keyrings/docker-archive-keyring.gpg
    
    # 添加Docker仓库
    echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/docker-archive-keyring.gpg] https://download.docker.com/linux/ubuntu $(lsb_release -cs) stable" | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    
    # 安装Docker Engine
    sudo apt-get update
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io
    
    # 启动Docker服务
    sudo systemctl start docker
    sudo systemctl enable docker
    
    # 添加当前用户到docker组
    sudo usermod -aG docker $USER
    
    log_info "Docker安装完成"
}

# 安装Docker Compose
install_docker_compose() {
    log_info "开始安装Docker Compose..."
    
    # 下载最新版本的Docker Compose
    COMPOSE_VERSION=$(curl -s https://api.github.com/repos/docker/compose/releases/latest | grep 'tag_name' | cut -d\" -f4)
    sudo curl -L "https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
    
    # 设置执行权限
    sudo chmod +x /usr/local/bin/docker-compose
    
    log_info "Docker Compose安装完成: $COMPOSE_VERSION"
}

# 安装NVIDIA Container Toolkit
install_nvidia_container_toolkit() {
    log_info "开始安装NVIDIA Container Toolkit..."
    
    # 添加NVIDIA仓库
    distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
    curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
    curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | sudo tee /etc/apt/sources.list.d/libnvidia-container.list
    
    # 安装nvidia-container-toolkit
    sudo apt-get update
    sudo apt-get install -y nvidia-container-toolkit
    
    # 重启Docker服务
    sudo systemctl restart docker
    
    log_info "NVIDIA Container Toolkit安装完成"
}

# 准备模型文件
prepare_models() {
    log_step "准备模型文件..."
    
    MODELS_DIR="$PROJECT_DIR/models"
    mkdir -p "$MODELS_DIR"
    
    # 检查是否存在模型文件
    REQUIRED_MODELS=(
        "fall_fast_int8.engine"
        "fall_refine_fp16.engine" 
        "smoke_fire_int8.engine"
    )
    
    MISSING_MODELS=()
    for model in "${REQUIRED_MODELS[@]}"; do
        if [[ ! -f "$MODELS_DIR/$model" ]]; then
            MISSING_MODELS+=("$model")
        fi
    done
    
    if [[ ${#MISSING_MODELS[@]} -gt 0 ]]; then
        log_warn "以下模型文件缺失: ${MISSING_MODELS[*]}"
        log_info "将创建占位符模型文件用于测试..."
        
        for model in "${MISSING_MODELS[@]}"; do
            touch "$MODELS_DIR/$model"
            log_info "创建占位符: $model"
        done
        
        log_warn "请在生产环境中替换为真实的TensorRT模型文件"
    else
        log_info "所有模型文件就绪"
    fi
}

# 准备配置文件
prepare_configs() {
    log_step "准备配置文件..."
    
    CONFIGS_DIR="$PROJECT_DIR/configs"
    
    # 检查DeepStream配置文件
    if [[ ! -f "$CONFIGS_DIR/deepstream_app.txt" ]]; then
        log_error "DeepStream配置文件不存在: $CONFIGS_DIR/deepstream_app.txt"
        exit 1
    fi
    
    # 检查并更新RTSP地址
    if grep -q "192.168.1.10[0-9]" "$CONFIGS_DIR/deepstream_app.txt"; then
        log_warn "检测到示例RTSP地址，请更新为实际的摄像头地址"
        read -p "是否现在编辑RTSP地址? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            nano "$CONFIGS_DIR/deepstream_app.txt"
        fi
    fi
    
    log_info "配置文件检查完成"
}

# 创建必要目录
create_directories() {
    log_step "创建必要目录..."
    
    DIRS=(
        "$PROJECT_DIR/logs"
        "$PROJECT_DIR/data"
        "$PROJECT_DIR/payloads"
        "$PROJECT_DIR/tracker/NvDCF"
        "$PROJECT_DIR/lib"
        "$PROJECT_DIR/labels"
    )
    
    for dir in "${DIRS[@]}"; do
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    done
}

# 拉取Docker镜像
pull_docker_images() {
    log_step "拉取Docker镜像..."
    
    IMAGES=(
        "nvcr.io/nvidia/deepstream:6.4-triton-multiarch"
        "nvcr.io/nvidia/k8s/dcgm-exporter:3.1.8-3.1.5-ubuntu20.04"
        "confluentinc/cp-kafka:7.4.1"
        "confluentinc/cp-zookeeper:7.4.1"
        "redis:7.2-alpine"
        "prom/prometheus:v2.45.0"
        "grafana/grafana:10.0.3"
    )
    
    for image in "${IMAGES[@]}"; do
        log_info "拉取镜像: $image"
        if ! docker pull "$image"; then
            log_warn "镜像拉取失败: $image (将在启动时自动拉取)"
        fi
    done
}

# 启动服务
start_services() {
    log_step "启动康养AI检测系统..."
    
    cd "$PROJECT_DIR"
    
    # 停止可能存在的旧容器
    log_info "停止现有容器..."
    docker-compose -f "$COMPOSE_FILE" down --remove-orphans
    
    # 启动所有服务
    log_info "启动服务..."
    docker-compose -f "$COMPOSE_FILE" up -d
    
    # 等待服务启动
    log_info "等待服务启动..."
    sleep 30
    
    # 检查服务状态
    check_services_health
}

# 检查服务健康状态
check_services_health() {
    log_step "检查服务健康状态..."
    
    SERVICES=(
        "deepstream-kangyang"
        "dcgm-exporter"
        "kafka-edge"
        "redis-edge"
        "prometheus-edge"
        "grafana-edge"
    )
    
    for service in "${SERVICES[@]}"; do
        if docker ps --format "table {{.Names}}\t{{.Status}}" | grep -q "$service.*Up"; then
            log_info "✓ $service 运行正常"
        else
            log_error "✗ $service 运行异常"
            docker logs --tail 20 "$service" 2>/dev/null || true
        fi
    done
    
    # GPU使用情况
    log_info "GPU使用情况:"
    nvidia-smi --query-gpu=name,utilization.gpu,memory.used,memory.total,temperature.gpu --format=csv,noheader
}

# 显示访问信息
show_access_info() {
    log_step "部署完成！访问信息如下："
    
    echo
    echo "🚀 康养AI检测系统 - NVIDIA L4优化版"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    echo "📊 监控服务:"
    echo "  • GPU监控 (DCGM):      http://localhost:9400/metrics"
    echo "  • Prometheus:          http://localhost:9090"
    echo "  • Grafana:             http://localhost:3000 (admin/admin123)"
    echo
    echo "🔧 基础服务:"
    echo "  • Kafka:               localhost:9092"
    echo "  • Redis:               localhost:6379"
    echo
    echo "📈 关键指标:"
    echo "  • 目标处理能力:        22路 × 720p @ 15FPS"
    echo "  • 预期GPU利用率:       70-85%"
    echo "  • 预期推理延迟:        P95 < 300ms"
    echo
    echo "🛠️ 常用命令:"
    echo "  • 查看服务状态:        docker-compose -f $COMPOSE_FILE ps"
    echo "  • 查看DeepStream日志:  docker logs -f deepstream-kangyang"
    echo "  • 查看GPU使用:         nvidia-smi"
    echo "  • 重启服务:            docker-compose -f $COMPOSE_FILE restart"
    echo "  • 停止服务:            docker-compose -f $COMPOSE_FILE down"
    echo
    echo "📁 重要文件位置:"
    echo "  • DeepStream配置:      $PROJECT_DIR/configs/deepstream_app.txt"
    echo "  • 模型文件:            $PROJECT_DIR/models/"
    echo "  • 日志文件:            $PROJECT_DIR/logs/"
    echo
    echo "⚠️  注意事项:"
    echo "  • 确保RTSP地址已更新为实际摄像头地址"
    echo "  • 生产环境请替换占位符模型文件"
    echo "  • 首次运行需要等待1-2分钟完全启动"
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
}

# 性能测试
run_performance_test() {
    log_step "运行性能测试..."
    
    # 等待DeepStream完全启动
    log_info "等待DeepStream完全启动..."
    sleep 60
    
    # 检查GPU利用率
    log_info "当前GPU状态:"
    nvidia-smi
    
    # 检查Docker容器资源使用
    log_info "容器资源使用情况:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
    
    # 运行基准测试
    if [[ -f "$PROJECT_DIR/scripts/performance_test.py" ]]; then
        log_info "运行基准测试脚本..."
        python3 "$PROJECT_DIR/scripts/performance_test.py" --duration 60
    fi
}

# 主函数
main() {
    echo
    log_info "康养AI检测系统 - NVIDIA L4优化版部署脚本"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    
    # 解析命令行参数
    SKIP_PREREQ=false
    RUN_PERF_TEST=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-prereq)
                SKIP_PREREQ=true
                shift
                ;;
            --performance-test)
                RUN_PERF_TEST=true
                shift
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo
                echo "选项:"
                echo "  --skip-prereq       跳过前置条件检查"
                echo "  --performance-test  部署后运行性能测试"
                echo "  --help, -h          显示此帮助信息"
                echo
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 执行部署流程
    if [[ "$SKIP_PREREQ" != true ]]; then
        check_prerequisites
    fi
    
    create_env_file
    create_directories
    prepare_models
    prepare_configs
    pull_docker_images
    start_services
    show_access_info
    
    if [[ "$RUN_PERF_TEST" == true ]]; then
        run_performance_test
    fi
    
    log_info "部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查上述日志"; exit 1' ERR

# 执行主函数
main "$@"