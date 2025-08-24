# 康养AI检测系统 - 阿里云容器镜像部署指南

## 📋 概述

本文档详细介绍如何使用阿里云容器镜像服务部署康养AI检测系统。该系统采用完全容器化部署，支持一键启动所有服务。

## 🏗️ 系统架构

```
┌─────────────────────────────────────────────────────────────┐
│                     阿里云容器镜像仓库                       │
├─────────────────────────────────────────────────────────────┤
│  • ljwx-ky-mysql:1.0.1         • ljwx-ky-backend:1.0.1     │
│  • ljwx-ky-frontend:1.0.1      • ljwx-ky-edge-controller:1.0.1 │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│                      本地部署环境                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   前端管理   │  │   后端API   │  │   数据库    │         │
│  │   :80       │  │   :8080     │  │   :3306     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │ 边缘控制器1  │  │ 边缘控制器2  │  │   监控系统   │         │
│  │   :8084     │  │   :8085     │  │   :9092     │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 快速部署

### 前置条件

1. **操作系统**: Linux (Ubuntu 18.04+, CentOS 7+)
2. **Docker**: >= 20.10.0
3. **Docker Compose**: >= 2.0.0
4. **内存**: 最少 8GB RAM
5. **磁盘**: 最少 50GB 可用空间
6. **网络**: 可访问互联网

### 一键部署

```bash
# 1. 克隆项目
git clone https://github.com/BrunoGao/kangyang-demo.git
cd kangyang-demo/deployment

# 2. 执行部署脚本
./deploy-aliyun.sh
```

## 📦 容器镜像详情

### 镜像列表

| 服务名称 | 镜像地址 | 版本 | 用途 |
|---------|----------|------|------|
| MySQL数据库 | `crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-mysql:1.0.1` | 1.0.1 | 数据存储 |
| 后端API | `crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-backend:1.0.1` | 1.0.1 | 业务逻辑 |
| 前端管理 | `crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-frontend:1.0.1` | 1.0.1 | 用户界面 |
| 边缘控制器 | `crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-edge-controller:1.0.1` | 1.0.1 | AI检测 |

### 镜像特性

#### MySQL数据库镜像
- **基础镜像**: mysql:8.0
- **预配置**: 字符集utf8mb4，时区Asia/Shanghai
- **初始化**: 自动创建数据库表和示例数据
- **配置优化**: 针对AI检测场景的性能优化

#### 后端API镜像  
- **基础镜像**: openjdk:17-jdk-slim
- **框架**: Spring Boot 3.2
- **特性**: RESTful API, 微信告警, 边缘设备管理
- **监控**: 集成Prometheus指标

#### 前端管理镜像
- **基础镜像**: nginx:alpine
- **框架**: Vue3 + Element Plus
- **特性**: 响应式设计, ECharts图表, 实时监控
- **优化**: Gzip压缩, 资源缓存

#### 边缘控制器镜像
- **基础镜像**: python:3.11-slim
- **AI框架**: OpenCV + 自主算法
- **特性**: 22路视频并发, 跌倒/火焰/烟雾检测
- **性能**: 优化内存使用, GPU加速支持

## ⚙️ 配置说明

### 环境变量配置

| 变量名 | 默认值 | 说明 |
|--------|--------|------|
| TZ | Asia/Shanghai | 时区设置 |
| MYSQL_ROOT_PASSWORD | kangyang123 | MySQL root密码 |
| MYSQL_PASSWORD | kangyang_pass | 业务用户密码 |
| REDIS_PASSWORD | kangyang_redis_pass | Redis密码 |
| GF_SECURITY_ADMIN_PASSWORD | kangyang_grafana_pass | Grafana密码 |

### 端口映射

| 服务 | 内部端口 | 外部端口 | 协议 |
|------|----------|----------|------|
| 前端管理 | 80 | 80, 3000 | HTTP |
| 后端API | 8080 | 8080 | HTTP |
| MySQL | 3306 | 3306 | TCP |
| Redis | 6379 | 6379 | TCP |
| 边缘控制器1 | 8084 | 8084 | HTTP |
| 边缘控制器2 | 8084 | 8085 | HTTP |
| Prometheus | 9090 | 9092 | HTTP |
| Grafana | 3000 | 3001 | HTTP |

### 数据卷挂载

```yaml
volumes:
  - mysql-data:/var/lib/mysql              # MySQL数据
  - redis-data:/data                       # Redis数据
  - edge-data:/data/edge-controller        # 边缘数据
  - ./logs/mysql:/var/log/mysql           # MySQL日志
  - ./logs/edge-1:/app/logs               # 边缘控制器1日志
  - ./logs/edge-2:/app/logs               # 边缘控制器2日志
  - ./mp4:/app/mp4                        # 测试视频文件
```

## 🔧 手动部署步骤

如果需要手动部署，请按照以下步骤操作：

### 1. 登录阿里云容器镜像服务

```bash
docker login --username=brunogao crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com
# 输入密码: admin123
```

### 2. 拉取镜像

```bash
docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-mysql:1.0.1
docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-backend:1.0.1
docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-frontend:1.0.1
docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-edge-controller:1.0.1
```

### 3. 创建目录结构

```bash
mkdir -p logs/{mysql,edge-1,edge-2}
mkdir -p data/{prometheus,grafana}
mkdir -p monitoring/grafana/provisioning/{dashboards,datasources}
mkdir -p mp4
```

### 4. 启动服务

```bash
docker-compose -f docker-compose-aliyun.yml up -d
```

## 📊 服务监控

### Prometheus指标

系统集成了Prometheus监控，可以监控以下指标：

- **系统指标**: CPU、内存、磁盘、网络使用率
- **业务指标**: API请求量、响应时间、错误率
- **AI指标**: 检测帧率、检测准确率、事件数量
- **数据库指标**: 连接数、查询性能、存储使用量

### Grafana仪表板

预配置的Grafana仪表板包含：

1. **系统总览**: 整体运行状态和关键指标
2. **边缘设备**: 两个边缘控制器的详细监控
3. **检测统计**: 跌倒、火焰、烟雾检测统计
4. **性能分析**: 各组件性能分析和趋势
5. **告警记录**: 历史告警和处理情况

## 🔍 故障排查

### 常见问题

#### 1. 服务启动失败

```bash
# 查看服务状态
docker-compose -f docker-compose-aliyun.yml ps

# 查看特定服务日志
docker-compose -f docker-compose-aliyun.yml logs -f [服务名]

# 重启服务
docker-compose -f docker-compose-aliyun.yml restart [服务名]
```

#### 2. 镜像拉取失败

```bash
# 检查网络连接
ping crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com

# 重新登录
docker login --username=brunogao crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com

# 手动拉取镜像
docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-edge-controller:1.0.1
```

#### 3. 数据库连接失败

```bash
# 检查MySQL容器状态
docker exec -it kangyang-mysql mysqladmin ping -u root -pkangyang123

# 重置数据库
docker-compose -f docker-compose-aliyun.yml down
docker volume rm deployment_mysql-data
docker-compose -f docker-compose-aliyun.yml up -d mysql
```

#### 4. 端口冲突

```bash
# 检查端口占用
netstat -tlnp | grep :80
netstat -tlnp | grep :8080

# 修改端口映射
vi docker-compose-aliyun.yml
# 修改ports配置，如 "8081:8080"
```

### 日志分析

#### 重要日志位置

```bash
# MySQL日志
tail -f logs/mysql/error.log

# 边缘控制器日志
tail -f logs/edge-1/app.log
tail -f logs/edge-2/app.log

# Docker Compose日志
docker-compose -f docker-compose-aliyun.yml logs -f --tail=100
```

## 🔧 性能调优

### 系统优化建议

#### 1. 内存优化

```yaml
# 调整MySQL内存配置
environment:
  - MYSQL_INNODB_BUFFER_POOL_SIZE=2G
  - MYSQL_KEY_BUFFER_SIZE=64M
```

#### 2. 磁盘优化

```bash
# 使用SSD存储
# 定期清理日志文件
find logs/ -name "*.log" -mtime +7 -delete

# 数据库定期备份和清理
docker exec kangyang-mysql mysqldump -u root -pkangyang123 kangyang_db > backup.sql
```

#### 3. 网络优化

```yaml
# 使用自定义网络
networks:
  kangyang-network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.20.0.0/16
```

## 🔄 更新升级

### 版本更新

```bash
# 1. 拉取新版本镜像
docker pull crpi-yilnm6upy4pmbp67.cn-shenzhen.personal.cr.aliyuncs.com/ljwx-ky/ljwx-ky-edge-controller:1.0.2

# 2. 更新docker-compose文件中的版本号
vi docker-compose-aliyun.yml

# 3. 滚动更新
docker-compose -f docker-compose-aliyun.yml up -d --no-deps edge-controller-1
docker-compose -f docker-compose-aliyun.yml up -d --no-deps edge-controller-2
```

### 数据备份

```bash
# 备份数据库
docker exec kangyang-mysql mysqldump -u root -pkangyang123 --all-databases > backup_$(date +%Y%m%d_%H%M%S).sql

# 备份Redis
docker exec kangyang-redis redis-cli --rdb /data/dump_$(date +%Y%m%d_%H%M%S).rdb

# 备份配置文件
tar -czf config_backup_$(date +%Y%m%d_%H%M%S).tar.gz monitoring/ logs/ data/
```

## 📞 技术支持

### 联系方式

- **项目仓库**: https://github.com/BrunoGao/kangyang-demo
- **问题报告**: https://github.com/BrunoGao/kangyang-demo/issues

### 系统要求

- **最低配置**: 4核CPU + 8GB RAM + 50GB存储
- **推荐配置**: 8核CPU + 16GB RAM + 100GB SSD
- **生产配置**: 16核CPU + 32GB RAM + 500GB SSD + GPU加速

### 许可证

本项目采用MIT许可证，详情请参考项目根目录的LICENSE文件。

---

**康养AI检测系统** - 让科技守护每一位老人的安全与健康 💙