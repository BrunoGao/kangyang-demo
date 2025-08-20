# 康养跌倒检测系统Demo使用指南

## 系统概述

本演示系统基于AI视觉算法实现老年人跌倒检测与告警，包含以下核心功能：

- 🤖 **实时跌倒检测**: 基于MediaPipe姿态估计的跌倒算法
- 🚨 **智能告警系统**: 即时告警推送和分级处理机制  
- 📊 **管理后台**: 事件管理、统计分析、系统配置
- 📺 **监控大屏**: 实时状态展示、可视化数据面板

## 快速启动

### 方式一：一键启动（推荐）
```bash
./start-demo.sh
```

### 方式二：手动启动
```bash
# 1. 启动基础服务
docker-compose up -d mysql redis

# 2. 启动AI检测服务
cd ai-detection
pip install -r requirements.txt
python app.py

# 3. 启动后端服务（新终端）
cd backend
./mvnw spring-boot:run

# 4. 启动管理界面（新终端）
cd frontend/admin
npm install && npm run dev

# 5. 启动监控大屏（新终端）
cd frontend/monitor
npm install && npm run dev
```

## 访问地址

| 服务 | 地址 | 说明 |
|------|------|------|
| 管理系统 | http://localhost:3000 | 事件管理、数据统计 |
| 监控大屏 | http://localhost:3001 | 实时监控展示 |
| AI检测API | http://localhost:5000 | 跌倒检测服务 |
| 后端API | http://localhost:8080 | RESTful接口 |

## 功能演示

### 1. 跌倒检测算法测试

```bash
cd ai-detection
python fall_detector.py
```

- 使用摄像头进行实时检测
- 显示人体关键点和倾斜角度
- 实时跌倒状态判断
- 按 'q' 退出测试

### 2. 管理后台功能

**仪表盘 (Dashboard)**
- 实时统计数据展示
- 告警趋势图表
- 最近事件列表
- 一键处理告警

**事件管理 (Events)**
- 分页查询历史告警
- 多条件筛选（状态、严重程度、时间范围）
- 批量处理功能
- 事件详情查看

**摄像头管理 (Cameras)**
- 设备状态监控
- 配置管理
- 在线状态检测

### 3. 监控大屏展示

**实时统计面板**
- 今日告警数量
- 待处理事件
- 系统状态监控
- 设备在线情况

**可视化图表**
- 告警趋势曲线
- 严重程度分布
- 实时数据更新

**告警推送**
- 全屏弹窗告警
- 声音提示（可配置）
- 自动刷新机制

## API接口文档

### 跌倒检测API

```bash
# 健康检查
GET http://localhost:5000/api/health

# 处理单帧图像
POST http://localhost:5000/api/process_frame
Content-Type: application/json
{
  "image": "data:image/jpeg;base64,...",
  "camera_id": "camera_1"
}

# 获取告警历史
GET http://localhost:5000/api/alerts?page=1&size=20
```

### 后端管理API

```bash
# 获取事件统计
GET http://localhost:8080/api/events/statistics

# 查询事件列表
GET http://localhost:8080/api/events?page=0&size=20

# 处理事件
PUT http://localhost:8080/api/events/{id}/handle?handler=管理员&remarks=已处理
```

## 算法参数调优

**跌倒检测阈值**
```python
# ai-detection/fall_detector.py
self.fall_threshold = 0.7  # 跌倒角度阈值
self.lying_time_threshold = 5.0  # 躺倒时间阈值
```

**告警频率控制**
```python
# 连续帧确认（减少误报）
if state['consecutive_fall_frames'] > 5:
    # 确认跌倒

# 持续告警间隔
if current_time - state['last_alert_time'] > 30:
    # 发送告警
```

## 数据库结构

**fall_events表**
- id: 主键
- person_id: 人员标识
- camera_id: 摄像头ID
- event_type: 事件类型
- severity: 严重程度
- body_angle: 身体角度
- duration: 持续时间
- location: 位置信息
- is_handled: 处理状态
- created_time: 发生时间

**cameras表**
- id: 主键
- camera_id: 摄像头标识
- camera_name: 设备名称
- location: 安装位置
- rtsp_url: 视频流地址
- status: 设备状态

## 故障排除

### 常见问题

1. **摄像头无法打开**
   - 检查设备权限
   - 确认摄像头未被其他应用占用
   - 尝试更换设备索引（0, 1, 2...）

2. **AI检测服务启动失败**
   - 检查Python依赖安装
   - 确认OpenCV正确安装
   - 查看错误日志：`tail -f ai-detection/ai-detection.log`

3. **后端服务连接失败**
   - 检查MySQL/Redis是否正常启动
   - 确认端口未被占用
   - 查看日志：`tail -f backend/backend.log`

4. **前端页面无法访问**
   - 检查Node.js版本（建议16+）
   - 重新安装依赖：`rm -rf node_modules && npm install`
   - 检查端口占用情况

### 性能优化

1. **降低CPU使用率**
   - 减少视频帧率
   - 降低图像分辨率
   - 使用GPU加速（需要CUDA环境）

2. **提高检测精度**
   - 收集更多训练数据
   - 调整检测阈值
   - 增加多角度摄像头

3. **系统稳定性**
   - 增加异常处理
   - 添加自动重启机制
   - 监控系统资源使用

## 停止服务

```bash
./stop-demo.sh
```

## 技术支持

如遇到问题，请检查：
1. 系统要求是否满足
2. 依赖软件是否正确安装
3. 端口是否被占用
4. 日志文件中的错误信息

更多技术细节请参考项目根目录下的 `CLAUDE.md` 文件。