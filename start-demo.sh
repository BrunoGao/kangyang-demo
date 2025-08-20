#!/bin/bash

echo "🚀 启动康养跌倒检测系统演示"

# 检查Docker是否安装
if ! command -v docker &> /dev/null; then
    echo "❌ 请先安装Docker"
    exit 1
fi

# 检查Docker Compose是否安装
if ! command -v docker-compose &> /dev/null; then
    echo "❌ 请先安装Docker Compose"
    exit 1
fi

echo "📦 启动基础服务（MySQL、Redis）..."
docker-compose up -d mysql redis

echo "⏳ 等待数据库启动..."
sleep 10

echo "🤖 启动AI检测服务..."
cd ai-detection
if [ ! -d "venv" ]; then
    echo "📦 创建Python虚拟环境..."
    python3 -m venv venv
    source venv/bin/activate
    pip install -r requirements.txt
else
    source venv/bin/activate
fi

echo "🔄 启动AI检测服务后台进程..."
nohup python app.py > ai-detection.log 2>&1 &
echo $! > ai-detection.pid
cd ..

echo "🏗️ 构建并启动后端服务..."
cd backend
if [ ! -f "target/fall-detection-backend-1.0.0.jar" ]; then
    echo "📦 构建Spring Boot应用..."
    ./mvnw clean package -DskipTests
fi

echo "🔄 启动后端服务..."
nohup java -jar target/fall-detection-backend-1.0.0.jar > backend.log 2>&1 &
echo $! > backend.pid
cd ..

echo "⏳ 等待后端服务启动..."
sleep 15

echo "🎨 启动前端管理界面..."
cd frontend/admin
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

echo "🔄 启动管理界面..."
nohup npm run dev > admin.log 2>&1 &
echo $! > admin.pid
cd ../..

echo "📺 启动监控大屏..."
cd frontend/monitor
if [ ! -d "node_modules" ]; then
    echo "📦 安装前端依赖..."
    npm install
fi

echo "🔄 启动监控大屏..."
nohup npm run dev > monitor.log 2>&1 &
echo $! > monitor.pid
cd ../..

echo ""
echo "✅ 康养跌倒检测系统启动完成！"
echo ""
echo "🔗 访问地址："
echo "   管理系统: http://localhost:3000"
echo "   监控大屏: http://localhost:3001"
echo "   AI服务API: http://localhost:5000"
echo "   后端API: http://localhost:8080"
echo ""
echo "📝 日志文件："
echo "   AI检测服务: ai-detection/ai-detection.log"
echo "   后端服务: backend/backend.log"
echo "   管理界面: frontend/admin/admin.log"
echo "   监控大屏: frontend/monitor/monitor.log"
echo ""
echo "🛑 停止服务: ./stop-demo.sh"