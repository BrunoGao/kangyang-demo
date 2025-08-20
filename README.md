# 康养跌倒检测系统 🏥

<div align="center">

![Logo](https://img.shields.io/badge/AI-康养系统-blue?style=for-the-badge)
![Docker](https://img.shields.io/badge/Docker-完全容器化-blue?style=for-the-badge&logo=docker)
![License](https://img.shields.io/badge/License-MIT-green?style=for-the-badge)

**基于AI视觉算法的智能跌倒检测与告警系统**

*为养老院和康养机构提供实时、准确的跌倒检测服务*

</div>

## ✨ 系统特性

- 🤖 **AI智能检测** - 基于YOLO + PoseNet的跌倒检测算法
- ⚡ **实时处理** - 支持多路视频流实时分析
- 📱 **多端展示** - 管理后台 + 监控大屏 + 移动端(规划)
- 🐳 **完全容器化** - Docker一键部署，开箱即用
- 🔔 **智能告警** - 微信推送 + 多级告警机制
- 📊 **数据可视化** - 实时图表和历史数据分析
- 🔐 **安全可靠** - 本地处理，隐私保护

## 🏗️ 系统架构

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
│  (Python 3.12)  │    │   数据存储       │    │   缓存/队列     │
│  + 测试框架      │    │                 │    │                 │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 📁 项目结构

```
📦 kangyang-demo
├── 🤖 ai-detection/              # AI检测服务 (Python 3.12)
│   ├── app.py                   # 主应用
│   ├── fall_detector.py         # 跌倒检测算法
│   ├── test_framework.py        # 自动化测试框架
│   ├── test_framework_web.py    # Web测试界面
│   ├── video_resource_manager.py # 视频资源管理
│   ├── start_test_platform.py   # 测试平台启动器
│   ├── VIDEO_TESTING_GUIDE.md   # 完整测试指南
│   ├── requirements.txt         # Python依赖
│   └── Dockerfile              # Docker配置
├── 🚀 backend/                   # 后端API (Spring Boot)
│   ├── src/                    # 源代码
│   ├── pom.xml                 # Maven配置
│   └── Dockerfile              # Docker配置
├── 🎨 frontend/                  # 前端界面
│   ├── admin/                  # 管理后台 (Vue.js)
│   └── monitor/                # 监控大屏 (Vue.js)
├── ⚙️ config/                    # 配置文件
│   ├── mysql/                  # MySQL配置
│   ├── redis/                  # Redis配置
│   └── nginx/                  # Nginx配置
├── 🐳 docker-compose.yml         # Docker编排文件
├── 🚀 docker-deploy.sh          # 一键部署脚本
├── 📚 QUICK_START.md            # 快速启动指南
└── 📖 DOCKER_DEPLOYMENT.md     # 完整部署文档
```

## 🚀 快速启动

### 方式一：Docker一键部署 (推荐)

```bash
# 克隆项目
git clone <项目地址>
cd kangyang-demo

# 一键启动所有服务
./docker-deploy.sh start

# 或者分步启动
docker compose up -d
```

### 方式二：开发环境启动

```bash
# 启动基础服务
docker compose -f docker-compose.simple.yml up -d

# 启动开发环境
docker compose -f docker-compose.dev.yml up -d
```

## 🌐 访问地址

| 服务 | 地址 | 描述 |
|------|------|------|
| 🏠 管理后台 | http://localhost:3000 | 系统管理界面 |
| 📺 监控大屏 | http://localhost:3001 | 实时监控展示 |
| 🔌 后端API | http://localhost:8080 | REST API服务 |
| 🤖 AI检测 | http://localhost:5000 | AI分析服务 |
| 🗄️ MySQL | localhost:3306 | 数据库服务 |
| 💾 Redis | localhost:6379 | 缓存服务 |

## 🛠️ 技术栈

### 后端技术
- **Spring Boot 2.7** - 企业级Java框架
- **MySQL 8.0** - 关系型数据库
- **Redis 7** - 内存缓存数据库
- **WebSocket** - 实时通信

### AI算法
- **Python 3.12** - 主要开发语言 (最新优化版本)
- **OpenCV** - 计算机视觉库
- **MediaPipe** - 姿态检测
- **YOLO** - 目标检测
- **Flask** - 轻量级Web框架
- **自动化测试框架** - 完整的AI模型测试和验证

### 前端技术
- **Vue.js 3** - 渐进式前端框架
- **Element Plus** - UI组件库
- **ECharts** - 数据可视化
- **Vite** - 前端构建工具
- **Nginx** - 反向代理服务器

### 部署技术
- **Docker** - 容器化技术
- **Docker Compose** - 容器编排
- **多阶段构建** - 镜像优化
- **健康检查** - 服务监控

## 🎯 核心功能

### 🔍 AI检测算法
- **姿态分析** - 基于关键点检测的人体姿态识别
- **动作识别** - 实时监测异常动作模式
- **跌倒判断** - 多维度特征融合的跌倒事件判定
- **误报过滤** - 智能算法减少误报率

### 📊 数据管理
- **事件记录** - 完整的跌倒事件数据存储
- **统计分析** - 多维度数据统计和趋势分析
- **历史查询** - 灵活的数据检索和导出功能
- **实时监控** - WebSocket实时数据推送

### 🚨 告警系统
- **即时通知** - 跌倒事件30秒内推送告警
- **多渠道推送** - 微信、短信、邮件等多种通知方式
- **分级告警** - 根据事件严重程度自动分级
- **确认机制** - 告警确认和处理流程管理

## 📋 系统要求

### 最低配置
- **CPU**: 2核心
- **内存**: 4GB RAM
- **存储**: 10GB 可用空间
- **网络**: 稳定的网络连接

### 推荐配置
- **CPU**: 4核心以上
- **内存**: 8GB RAM以上
- **存储**: 50GB SSD存储
- **GPU**: NVIDIA GPU (可选，用于AI加速)

### 软件要求
- **Docker**: 20.10+
- **Docker Compose**: 2.0+
- **操作系统**: Linux/Windows/macOS

## 📚 文档指南

- **[📖 完整部署文档](DOCKER_DEPLOYMENT.md)** - 详细的部署和配置指南
- **[🚀 快速启动指南](QUICK_START.md)** - 5分钟快速上手
- **[⚙️ 项目配置说明](CLAUDE.md)** - 开发和配置参考
- **[🎥 AI测试完整指南](ai-detection/VIDEO_TESTING_GUIDE.md)** - 视频测试和验证框架
- **[🧪 自动化测试框架](ai-detection/test_framework.py)** - AI模型性能测试工具

## 🧪 AI测试与验证

### 🎯 自动化测试框架
项目包含完整的AI模型测试和验证框架，支持：

- **🎬 视频测试**: 支持跌倒检测、火焰检测、烟雾检测等多种场景
- **📊 性能评估**: 自动生成准确率、召回率、F1分数等关键指标
- **🌐 Web界面**: 提供直观的测试管理和结果可视化界面
- **📈 批量测试**: 支持大规模测试数据集的自动化处理
- **📋 详细报告**: 生成包含测试结果、性能指标和错误分析的完整报告

### 🚀 快速开始测试

```bash
# 进入AI检测目录
cd ai-detection

# 启动Web测试平台
python start_test_platform.py

# 或直接运行命令行测试
python test_framework.py

# 访问Web界面
open http://localhost:5558
```

### 📋 测试覆盖范围

- **基础功能测试**: 跌倒检测准确性验证
- **性能压力测试**: 多路视频流并发处理
- **鲁棒性测试**: 低光照、复杂场景等极端条件
- **误报率测试**: 正常活动的误判率控制
- **实时性测试**: 检测延迟和响应时间评估

## 🤝 贡献指南

欢迎贡献代码和提出建议！请遵循以下步骤：

1. Fork 本项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送分支 (`git push origin feature/AmazingFeature`)
5. 创建 Pull Request

## 📄 许可证

本项目基于 MIT 许可证开源 - 查看 [LICENSE](LICENSE) 文件了解详情

## 🆘 技术支持

- **GitHub Issues**: [问题反馈](https://github.com/your-repo/issues)
- **技术文档**: [在线文档](https://your-docs.com)
- **联系方式**: your-email@example.com

---

<div align="center">

**⭐ 如果这个项目对你有帮助，请给个Star支持一下！**

Made with ❤️ by 康养开发团队

</div>