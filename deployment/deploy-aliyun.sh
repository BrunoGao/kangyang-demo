#!/bin/bash
# 康养AI检测系统 - 阿里云容器镜像一键部署脚本

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

# 创建必要目录
create_directories() {
    log_step "创建必要目录..."
    
    DIRS=(
        "$SCRIPT_DIR/logs/mysql"
        "$SCRIPT_DIR/logs/edge-1"
        "$SCRIPT_DIR/logs/edge-2"
        "$SCRIPT_DIR/data/prometheus"
        "$SCRIPT_DIR/data/grafana"
        "$SCRIPT_DIR/monitoring/grafana/provisioning/dashboards"
        "$SCRIPT_DIR/monitoring/grafana/provisioning/datasources"
        "$SCRIPT_DIR/mp4"
    )
    
    for dir in "${DIRS[@]}"; do
        mkdir -p "$dir"
        log_info "创建目录: $dir"
    done
    
    # 设置grafana目录权限
    sudo chown -R 472:472 "$SCRIPT_DIR/data/grafana" 2>/dev/null || true
}

# 创建Prometheus配置
create_prometheus_config() {
    log_step "创建Prometheus监控配置..."
    
    cat > "$SCRIPT_DIR/monitoring/prometheus.yml" << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

rule_files:
  # - "first_rules.yml"
  # - "second_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'kangyang-backend'
    static_configs:
      - targets: ['172.20.0.20:8080']
    metrics_path: '/actuator/prometheus'
    scrape_interval: 30s

  - job_name: 'kangyang-edge-1'
    static_configs:
      - targets: ['172.20.0.30:9090']
    scrape_interval: 15s

  - job_name: 'kangyang-edge-2'
    static_configs:
      - targets: ['172.20.0.31:9090']
    scrape_interval: 15s

  - job_name: 'mysql-exporter'
    static_configs:
      - targets: ['172.20.0.10:9104']
    scrape_interval: 30s

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['172.20.0.11:9121']
    scrape_interval: 30s
EOF

    log_info "Prometheus配置文件创建完成"
}

# 创建Grafana数据源配置
create_grafana_config() {
    log_step "创建Grafana配置..."
    
    # 数据源配置
    cat > "$SCRIPT_DIR/monitoring/grafana/provisioning/datasources/prometheus.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://172.20.0.40:9090
    isDefault: true
    editable: true
EOF

    # 仪表板配置
    cat > "$SCRIPT_DIR/monitoring/grafana/provisioning/dashboards/dashboard.yml" << EOF
apiVersion: 1

providers:
  - name: 'default'
    orgId: 1
    folder: ''
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /etc/grafana/provisioning/dashboards
EOF

    log_info "Grafana配置文件创建完成"
}

# 拉取最新镜像
pull_images() {
    log_step "拉取最新Docker镜像..."
    
    IMAGES=(
        "crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-mysql:1.0.1"
        "crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-backend:1.0.1"
        "crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-frontend:1.0.1"
        "crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-edge-controller:1.0.1"
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

# 检查Docker登录状态
check_docker_login() {
    log_step "检查Docker登录状态..."
    
    if ! docker images | grep -q "crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com"; then
        log_warn "未检测到阿里云镜像，尝试登录..."
        echo "请输入阿里云容器镜像服务密码:"
        docker login --username=brunogao crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com
    else
        log_info "Docker登录状态正常"
    fi
}

# 启动服务
start_services() {
    log_step "启动康养AI检测系统..."
    
    cd "$SCRIPT_DIR"
    
    # 停止可能存在的旧容器
    log_info "停止现有容器..."
    docker-compose -f docker-compose-aliyun.yml down --remove-orphans 2>/dev/null || true
    
    # 启动所有服务
    log_info "启动服务..."
    docker-compose -f docker-compose-aliyun.yml up -d
    
    # 等待服务启动
    log_info "等待服务启动完成..."
    sleep 30
    
    # 检查服务状态
    check_services_health
}

# 检查服务健康状态
check_services_health() {
    log_step "检查服务健康状态..."
    
    SERVICES=(
        "kangyang-mysql:3306"
        "kangyang-redis:6379"
        "kangyang-backend:8080"
        "kangyang-frontend:80"
        "kangyang-edge-1:8084"
        "kangyang-edge-2:8084"
        "kangyang-prometheus:9090"
        "kangyang-grafana:3000"
    )
    
    for service in "${SERVICES[@]}"; do
        container_name=$(echo $service | cut -d: -f1)
        port=$(echo $service | cut -d: -f2)
        
        if docker ps --format "table {{.Names}}\\t{{.Status}}" | grep -q "$container_name.*Up"; then
            log_info "✓ $container_name 运行正常"
        else
            log_error "✗ $container_name 运行异常"
            docker logs --tail 20 "$container_name" 2>/dev/null || true
        fi
    done
}

# 显示访问信息
show_access_info() {
    log_step "部署完成！访问信息如下："
    
    # 获取主机IP
    HOST_IP=$(hostname -I | awk '{print $1}' 2>/dev/null || echo "localhost")
    
    echo
    echo "🚀 康养AI检测系统 - 阿里云容器镜像版"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    echo "📊 管理平台:"
    echo "  • 前端管理界面:        http://$HOST_IP"
    echo "  • 后端API接口:         http://$HOST_IP:8080"
    echo "  • API文档地址:         http://$HOST_IP:8080/swagger-ui.html"
    echo
    echo "🤖 边缘控制器:"
    echo "  • 边缘控制器#1:        http://$HOST_IP:8084"
    echo "  • 边缘控制器#2:        http://$HOST_IP:8085"
    echo "  • 视频测试页面:        http://$HOST_IP:3000/video-test"
    echo
    echo "📈 监控服务:"
    echo "  • Prometheus:          http://$HOST_IP:9092"
    echo "  • Grafana:             http://$HOST_IP:3001 (admin/kangyang_grafana_pass)"
    echo
    echo "💾 数据库服务:"
    echo "  • MySQL:               $HOST_IP:3306 (root/kangyang123)"
    echo "  • Redis:               $HOST_IP:6379 (密码: kangyang_redis_pass)"
    echo
    echo "🛠️ 常用命令:"
    echo "  • 查看服务状态:        docker-compose -f docker-compose-aliyun.yml ps"
    echo "  • 查看服务日志:        docker-compose -f docker-compose-aliyun.yml logs -f [服务名]"
    echo "  • 重启服务:            docker-compose -f docker-compose-aliyun.yml restart [服务名]"
    echo "  • 停止服务:            docker-compose -f docker-compose-aliyun.yml down"
    echo
    echo "📁 重要目录:"
    echo "  • 日志目录:            $SCRIPT_DIR/logs/"
    echo "  • 数据目录:            $SCRIPT_DIR/data/"
    echo "  • 配置目录:            $SCRIPT_DIR/monitoring/"
    echo
    echo "🔧 默认账号信息:"
    echo "  • 数据库root密码:      kangyang123"
    echo "  • 数据库用户密码:      kangyang_pass"
    echo "  • Redis密码:           kangyang_redis_pass"
    echo "  • Grafana密码:         kangyang_grafana_pass"
    echo
    echo "⚠️  注意事项:"
    echo "  • 首次启动需要等待2-3分钟完全就绪"
    echo "  • 生产环境请修改默认密码"
    echo "  • 确保防火墙已开放相应端口"
    echo
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
}

# 主函数
main() {
    echo
    log_info "康养AI检测系统 - 阿里云容器镜像一键部署脚本"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo
    
    # 解析命令行参数
    SKIP_PULL=false
    SKIP_LOGIN=false
    
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-pull)
                SKIP_PULL=true
                shift
                ;;
            --skip-login)
                SKIP_LOGIN=true
                shift
                ;;
            --help|-h)
                echo "用法: $0 [选项]"
                echo
                echo "选项:"
                echo "  --skip-pull      跳过镜像拉取"
                echo "  --skip-login     跳过登录检查"
                echo "  --help, -h       显示此帮助信息"
                echo
                exit 0
                ;;
            *)
                log_error "未知参数: $1"
                exit 1
                ;;
        esac
    done
    
    # 检查Docker是否安装
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装，请先安装Docker"
        exit 1
    fi
    
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose未安装，请先安装Docker Compose"
        exit 1
    fi
    
    # 执行部署流程
    if [[ "$SKIP_LOGIN" != true ]]; then
        check_docker_login
    fi
    
    create_directories
    create_prometheus_config
    create_grafana_config
    
    if [[ "$SKIP_PULL" != true ]]; then
        pull_images
    fi
    
    start_services
    show_access_info
    
    log_info "部署完成！"
}

# 错误处理
trap 'log_error "部署过程中发生错误，请检查上述日志"; exit 1' ERR

# 执行主函数
main "$@"