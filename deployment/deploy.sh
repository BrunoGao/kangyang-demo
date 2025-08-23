#!/bin/bash

# 康养AI检测系统 - 部署脚本
set -e

# 颜色定义
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

log_info() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# 检查Docker
check_docker() {
    if ! command -v docker &> /dev/null; then
        log_error "Docker未安装"
        exit 1
    fi
    
    if ! docker compose version &> /dev/null; then
        log_error "Docker Compose未安装"
        exit 1
    fi
    
    log_info "✅ Docker环境检查通过"
}

# 创建环境配置
create_env() {
    if [ ! -f ".env" ]; then
        cat > .env << EOF
# 康养AI检测系统环境配置
DB_PASSWORD=kangyang123456
WECHAT_ENABLED=true
WECHAT_WEBHOOK_URL=
EDGE_API_KEY=$(openssl rand -hex 32 2>/dev/null || echo "default_api_key")
TZ=Asia/Shanghai
EOF
        log_info "✅ 环境配置文件已创建"
    fi
}

# 部署服务
deploy() {
    log_info "开始部署康养AI检测系统..."
    
    case "${1:-all}" in
        "all")
            docker compose up -d --build
            ;;
        "backend")
            docker compose up -d --build mysql redis management-backend edge-controller-1 edge-controller-2
            ;;
        "stop")
            docker compose down
            log_info "服务已停止"
            return 0
            ;;
        *)
            log_error "使用方法: $0 [all|backend|stop]"
            exit 1
            ;;
    esac
    
    log_info "✅ 部署完成"
}

# 显示访问信息
show_info() {
    log_info "🎉 康养AI检测系统部署完成！"
    echo
    echo "访问地址："
    echo "  📊 管理平台前端: http://localhost:3000"
    echo "  🔧 管理平台API: http://localhost:8080/api"
    echo "  🤖 边缘控制器#1: http://localhost:8084"
    echo "  🤖 边缘控制器#2: http://localhost:8085"
    echo
    echo "常用命令："
    echo "  查看日志: docker compose logs -f [服务名]"
    echo "  停止系统: ./deploy.sh stop"
    echo "  查看状态: docker compose ps"
}

# 主函数
main() {
    echo "=========================================="
    echo "     康养AI检测系统 - 部署脚本"
    echo "=========================================="
    echo
    
    check_docker
    create_env
    deploy "$1"
    
    if [ "$1" != "stop" ]; then
        show_info
    fi
}

main "$@"