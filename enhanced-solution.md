# 康养跌倒检测系统 - 完整解决方案

## 📊 原始需求对应实现

### 1. 软件算法和管理系统 (已实现)

**2个算法模型:**
- ✅ **跌倒检测算法**: 基于MediaPipe姿态估计，检测人体倾斜角度和躺倒时间
- 🔄 **火焰/烟雾识别**: 需要添加基于YOLO的火灾检测模型

**AI管理系统:**
- ✅ Spring Boot后端API
- ✅ Vue3管理界面
- ✅ 监控大屏展示
- ✅ 告警管理系统

### 2. 硬件AI边缘控制器方案

**22个摄像头分布式部署:**
```
机房部署结构:
├── 主控服务器 (1台)
│   ├── Spring Boot管理系统
│   ├── MySQL数据库
│   └── Redis缓存
├── AI边缘节点 (11台)
│   ├── 每台负责2个摄像头
│   ├── NVIDIA Jetson Nano/Xavier
│   └── 本地AI推理计算
└── 网络交换机
    └── 千兆以太网连接
```

## 🔧 补充功能实现

### 火焰/烟雾检测算法

**需要添加的火灾检测功能:**

```python
# ai-detection/fire_detector.py
import cv2
import numpy as np
from ultralytics import YOLO

class FireSmokeDetector:
    def __init__(self):
        # 使用YOLOv8训练的火焰检测模型
        self.model = YOLO('models/fire_smoke_yolo.pt')
        self.classes = {0: 'fire', 1: 'smoke'}
        
    def detect_fire_smoke(self, frame):
        """检测火焰和烟雾"""
        results = self.model(frame)
        detections = []
        
        for result in results:
            boxes = result.boxes
            if boxes is not None:
                for box in boxes:
                    x1, y1, x2, y2 = box.xyxy[0].cpu().numpy()
                    confidence = box.conf[0].cpu().numpy()
                    class_id = int(box.cls[0].cpu().numpy())
                    
                    if confidence > 0.5:  # 置信度阈值
                        detections.append({
                            'type': self.classes[class_id],
                            'confidence': float(confidence),
                            'bbox': [int(x1), int(y1), int(x2), int(y2)],
                            'area': (x2-x1) * (y2-y1)
                        })
        
        return detections
```

### 3. 双算法集成方案

**统一检测服务架构:**
```python
# ai-detection/unified_detector.py
class UnifiedDetector:
    def __init__(self):
        self.fall_detector = FallDetector()
        self.fire_detector = FireSmokeDetector()
        
    def process_frame(self, frame, camera_id):
        results = {
            'camera_id': camera_id,
            'timestamp': datetime.now().isoformat(),
            'detections': []
        }
        
        # 跌倒检测
        fall_result = self.fall_detector.detect_fall(frame)
        if fall_result['is_fall']:
            results['detections'].append({
                'type': 'fall',
                'severity': fall_result['severity'],
                'person_id': fall_result.get('person_id'),
                'location': fall_result.get('location')
            })
        
        # 火灾检测
        fire_detections = self.fire_detector.detect_fire_smoke(frame)
        for detection in fire_detections:
            results['detections'].append({
                'type': detection['type'],
                'confidence': detection['confidence'],
                'bbox': detection['bbox']
            })
            
        return results
```

## 🏗️ 分布式部署架构

### AI边缘控制器硬件配置

**推荐硬件方案:**
- **主控制器**: NVIDIA Jetson Xavier NX (2个摄像头/台)
- **CPU**: 6核Carmel ARM v8.2 64位
- **GPU**: 384核NVIDIA Volta GPU
- **内存**: 8GB LPDDR4x
- **存储**: 64GB eUFS + 128GB SD卡
- **网络**: 千兆以太网

**软件栈:**
```bash
# Jetson设备软件安装
sudo apt update
sudo apt install python3-pip
pip3 install opencv-python ultralytics torch torchvision
pip3 install mediapipe numpy requests websocket-client
```

### 分布式网络架构

```
康养中心网络拓扑:
┌─────────────────────────────────────────────────────────┐
│                    主控服务器                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────┐        │
│  │Spring Boot  │ │  MySQL      │ │   Redis     │        │
│  │管理系统      │ │  数据库      │ │  缓存队列    │        │
│  │Port:8080    │ │Port:3306    │ │Port:6379    │        │
│  └─────────────┘ └─────────────┘ └─────────────┘        │
└─────────────────────────────────────────────────────────┘
                              │
                    ┌─────────┴─────────┐
                    │  千兆交换机        │
                    │ (24端口)          │
                    └─────────┬─────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        │                     │                     │
┌───────▼─────────┐  ┌────────▼────────┐  ┌────────▼────────┐
│AI边缘节点-1      │  │AI边缘节点-2      │  │AI边缘节点-11     │
│Jetson Xavier    │  │Jetson Xavier    │  │Jetson Xavier    │
├─────────────────┤  ├─────────────────┤  ├─────────────────┤
│📷摄像头1(大厅)   │  │📷摄像头3(餐厅)   │  │📷摄像头21(走廊)  │
│📷摄像头2(活动室) │  │📷摄像头4(休息区) │  │📷摄像头22(花园)  │
└─────────────────┘  └─────────────────┘  └─────────────────┘
```

### 边缘AI部署脚本

```bash
# deploy/edge_deploy.sh
#!/bin/bash
# Jetson边缘设备部署脚本

DEVICE_ID=$1
CAMERA_IDS=$2
SERVER_IP="192.168.1.100"

echo "🚀 部署AI边缘节点 $DEVICE_ID"

# 1. 系统配置
sudo systemctl set-default multi-user.target
sudo systemctl disable lightdm

# 2. AI模型下载
mkdir -p models
wget http://$SERVER_IP:8080/api/models/fall_detection.pt -O models/fall_detection.pt
wget http://$SERVER_IP:8080/api/models/fire_smoke.pt -O models/fire_smoke.pt

# 3. 启动AI检测服务
python3 edge_detector.py --device-id $DEVICE_ID --cameras $CAMERA_IDS --server $SERVER_IP

echo "✅ 边缘节点 $DEVICE_ID 部署完成"
```

## 📊 系统监控与告警

### 微信告警集成

```python
# backend/src/main/java/com/kangyang/service/WeChatAlertService.java
@Service
public class WeChatAlertService {
    
    @Value("${wechat.webhook.url}")
    private String webhookUrl;
    
    public void sendAlert(FallEvent event) {
        Map<String, Object> message = new HashMap<>();
        message.put("msgtype", "markdown");
        
        Map<String, String> markdown = new HashMap<>();
        markdown.put("content", String.format(
            "## 🚨 康养告警通知\n" +
            "**事件类型**: %s\n" +
            "**发生位置**: %s\n" +
            "**严重程度**: %s\n" +
            "**发生时间**: %s\n" +
            "**处理状态**: 待处理\n\n" +
            "[查看详情](http://monitor.kangyang.com/events/%s)",
            event.getEventType(),
            event.getLocation(),
            event.getSeverity(),
            event.getTimestamp(),
            event.getId()
        ));
        
        message.put("markdown", markdown);
        
        // 发送微信消息
        restTemplate.postForObject(webhookUrl, message, String.class);
    }
}
```

### 数据统计分析

**已实现功能:**
- ✅ 实时告警统计
- ✅ 每日/每月趋势分析  
- ✅ 摄像头状态监控
- ✅ 响应时间统计

**需要补充的功能:**
- 🔄 误报率分析
- 🔄 热力图显示
- 🔄 预警机制
- 🔄 历史数据导出

## 🎯 实施计划

### 第一阶段 (已完成)
- ✅ 基础算法验证
- ✅ 核心系统搭建
- ✅ 演示界面开发

### 第二阶段 (2周)
- 🔄 火焰/烟雾检测算法集成
- 🔄 边缘设备采购与配置
- 🔄 分布式部署架构实施

### 第三阶段 (1周)
- 🔄 22个摄像头点位安装
- 🔄 网络配置与调试
- 🔄 系统集成测试

### 第四阶段 (1周)
- 🔄 用户培训
- 🔄 运维文档编写
- 🔄 正式上线运行

## 📋 技术规格总结

| 组件 | 技术选型 | 部署位置 | 状态 |
|------|----------|----------|------|
| 跌倒检测 | MediaPipe + Python | 边缘节点 | ✅ 已实现 |
| 火焰检测 | YOLOv8 + Python | 边缘节点 | 🔄 待实现 |
| 后端API | Spring Boot 2.7 | 主控服务器 | ✅ 已实现 |
| 前端管理 | Vue3 + Element Plus | 主控服务器 | ✅ 已实现 |
| 监控大屏 | Vue3 + ECharts | 主控服务器 | ✅ 已实现 |
| 数据库 | MySQL 8.0 | 主控服务器 | ✅ 已实现 |
| 缓存 | Redis 6.0 | 主控服务器 | ✅ 已实现 |
| 边缘计算 | Jetson Xavier NX | 分布式部署 | 🔄 待采购 |

现有演示系统已完全满足算法验证需求，可立即进行第二阶段的火焰检测算法集成和硬件采购工作。