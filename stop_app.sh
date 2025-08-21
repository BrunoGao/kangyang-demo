#!/bin/bash

echo "🛑 停止康养跌倒检测系统"

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 停止进程函数
stop_service() {
    local service_name=$1
    local pid_file=$2
    
    if [ -f "$pid_file" ]; then
        local pid=$(cat "$pid_file")
        if kill -0 "$pid" 2>/dev/null; then
            echo -e "${YELLOW}停止 $service_name (PID: $pid)...${NC}"
            kill "$pid"
            sleep 2
            if kill -0 "$pid" 2>/dev/null; then
                echo -e "${RED}强制停止 $service_name...${NC}"
                kill -9 "$pid"
            fi
        fi
        rm -f "$pid_file"
    else
        echo -e "${BLUE}$service_name 未运行${NC}"
    fi
}

# 停止端口进程
stop_port() {
    local port=$1
    local service_name=$2
    
    if lsof -i :$port &> /dev/null; then
        echo -e "${YELLOW}停止端口 $port 上的 $service_name 进程...${NC}"
        lsof -ti :$port | xargs kill -9 2>/dev/null || true
    fi
}

echo ""
echo -e "${BLUE}🔍 停止应用服务...${NC}"

# 停止前端服务
stop_service "监控大屏" "frontend/monitor/monitor.pid"
stop_service "管理界面" "frontend/admin/admin.pid"

# 停止后端服务
stop_service "后端服务" "backend/backend.pid"

# 停止AI检测服务  
stop_service "AI检测服务" "ai-detection/ai-detection.pid"

# 额外检查端口进程
echo ""
echo -e "${BLUE}🔍 检查并清理端口占用...${NC}"
stop_port 3001 "监控大屏"
stop_port 3000 "管理界面"
stop_port 8080 "后端服务"
stop_port 5000 "AI检测服务"

echo ""
echo -e "${BLUE}🗄️  保留数据库服务运行...${NC}"
echo -e "${YELLOW}💡 MySQL和Redis服务保持运行状态${NC}"

# 清理日志文件（可选）
echo ""
read -p "是否清理日志文件? (y/N): " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}清理日志文件...${NC}"
    rm -f ai-detection/ai-detection.log
    rm -f backend/backend.log
    rm -f frontend/admin/admin.log
    rm -f frontend/monitor/monitor.log
    echo -e "${GREEN}✓ 日志文件已清理${NC}"
fi

echo ""
echo -e "${GREEN}✅ 康养跌倒检测系统已完全停止${NC}"
echo ""
echo -e "${BLUE}💡 提示：${NC}"
echo "   - 重新启动: ./start_app.sh"
echo "   - 查看进程: ps aux | grep -E '(kangyang|java|python|node)'"
echo "   - 检查端口: lsof -i :3000,:3001,:5000,:8080"