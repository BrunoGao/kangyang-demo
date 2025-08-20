# 康养跌倒检测系统 - 快速启动指南

## 🚀 一键启动

### 方法一：使用脚本（推荐）

```bash
# 启动基础服务（MySQL + Redis）
./docker-deploy.sh start

# 如果遇到构建问题，可以分步启动：
# 1. 先启动基础服务
docker compose -f docker-compose.simple.yml up -d

# 2. 等待数据库启动完成（约60秒）
sleep 60

# 3. 验证基础服务
docker compose -f docker-compose.simple.yml ps
```

### 方法二：直接使用Docker Compose

```bash
# 启动所有服务
docker compose up -d

# 查看服务状态
docker compose ps

# 查看日志
docker compose logs -f
```

## 📊 服务状态检查

```bash
# 检查所有容器状态
docker compose ps

# 检查MySQL连接
docker exec kangyang-mysql mysql -u kangyang -pkangyang123 -e "SHOW DATABASES;"

# 检查Redis连接
docker exec kangyang-redis redis-cli ping
```

## 🌐 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| MySQL | localhost:3306 | 数据库服务 |
| Redis | localhost:6379 | 缓存服务 |
| 管理后台 | http://localhost:3000 | 前端界面 |
| 监控大屏 | http://localhost:3001 | 监控界面 |
| 后端API | http://localhost:8080 | REST API |
| AI检测 | http://localhost:5000 | AI服务 |

## 🔧 常用命令

```bash
# 启动服务
docker compose up -d

# 停止服务
docker compose down

# 重启服务
docker compose restart

# 查看日志
docker compose logs -f [服务名]

# 进入容器
docker exec -it [容器名] bash

# 清理所有数据（谨慎使用）
docker compose down -v
docker system prune -f
```

## 🗄️ 数据库配置

- **数据库名**: kangyang
- **用户名**: kangyang  
- **密码**: kangyang123
- **Root密码**: root123

## 📝 开发模式

```bash
# 启动开发环境（支持热重载）
docker compose -f docker-compose.dev.yml up -d

# 开发环境特性：
# - 源码挂载，支持热重载
# - 调试端口开放
# - 开发工具集成
```

## 🐛 故障排查

### MySQL启动失败
```bash
# 查看MySQL日志
docker compose logs mysql

# 重新初始化数据库
docker compose down -v
docker compose up -d mysql
```

### 端口占用问题
```bash
# 检查端口占用
netstat -tulpn | grep :3306
netstat -tulpn | grep :6379

# 修改.env文件中的端口配置
vim .env
```

### 内存不足
```bash
# 检查Docker资源使用
docker stats

# 清理未使用的镜像和容器
docker system prune -f
```

## 📚 更多信息

- 完整部署文档: [DOCKER_DEPLOYMENT.md](./DOCKER_DEPLOYMENT.md)
- 项目说明: [CLAUDE.md](./CLAUDE.md)
- 系统架构: [README.md](./README.md)

## ✅ 验证部署成功

1. 所有容器状态为 `Up` 且 `healthy`
2. 数据库连接测试成功
3. Redis连接测试返回 `PONG`
4. 可以访问前端页面（如果已启动）

```bash
# 一键检查所有服务健康状态
./docker-deploy.sh health
```