# 康养跌倒检测系统 Demo

基于AI视觉算法的老年人跌倒检测与告警系统演示版本。

## 项目结构

```
├── ai-detection/          # Python AI检测服务
├── backend/              # Spring Boot后端API
├── frontend/
│   ├── admin/           # Vue管理端界面
│   └── monitor/         # 监控大屏展示
├── docker/              # Docker配置文件
└── docs/               # 文档资料
```

## 快速启动

### 1. AI检测服务
```bash
cd ai-detection
pip install -r requirements.txt
python app.py
```

### 2. 后端服务
```bash
cd backend
./mvnw spring-boot:run
```

### 3. 前端界面
```bash
# 管理端
cd frontend/admin
npm install && npm run dev

# 监控大屏
cd frontend/monitor
npm install && npm run dev
```

## 功能演示

- 实时视频流处理
- 跌倒事件检测和告警
- 事件管理和历史查询
- 监控大屏实时展示

## 系统要求

- Python 3.8+
- Java 11+
- Node.js 16+
- MySQL 8.0+