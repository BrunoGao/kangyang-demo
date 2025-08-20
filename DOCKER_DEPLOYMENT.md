# 康养跌倒检测系统 - Docker部署指南

## 项目概述

康养跌倒检测系统是一个基于AI的智能监控系统，专为养老院等康养机构设计。系统通过计算机视觉技术检测老人跌倒事件，并及时发送预警通知。

## 系统架构

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   管理后台       │    │   监控大屏       │    │   移动端APP     │
│  (Vue.js)       │    │  (Vue.js)       │    │   (预留接口)     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │   Nginx代理     │
                    │   (可选)        │
                    └─────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Spring Boot    │
                    │   后端API       │
                    └─────────────────┘
                                 │
         ┌───────────────────────┼───────────────────────┐
         │                       │                       │
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   AI检测服务     │    │     MySQL       │    │     Redis       │
│  (Python)       │    │   数据存储       │    │   缓存/队列     │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 服务组件

| 服务 | 技术栈 | 端口 | 描述 |
|------|--------|------|------|
| mysql | MySQL 8.0 | 3306 | 主数据库，存储事件、用户等数据 |
| redis | Redis 7 | 6379 | 缓存和消息队列 |
| ai-detection | Python/Flask | 5000 | AI视频分析服务 |
| backend | Spring Boot | 8080 | 后端API服务 |
| admin-frontend | Vue.js/Nginx | 3000 | 管理后台界面 |
| monitor-frontend | Vue.js/Nginx | 3001 | 监控大屏界面 |
| nginx | Nginx | 80/443 | 反向代理(可选) |

## 快速开始

### 1. 环境要求

- Docker 20.10+
- Docker Compose 2.0+
- 最少 4GB RAM
- 最少 10GB 磁盘空间

### 2. 部署步骤

```bash
# 克隆项目
git clone <项目地址>
cd kangyang-demo

# 使用部署脚本启动所有服务
./docker-deploy.sh start

# 或者使用docker-compose直接启动
docker-compose up -d
```

### 3. 访问地址

- **管理后台**: http://localhost:3000
- **监控大屏**: http://localhost:3001  
- **后端API**: http://localhost:8080
- **AI检测服务**: http://localhost:5000

### 4. 默认账号

- 数据库root密码: `root123`
- 业务数据库: `kangyang` / `kangyang123`

## 部署脚本使用

项目提供了便捷的部署脚本 `docker-deploy.sh`：

```bash
# 显示帮助
./docker-deploy.sh help

# 启动所有服务
./docker-deploy.sh start

# 启动包含Nginx代理的完整服务
./docker-deploy.sh start-nginx

# 停止所有服务
./docker-deploy.sh stop

# 重启服务
./docker-deploy.sh restart

# 构建镜像
./docker-deploy.sh build

# 查看服务状态
./docker-deploy.sh status

# 查看日志
./docker-deploy.sh logs [服务名]

# 健康检查
./docker-deploy.sh health

# 清理数据（危险操作）
./docker-deploy.sh cleanup
```

## 开发环境

对于开发调试，使用 `docker-compose.dev.yml`：

```bash
# 启动开发环境
docker-compose -f docker-compose.dev.yml up -d

# 开发环境特性:
# - 热重载
# - 调试端口开放
# - 源码挂载
# - 开发工具集成
```

### 开发端口

| 服务 | 应用端口 | 调试端口 | 描述 |
|------|----------|----------|------|
| backend | 8080 | 8000 | Java远程调试 |
| ai-detection | 5000 | 5678 | Python调试 |
| admin-frontend | 3000 | - | 热重载开发服务器 |
| monitor-frontend | 3001 | - | 热重载开发服务器 |

## 配置文件说明

### 环境变量 (.env)

```bash
# 数据库配置
MYSQL_ROOT_PASSWORD=root123
MYSQL_DATABASE=kangyang
MYSQL_USER=kangyang
MYSQL_PASSWORD=kangyang123

# 服务端口
AI_PORT=5000
BACKEND_PORT=8080
ADMIN_PORT=3000
MONITOR_PORT=3001
```

### 配置文件目录

```
config/
├── mysql/
│   └── my.cnf           # MySQL配置
├── redis/
│   └── redis.conf       # Redis配置
└── nginx/
    ├── nginx.conf       # Nginx主配置
    └── conf.d/
        └── default.conf # 站点配置
```

## 生产环境部署

### 1. 安全配置

```bash
# 修改默认密码
vim .env

# 设置防火墙规则
ufw allow 80/tcp
ufw allow 443/tcp
ufw deny 3306/tcp  # 禁止外部访问数据库
ufw deny 6379/tcp  # 禁止外部访问Redis
```

### 2. SSL证书配置

```bash
# 在nginx配置中添加SSL证书
# config/nginx/conf.d/ssl.conf
```

### 3. 数据备份

```bash
# 数据库备份
docker exec kangyang-mysql mysqldump -u root -p kangyang > backup.sql

# Redis备份
docker exec kangyang-redis redis-cli BGSAVE
```

### 4. 监控告警

建议集成以下监控方案：
- Prometheus + Grafana
- ELK Stack
- 企业微信/钉钉告警

## 故障排查

### 常见问题

1. **服务启动失败**
   ```bash
   # 查看服务日志
   ./docker-deploy.sh logs [服务名]
   
   # 检查端口占用
   netstat -tulpn | grep :端口号
   ```

2. **数据库连接失败**
   ```bash
   # 检查数据库状态
   docker exec kangyang-mysql mysql -u root -p -e "SHOW DATABASES;"
   
   # 重置数据库密码
   docker exec -it kangyang-mysql mysql -u root -p
   ```

3. **前端页面加载失败**
   ```bash
   # 检查nginx代理配置
   docker exec kangyang-nginx nginx -t
   
   # 重载nginx配置
   docker exec kangyang-nginx nginx -s reload
   ```

### 性能调优

1. **JVM参数调优**
   ```bash
   # 在docker-compose.yml中调整JAVA_OPTS
   JAVA_OPTS: "-Xmx1g -Xms512m -XX:+UseG1GC"
   ```

2. **数据库参数调优**
   ```bash
   # 编辑 config/mysql/my.cnf
   innodb_buffer_pool_size = 512M
   max_connections = 500
   ```

3. **Redis内存限制**
   ```bash
   # 编辑 config/redis/redis.conf
   maxmemory 512mb
   maxmemory-policy allkeys-lru
   ```

## 版本更新

```bash
# 备份数据
./docker-deploy.sh stop
cp -r data data_backup

# 拉取新代码
git pull origin main

# 重建并启动
./docker-deploy.sh build
./docker-deploy.sh start
```

## 技术支持

- 项目文档: [CLAUDE.md](./CLAUDE.md)
- 问题反馈: GitHub Issues
- 技术交流: 企业微信群

## 许可证

本项目基于 MIT 许可证开源。