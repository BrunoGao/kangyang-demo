#!/bin/bash

echo "🚀 启动康养跌倒检测系统（本地版）"
echo ""

# 颜色定义
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# 检查必要工具
check_tool() {
    if ! command -v $1 &> /dev/null; then
        echo -e "${RED}❌ 请先安装 $1${NC}"
        exit 1
    fi
}

# 检查端口是否被占用
check_port() {
    if lsof -i :$1 &> /dev/null; then
        echo -e "${YELLOW}⚠️  端口 $1 已被占用，尝试停止现有进程...${NC}"
        lsof -ti :$1 | xargs kill -9 2>/dev/null || true
        sleep 2
    fi
}

# 等待服务启动
wait_for_service() {
    echo -n "等待 $1 服务启动"
    for i in {1..30}; do
        if curl -f $2 &> /dev/null; then
            echo -e " ${GREEN}✓${NC}"
            return 0
        fi
        echo -n "."
        sleep 1
    done
    echo -e " ${RED}✗${NC}"
    echo -e "${RED}❌ $1 服务启动失败${NC}"
    return 1
}

# 检查Python版本
check_python() {
    if command -v python3 &> /dev/null; then
        PYTHON_CMD="python3"
    elif command -v python &> /dev/null; then
        PYTHON_CMD="python"
    else
        echo -e "${RED}❌ 请先安装 Python${NC}"
        exit 1
    fi
    
    PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
    echo -e "${BLUE}📦 使用 Python $PYTHON_VERSION${NC}"
}

echo -e "${BLUE}🔍 检查系统环境...${NC}"
check_python
check_tool "java"
check_tool "npm"
check_tool "mysql"
check_tool "redis-server"

echo ""
echo -e "${BLUE}🗄️  检查数据库连接...${NC}"

# 停止可能运行的应用服务（不停止数据库）
echo -e "${YELLOW}🛑 停止现有应用服务...${NC}"
check_port 5000
check_port 8080
check_port 3000
check_port 3001

# 检查MySQL连接
echo "检查 MySQL 连接..."
if ! mysql -h 127.0.0.1 -u root -p123456 -e "SELECT 1;" &>/dev/null; then
    echo -e "${RED}❌ MySQL连接失败，请确保MySQL服务已启动${NC}"
    echo "   提示: brew services start mysql 或 brew services start mysql@8.4"
    exit 1
fi

# 检查Redis连接
echo "检查 Redis 连接..."
if ! redis-cli ping &>/dev/null; then
    echo -e "${RED}❌ Redis连接失败，请确保Redis服务已启动${NC}"
    echo "   提示: brew services start redis"
    exit 1
fi

# 创建数据库（如果不存在）
echo "确保数据库存在..."
mysql -h 127.0.0.1 -u root -p123456 -e "CREATE DATABASE IF NOT EXISTS kangyang;" 2>/dev/null || {
    echo -e "${YELLOW}⚠️  数据库创建失败，但会继续运行${NC}"
}

echo -e "${GREEN}✓ 数据库连接正常${NC}"

echo ""
echo -e "${BLUE}🤖 启动AI检测服务...${NC}"
cd ai-detection

# 创建Python虚拟环境
if [ ! -d "venv" ]; then
    echo "创建Python虚拟环境..."
    $PYTHON_CMD -m venv venv
fi

# 激活虚拟环境
source venv/bin/activate

# 安装依赖（使用简化版requirements）
echo "安装Python依赖..."
pip install --upgrade pip -i https://pypi.tuna.tsinghua.edu.cn/simple/ 2>/dev/null || pip install --upgrade pip
pip install -r requirements-demo.txt -i https://pypi.tuna.tsinghua.edu.cn/simple/ 2>/dev/null || pip install -r requirements-demo.txt

# 启动AI服务（在虚拟环境中）
echo "启动AI检测服务..."
nohup ./venv/bin/python app_simple.py > ai-detection.log 2>&1 &
echo $! > ai-detection.pid
cd ..

echo ""
echo -e "${BLUE}🏗️ 构建并启动后端服务...${NC}"
cd backend

# 检查Maven wrapper
if [ ! -f "mvnw" ]; then
    echo "下载Maven Wrapper..."
    curl -O https://repo1.maven.org/maven2/org/apache/maven/wrapper/maven-wrapper/3.2.0/maven-wrapper-3.2.0.jar
    echo '#!/bin/sh
    MAVEN_PROJECTBASEDIR=${MAVEN_BASEDIR:-"$PWD"}
    MAVEN_OPTS="$MAVEN_OPTS -Djava.awt.headless=true"
    exec java $MAVEN_OPTS -classpath maven-wrapper.jar "-Dmaven.multiModuleProjectDirectory=$MAVEN_PROJECTBASEDIR" org.apache.maven.wrapper.MavenWrapperMain "$@"' > mvnw
    chmod +x mvnw
fi

# 构建项目
if [ ! -f "target/fall-detection-backend-1.0.0.jar" ]; then
    echo "构建Spring Boot应用..."
    if [ -f "mvnw" ]; then
        ./mvnw clean package -DskipTests
    else
        mvn clean package -DskipTests
    fi
fi

# 启动后端服务
echo "启动后端服务..."
nohup java -jar target/*.jar > backend.log 2>&1 &
echo $! > backend.pid
cd ..

echo ""
echo -e "${BLUE}🎨 启动前端服务...${NC}"

# 启动管理界面
echo "启动管理界面..."
cd frontend/admin
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi
nohup npm run dev > admin.log 2>&1 &
echo $! > admin.pid
cd ../..

# 启动监控大屏
echo "启动监控大屏..."
cd frontend/monitor
if [ ! -d "node_modules" ]; then
    echo "安装前端依赖..."
    npm install
fi
nohup npm run dev -- --port 3001 > monitor.log 2>&1 &
echo $! > monitor.pid
cd ../..

echo ""
echo -e "${YELLOW}⏳ 等待服务启动完成...${NC}"
sleep 10

# 检查服务状态
echo ""
echo -e "${BLUE}🔍 检查服务状态...${NC}"
wait_for_service "AI检测服务" "http://localhost:5000/health" || echo -e "${YELLOW}⚠️  AI服务可能需要更多时间启动${NC}"
wait_for_service "后端服务" "http://localhost:8080/actuator/health" || wait_for_service "后端服务" "http://localhost:8080" || echo -e "${YELLOW}⚠️  后端服务可能需要更多时间启动${NC}"
wait_for_service "管理界面" "http://localhost:3000" || echo -e "${YELLOW}⚠️  管理界面可能需要更多时间启动${NC}"
wait_for_service "监控大屏" "http://localhost:3001" || echo -e "${YELLOW}⚠️  监控大屏可能需要更多时间启动${NC}"

echo ""
echo -e "${GREEN}✅ 康养跌倒检测系统启动完成！${NC}"
echo ""
echo -e "${BLUE}🔗 访问地址：${NC}"
echo "   管理系统: http://localhost:3000"
echo "   监控大屏: http://localhost:3001"  
echo "   AI服务API: http://localhost:5000"
echo "   后端API: http://localhost:8080"
echo ""
echo -e "${BLUE}📝 日志文件：${NC}"
echo "   AI检测服务: ai-detection/ai-detection.log"
echo "   后端服务: backend/backend.log"
echo "   管理界面: frontend/admin/admin.log"
echo "   监控大屏: frontend/monitor/monitor.log"
echo ""
echo -e "${BLUE}🛑 停止服务：${NC}"
echo "   运行: ./stop_app.sh"
echo ""
echo -e "${GREEN}🎉 系统已就绪，开始使用吧！${NC}"