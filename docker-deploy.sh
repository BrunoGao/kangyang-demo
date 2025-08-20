#!/bin/bash

# 康养跌倒检测系统 Docker 部署脚本
# 使用方法: ./docker-deploy.sh [start|stop|restart|build|logs]

set -e

PROJECT_NAME="kangyang"
COMPOSE_FILE="docker-compose.yml"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 打印带颜色的消息
print_message() {
    local color=$1
    local message=$2
    echo -e "${color}[$(date +'%Y-%m-%d %H:%M:%S')] ${message}${NC}"
}

# 检查Docker和Docker Compose
check_requirements() {
    print_message $BLUE "检查系统要求..."
    
    if ! command -v docker &> /dev/null; then
        print_message $RED "错误: Docker 未安装"
        exit 1
    fi
    
    # 检查Docker Compose (优先使用 docker compose)
    if docker compose version &> /dev/null; then
        COMPOSE_CMD="docker compose"
    elif command -v docker-compose &> /dev/null; then
        COMPOSE_CMD="docker-compose"
    else
        print_message $RED "错误: Docker Compose 未安装"
        print_message $YELLOW "请安装 Docker Compose 或使用较新版本的 Docker"
        exit 1
    fi
    
    print_message $GREEN "系统要求检查通过 (使用: $COMPOSE_CMD)"
}

# 创建必要的目录
create_directories() {
    print_message $BLUE "创建必要的目录..."
    mkdir -p logs/nginx
    mkdir -p videos
    chmod 755 logs/nginx videos
    print_message $GREEN "目录创建完成"
}

# 构建镜像
build_images() {
    print_message $BLUE "构建Docker镜像..."
    $COMPOSE_CMD build --no-cache
    print_message $GREEN "镜像构建完成"
}

# 检查镜像是否存在
check_images() {
    local missing_images=()
    local services=("ai-detection" "backend" "admin-frontend" "monitor-frontend")
    
    for service in "${services[@]}"; do
        local image_name="kangyang-demo-${service}"
        if ! docker images -q "$image_name" | grep -q .; then
            missing_images+=("$service")
        fi
    done
    
    if [ ${#missing_images[@]} -gt 0 ]; then
        print_message $YELLOW "检测到以下服务缺少镜像: ${missing_images[*]}"
        print_message $BLUE "正在构建缺少的镜像..."
        
        for service in "${missing_images[@]}"; do
            print_message $YELLOW "构建 $service 镜像..."
            $COMPOSE_CMD build "$service"
        done
        
        print_message $GREEN "镜像构建完成"
    else
        print_message $GREEN "所有服务镜像已存在，跳过构建"
    fi
}

# 启动服务
start_services() {
    print_message $BLUE "启动康养系统服务..."
    create_directories
    
    # 检查并构建缺少的镜像
    check_images
    
    # 启动基础服务（MySQL, Redis）
    print_message $YELLOW "启动基础服务..."
    $COMPOSE_CMD up -d mysql redis
    
    # 等待数据库准备就绪
    print_message $YELLOW "等待数据库初始化..."
    sleep 30
    
    # 启动应用服务
    print_message $YELLOW "启动应用服务..."
    $COMPOSE_CMD up -d ai-detection backend
    
    # 等待后端服务启动
    print_message $YELLOW "等待后端服务启动..."
    sleep 20
    
    # 启动前端服务
    print_message $YELLOW "启动前端服务..."
    $COMPOSE_CMD up -d admin-frontend monitor-frontend
    
    print_message $GREEN "所有服务启动完成"
    show_status
}

# 启动服务（包含Nginx）
start_with_nginx() {
    print_message $BLUE "启动康养系统服务（包含Nginx反向代理）..."
    COMPOSE_PROFILES=nginx start_services
    $COMPOSE_CMD --profile nginx up -d nginx
    print_message $GREEN "Nginx代理服务启动完成"
}

# 停止服务
stop_services() {
    print_message $BLUE "停止康养系统服务..."
    $COMPOSE_CMD down
    print_message $GREEN "服务停止完成"
}

# 重启服务
restart_services() {
    print_message $BLUE "重启康养系统服务..."
    stop_services
    sleep 5
    start_services
}

# 查看日志
show_logs() {
    local service=$1
    if [ -n "$service" ]; then
        print_message $BLUE "查看 $service 服务日志..."
        $COMPOSE_CMD logs -f "$service"
    else
        print_message $BLUE "查看所有服务日志..."
        $COMPOSE_CMD logs -f
    fi
}

# 显示服务状态
show_status() {
    print_message $BLUE "服务状态:"
    $COMPOSE_CMD ps
    
    echo
    print_message $BLUE "访问地址:"
    echo "  管理后台: http://localhost:3000"
    echo "  监控大屏: http://localhost:3001"
    echo "  后端API: http://localhost:8080"
    echo "  AI检测: http://localhost:5000"
    echo "  MySQL: localhost:3306"
    echo "  Redis: localhost:6379"
    
    if $COMPOSE_CMD ps nginx &> /dev/null; then
        echo "  Nginx代理: http://localhost"
        echo "    - 管理后台: http://localhost"
        echo "    - 监控大屏: http://monitor.kangyang.local"
        echo "    - API服务: http://api.kangyang.local"
        echo "    - AI服务: http://ai.kangyang.local"
    fi
}

# 清理数据
cleanup() {
    print_message $YELLOW "警告: 这将删除所有容器和数据卷"
    read -p "确定继续吗? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        print_message $BLUE "清理系统数据..."
        $COMPOSE_CMD down -v
        docker system prune -f
        print_message $GREEN "清理完成"
    else
        print_message $YELLOW "清理操作已取消"
    fi
}

# 健康检查
health_check() {
    print_message $BLUE "执行健康检查..."
    
    services=("mysql" "redis" "ai-detection" "backend" "admin-frontend" "monitor-frontend")
    
    for service in "${services[@]}"; do
        if $COMPOSE_CMD ps "$service" | grep -q "Up"; then
            print_message $GREEN "✓ $service 运行正常"
        else
            print_message $RED "✗ $service 运行异常"
        fi
    done
}

# 显示帮助
show_help() {
    echo "康养跌倒检测系统 Docker 部署脚本"
    echo
    echo "使用方法: $0 [命令] [选项]"
    echo
    echo "命令:"
    echo "  start         启动所有服务（自动检测并构建缺少的镜像）"
    echo "  start-nginx   启动所有服务（包含Nginx）"
    echo "  stop          停止所有服务"
    echo "  restart       重启所有服务"
    echo "  build         构建所有Docker镜像"
    echo "  rebuild       强制重新构建所有镜像"
    echo "  logs [服务名] 查看日志"
    echo "  status        查看服务状态"
    echo "  health        健康检查"
    echo "  cleanup       清理数据（危险操作）"
    echo "  help          显示帮助"
    echo
    echo "示例:"
    echo "  $0 start              # 启动所有服务"
    echo "  $0 logs backend       # 查看后端服务日志"
    echo "  $0 restart            # 重启所有服务"
}

# 主函数
main() {
    check_requirements
    
    case "${1:-help}" in
        "start")
            start_services
            ;;
        "start-nginx")
            start_with_nginx
            ;;
        "stop")
            stop_services
            ;;
        "restart")
            restart_services
            ;;
        "build")
            build_images
            ;;
        "rebuild")
            print_message $BLUE "强制重新构建所有镜像..."
            $COMPOSE_CMD build --no-cache
            print_message $GREEN "镜像重新构建完成"
            ;;
        "logs")
            show_logs "$2"
            ;;
        "status")
            show_status
            ;;
        "health")
            health_check
            ;;
        "cleanup")
            cleanup
            ;;
        "help"|"-h"|"--help")
            show_help
            ;;
        *)
            print_message $RED "未知命令: $1"
            show_help
            exit 1
            ;;
    esac
}

# 执行主函数
main "$@"