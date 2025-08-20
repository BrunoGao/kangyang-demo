# 测试视频获取和管理完整指南

## 概述

本指南提供了康养项目中跌倒检测和火焰检测算法测试视频的完整获取、管理和使用方案。

## 📁 目录结构

```
test_videos/
├── fall_detection/          # 跌倒检测视频
├── fire_detection/          # 火焰检测视频
├── smoke_detection/         # 烟雾检测视频
├── normal_scenes/           # 正常场景对照组
├── mixed_scenarios/         # 复合场景测试
├── synthetic_data/          # 合成数据
├── real_world_samples/      # 真实场景采集
└── video_index.json         # 视频索引文件
```

## 🎯 测试视频分类

### 1. 跌倒检测视频

#### 基础场景
- `elderly_bathroom_fall.mp4` - 老人卫生间跌倒 (中等难度)
- `elderly_bedroom_fall.mp4` - 老人卧室跌倒 (简单)
- `elderly_kitchen_fall.mp4` - 老人厨房跌倒 (中等难度)
- `elderly_living_room_fall.mp4` - 老人客厅跌倒 (简单)

#### 复杂场景
- `complex_movement_fall.mp4` - 复杂运动中的跌倒 (困难)
- `multiple_person_fall.mp4` - 多人场景中的跌倒 (困难)
- `low_light_fall.mp4` - 低光照条件下的跌倒 (困难)
- `elderly_walker_fall.mp4` - 使用助行器时的跌倒 (中等)

#### 误报测试
- `elderly_sitting_down.mp4` - 正常坐下动作 (简单)
- `elderly_lying_down.mp4` - 正常躺下动作 (简单)
- `elderly_picking_up.mp4` - 拾取物品动作 (中等)
- `elderly_exercise.mp4` - 康复训练动作 (中等)

### 2. 火焰检测视频

#### 不同环境
- `kitchen_fire.mp4` - 厨房火灾 (中等难度)
- `living_room_fire.mp4` - 客厅火灾 (简单)
- `bedroom_fire.mp4` - 卧室火灾 (中等)
- `electrical_fire.mp4` - 电器火灾 (困难)

#### 不同火焰类型
- `small_flame.mp4` - 小火苗 (简单)
- `large_fire.mp4` - 大火 (简单)
- `candle_flame.mp4` - 蜡烛火焰 (困难-容易误报)
- `gas_stove_flame.mp4` - 燃气灶火焰 (困难-正常使用)

### 3. 烟雾检测视频

#### 不同烟雾密度
- `light_smoke.mp4` - 轻微烟雾 (困难)
- `medium_smoke.mp4` - 中等烟雾 (中等)
- `heavy_smoke.mp4` - 浓烟 (简单)
- `cooking_smoke.mp4` - 烹饪烟雾 (困难-正常情况)

### 4. 复合场景

#### 紧急情况
- `emergency_evacuation.mp4` - 紧急疏散(跌倒+火灾) (非常困难)
- `fire_escape_fall.mp4` - 火灾逃生时跌倒 (困难)
- `smoke_confusion_fall.mp4` - 烟雾中迷失方向跌倒 (困难)

## 🔧 视频技术规格

### 推荐格式
- **容器格式**: MP4 (H.264编码)
- **分辨率**: 1920x1080 (Full HD)
- **帧率**: 30 FPS
- **码率**: 5-8 Mbps
- **音频**: AAC 128kbps (可选)

### 质量要求
- **清晰度**: 能清楚识别人物动作和火焰形状
- **光照**: 涵盖正常、低光、背光等多种条件
- **视角**: 监控摄像头常见角度(俯视、侧视)
- **时长**: 30-180秒，包含完整的事件过程

## 📥 视频获取方案

### 方案1: 开源数据集

#### 跌倒检测数据集
1. **UR Fall Detection Dataset**
   - 来源: University of Rzeszow
   - 包含70个跌倒和30个正常活动视频
   - 下载: http://fenix.ur.edu.pl/~mkepski/ds/uf.html

2. **FDD (Fall Detection Dataset)**
   - 包含多角度摄像头视频
   - 191个跌倒事件，130个日常活动
   - 适合多角度测试

3. **Multicam Fall Dataset**
   - 8个摄像头同步录制
   - 包含24个不同跌倒类型
   - 适合测试摄像头角度鲁棒性

#### 火焰检测数据集
1. **Fire and Smoke Detection Dataset**
   - 包含火焰、烟雾、正常场景
   - 视频和图像数据
   - Kaggle等平台可下载

2. **Burning Building Dataset**
   - 建筑物火灾视频
   - 多种火焰和烟雾场景
   - 适合室内环境测试

### 方案2: 合成数据生成

#### 3D渲染工具
```python
# 使用Blender Python API生成合成视频
import bpy
import numpy as np

def generate_fall_scene():
    # 创建室内场景
    # 添加人物模型
    # 模拟跌倒动作
    # 设置摄像头角度
    # 渲染视频
    pass
```

#### Unity 3D场景
- 创建康养院室内环境
- 使用角色控制器模拟老人动作
- 添加物理效果模拟跌倒
- 导出高质量测试视频

### 方案3: 实地拍摄

#### 安全拍摄原则
- 使用专业演员或志愿者
- 确保安全防护措施
- 多角度同步拍摄
- 后期处理优化

#### 拍摄清单
```markdown
□ 场景布置(卫生间、卧室、客厅、厨房)
□ 演员安全装备(护具、安全垫)
□ 多机位设置(3-4个角度)
□ 照明设备(模拟不同光照条件)
□ 火焰特效道具(安全的LED火焰)
□ 烟雾机(无害烟雾发生器)
```

## 🛠️ 视频管理工具使用

### 视频资源管理器
```bash
# 设置测试环境
python video_resource_manager.py

# 下载示例视频
from video_resource_manager import VideoResourceManager
manager = VideoResourceManager()
results = manager.download_sample_videos()

# 生成合成视频
synthetic_results = manager.generate_synthetic_videos()

# 验证视频完整性
validation = manager.validate_videos()
```

### 视频标注工具
```python
# 为视频添加标注信息
metadata = {
    'description': '老人卫生间跌倒场景',
    'expected_detections': ['fall'],
    'difficulty': 'medium',
    'duration_seconds': 45,
    'tags': ['fall', 'elderly', 'bathroom'],
    'ground_truth': {
        'fall_events': [
            {'start_time': 15.2, 'end_time': 17.8, 'severity': 'high'},
            {'start_time': 25.1, 'end_time': 26.9, 'severity': 'medium'}
        ]
    }
}

video_id = manager.register_video('bathroom_fall.mp4', metadata)
```

## 📊 测试用例设计

### 基础测试套件
```python
basic_test_cases = [
    {
        'id': 'fall_easy_001',
        'name': '简单跌倒检测',
        'video': 'elderly_bedroom_fall.mp4',
        'expected_results': {
            'detections': 1,
            'min_confidence': 0.8,
            'max_latency': 2.0
        }
    },
    {
        'id': 'fire_medium_001', 
        'name': '厨房火灾检测',
        'video': 'kitchen_fire.mp4',
        'expected_results': {
            'detections': ['fire', 'smoke'],
            'min_confidence': 0.7,
            'max_latency': 3.0
        }
    }
]
```

### 性能测试套件
```python
performance_test_cases = [
    {
        'id': 'perf_001',
        'name': '处理速度测试',
        'video': 'long_normal_scene.mp4',
        'requirements': {
            'max_processing_time': 5.0,
            'max_memory_usage': '1GB',
            'max_cpu_usage': 80
        }
    }
]
```

### 鲁棒性测试套件
```python
robustness_test_cases = [
    {
        'id': 'robust_001',
        'name': '低光照鲁棒性',
        'videos': ['low_light_fall_*.mp4'],
        'requirements': {
            'min_detection_rate': 0.7,
            'max_false_positive_rate': 0.1
        }
    }
]
```

## 🎯 质量控制标准

### 视频质量评估
1. **技术质量**
   - 分辨率清晰度 (8-10分)
   - 帧率稳定性 (8-10分)
   - 压缩质量 (7-10分)

2. **内容质量**
   - 事件清晰度 (8-10分)
   - 场景真实性 (7-10分)
   - 光照条件 (6-10分)

3. **标注质量**
   - 时间点准确性 (9-10分)
   - 分类正确性 (9-10分)
   - 元数据完整性 (8-10分)

### 测试覆盖率要求
- **场景覆盖**: 卫生间、卧室、客厅、厨房各≥5个视频
- **难度覆盖**: 简单(30%)、中等(40%)、困难(20%)、很难(10%)
- **条件覆盖**: 正常光照(60%)、低光(20%)、背光(20%)
- **时长覆盖**: 短(30s, 40%)、中(60s, 40%)、长(120s+, 20%)

## 📈 使用最佳实践

### 测试流程
1. **准备阶段**
   - 确认视频完整性
   - 验证标注数据
   - 配置测试环境

2. **执行阶段**
   - 按难度递进测试
   - 记录详细性能数据
   - 监控资源使用情况

3. **分析阶段**
   - 生成测试报告
   - 分析失败案例
   - 识别改进方向

### 存储管理
- **本地存储**: SSD推荐，≥500GB空间
- **备份策略**: 定期备份到云存储
- **版本控制**: Git LFS管理大文件
- **清理策略**: 定期清理临时文件

### 性能优化
- **批量处理**: 并行处理多个视频
- **缓存策略**: 缓存常用视频特征
- **资源监控**: 实时监控CPU/内存使用
- **负载均衡**: 分布式测试支持

## 🔒 法律和伦理考虑

### 数据隐私
- 所有真实拍摄需获得同意书
- 敏感信息需要打码处理
- 遵守GDPR等隐私法规

### 开源许可
- 明确标注数据来源和许可
- 遵守开源数据集使用条款
- 商业使用需确认授权

### 伦理审查
- 老人相关内容需伦理委员会审批
- 避免歧视性或偏见性内容
- 确保测试数据的多样性和包容性

## 🚀 快速开始

### 1. 环境设置
```bash
# 安装依赖
pip install -r requirements.txt

# 创建视频目录
mkdir -p test_videos/{fall_detection,fire_detection,smoke_detection}

# 初始化视频管理器
python video_resource_manager.py
```

### 2. 下载基础数据集
```python
from video_resource_manager import VideoResourceManager

manager = VideoResourceManager()
# 下载示例视频(如果可用)
results = manager.download_sample_videos()
# 生成合成测试数据
synthetic = manager.generate_synthetic_videos()
```

### 3. 运行基础测试
```python
from test_framework import quick_test

# 快速测试
result = quick_test(test_type='fall', difficulty='easy')
print(f"通过率: {result['report']['summary']['pass_rate']:.1%}")
```

### 4. Web界面测试
```bash
# 启动Web界面
python test_framework_web.py

# 浏览器访问
open http://localhost:5558
```

## 📞 支持和反馈

遇到问题或需要帮助时:

1. 检查日志文件: `test_framework.log`
2. 验证视频文件完整性
3. 确认依赖环境正确安装
4. 查看GitHub Issues获取最新解决方案

---

**注意**: 本指南将随着项目发展持续更新，请定期查看最新版本。