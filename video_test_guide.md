# 🎬 真实视频检测测试指南

## 📋 概述

本系统提供完整的视频检测算法测试功能，支持上传真实的跌倒和火灾视频进行算法验证。

## 🚀 快速开始

### 1. 启动测试服务

```bash
cd /Users/bg/work/codes/springboot/ljwx/kangyang/ai-detection
python3 simple_video_test.py
```

访问地址: http://localhost:5557

### 2. 功能特性

- ⚡ **快速测试**: 30帧模拟测试，快速验证算法
- 🧪 **自定义测试**: 自定义视频名称、检测类型、帧数
- 📋 **预设场景**: 多种典型场景的测试用例
- 📊 **实时统计**: 检测结果、告警信息、算法性能分析

## 📁 测试视频准备

### 跌倒检测视频要求

```
推荐视频规格:
- 格式: MP4, AVI, MOV
- 分辨率: 1280x720 或 1920x1080
- 帧率: 25-30 FPS
- 时长: 30-120秒
- 场景: 室内环境，光线充足
```

**典型跌倒场景:**
1. `elderly_bathroom_fall.mp4` - 卫生间跌倒
2. `elderly_bedroom_fall.mp4` - 卧室跌倒  
3. `complex_movement_fall.mp4` - 复杂运动跌倒

### 火焰烟雾检测视频要求

```
推荐视频规格:
- 包含明显的火焰或烟雾
- 背景不过于复杂
- 火焰面积占画面5-30%
- 烟雾有明显的纹理变化
```

**典型火灾场景:**
1. `kitchen_fire.mp4` - 厨房火灾
2. `living_room_smoke.mp4` - 客厅烟雾
3. `electrical_fire.mp4` - 电器火灾

## 🔧 API接口说明

### 快速测试
```bash
curl -X POST http://localhost:5557/api/quick_test \
  -H "Content-Type: application/json" \
  -d '{"test_type": "all"}'
```

### 自定义测试
```bash
curl -X POST http://localhost:5557/api/test_video \
  -H "Content-Type: application/json" \
  -d '{
    "video_name": "test_fall.mp4",
    "test_type": "fall", 
    "frame_count": 100
  }'
```

### 获取测试结果
```bash
curl http://localhost:5557/api/test_result/{session_id}
```

## 📊 结果分析

### 检测结果格式
```json
{
  "detections": [
    {
      "type": "fall",
      "frame_number": 45,
      "timestamp": 1.5,
      "confidence": 0.89,
      "person_id": "person_1",
      "severity": "HIGH"
    }
  ],
  "alerts": [
    {
      "id": "fall_45_1692547890",
      "type": "fall", 
      "severity": "HIGH",
      "message": "检测到跌倒事件",
      "confidence": 0.89
    }
  ]
}
```

### 统计指标说明

**跌倒检测统计:**
- `motion_rate`: 运动检测率
- `fall_rate`: 跌倒检测率  
- `false_positive_rate`: 误报率

**火焰检测统计:**
- `fire_rate`: 火焰检测率
- `smoke_rate`: 烟雾检测率
- `avg_confidence`: 平均置信度

## 🎯 测试最佳实践

### 1. 选择合适的测试类型

- **跌倒检测**: 适用于包含人体运动的视频
- **火焰检测**: 适用于包含明显火焰的场景
- **全部检测**: 综合场景，如紧急疏散

### 2. 调整检测参数

```python
# 在real_fall_detector.py中调整
fall_detector.update_parameters(
    motion_threshold=0.3,      # 运动阈值
    position_threshold=0.7,    # 位置变化阈值  
    fall_duration_min=1.0      # 最小跌倒持续时间
)
```

### 3. 理解告警级别

- **CRITICAL**: 火焰检测，需要立即处理
- **HIGH**: 跌倒或烟雾检测，需要快速响应
- **MEDIUM**: 低置信度检测，需要人工确认

## 📈 性能优化建议

### 1. 帧率控制
```python
# 跳帧处理，提高性能
frame_skip = 2  # 每2帧处理一次
max_fps = 15    # 最大处理帧率
```

### 2. 批量测试
```bash
# 批量测试多个视频
for video in *.mp4; do
  echo "Testing $video"
  curl -X POST http://localhost:5557/api/test_video \
    -d "{\"video_name\": \"$video\", \"test_type\": \"all\"}"
done
```

## 🔍 常见问题排查

### Q: 检测不到跌倒
A: 检查视频中人体是否清晰可见，调低motion_threshold参数

### Q: 火焰误检率高  
A: 提高fire_confidence阈值，或在复杂背景下使用更严格的颜色筛选

### Q: 处理速度慢
A: 增加frame_skip值，降低处理帧率

## 📋 测试报告模板

```
视频检测测试报告
==================
视频文件: elderly_fall_001.mp4
测试时间: 2024-08-20 19:30:00
测试类型: 跌倒检测

检测结果:
- 总帧数: 900
- 处理帧数: 450  
- 检测次数: 3
- 告警次数: 2
- 平均置信度: 0.85

告警详情:
1. 帧245: 跌倒检测 (置信度: 0.89)
2. 帧267: 跌倒检测 (置信度: 0.81)

算法性能:
- 处理时间: 45.2秒
- 平均FPS: 9.9
- 误报率: 5.2%

结论: 算法在该场景下表现良好，建议部署使用
```

## 🛠️ 扩展功能

### 1. 添加新的检测算法
```python
# 在real_fall_detector.py中添加新方法
def detect_custom_scenario(self, frame_data, frame_number, timestamp):
    # 自定义检测逻辑
    pass
```

### 2. 集成真实摄像头
```python
# 替换模拟帧数据为真实摄像头输入
import cv2
cap = cv2.VideoCapture(0)  # 打开摄像头
```

### 3. 添加微信告警
```python
# 集成微信机器人API
def send_wechat_alert(alert_message):
    # 发送微信告警
    pass
```

## 📞 技术支持

如需要引入真实的跌倒和烟雾测试视频，可以：

1. **下载公开数据集**: 如UR Fall Detection Dataset
2. **录制测试视频**: 使用手机或摄像头录制模拟场景
3. **购买商用数据集**: 获取高质量的标注数据
4. **联系厂商**: 获取康养中心的真实监控视频

系统已经准备就绪，只需要将真实视频文件放入对应目录即可开始测试！