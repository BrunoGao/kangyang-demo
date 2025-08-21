from flask import Flask, request, jsonify
import json
import random
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kangyang-fall-detection'

# 全局统计数据
global_stats = {
    'total_frames': 0,
    'fall_alerts': 0,
    'fire_alerts': 0,
    'smoke_alerts': 0,
    'last_reset': datetime.now().isoformat()
}

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Unified Detection (Demo Mode)',
        'features': ['fall_detection', 'fire_detection', 'smoke_detection'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    """处理单帧图像 - 统一检测模拟版本"""
    try:
        data = request.json
        if 'image' not in data:
            return jsonify({'error': '缺少图像数据'}), 400
        
        camera_id = data.get('camera_id', 'camera_1')
        enable_fall = data.get('enable_fall', True)
        enable_fire = data.get('enable_fire', True)
        
        global_stats['total_frames'] += 1
        
        detections = []
        alerts = []
        
        # 模拟跌倒检测
        if enable_fall and random.random() < 0.08:  # 8%概率模拟跌倒
            fall_detection = {
                'type': 'fall',
                'confidence': round(random.uniform(0.75, 0.95), 2),
                'severity': 'HIGH',
                'person_id': f'person_{random.randint(1, 3)}',
                'body_angle': round(random.uniform(0.8, 1.4), 2),
                'duration': round(random.uniform(0, 30), 1),
                'location': [random.randint(100, 500), random.randint(100, 400)],
                'timestamp': datetime.now().isoformat()
            }
            detections.append(fall_detection)
            
            if fall_detection['confidence'] > 0.8:
                alerts.append({
                    'id': f"fall_{int(time.time() * 1000)}",
                    'type': 'fall',
                    'severity': 'HIGH',
                    'message': f"检测到跌倒事件，置信度: {fall_detection['confidence']:.2f}",
                    'timestamp': fall_detection['timestamp']
                })
                global_stats['fall_alerts'] += 1
        
        # 模拟火焰检测
        if enable_fire and random.random() < 0.05:  # 5%概率模拟火焰
            fire_detection = {
                'type': 'fire',
                'confidence': round(random.uniform(0.6, 0.9), 2),
                'bbox': [
                    random.randint(50, 200),
                    random.randint(50, 200),
                    random.randint(250, 400),
                    random.randint(250, 400)
                ],
                'area': random.randint(1000, 5000),
                'center': [random.randint(100, 500), random.randint(100, 400)],
                'timestamp': datetime.now().isoformat()
            }
            detections.append(fire_detection)
            
            if fire_detection['confidence'] > 0.7:
                alerts.append({
                    'id': f"fire_{int(time.time() * 1000)}",
                    'type': 'fire',
                    'severity': 'CRITICAL',
                    'message': f"检测到火焰，置信度: {fire_detection['confidence']:.2f}",
                    'timestamp': fire_detection['timestamp']
                })
                global_stats['fire_alerts'] += 1
        
        # 模拟烟雾检测
        if enable_fire and random.random() < 0.03:  # 3%概率模拟烟雾
            smoke_detection = {
                'type': 'smoke',
                'confidence': round(random.uniform(0.5, 0.8), 2),
                'bbox': [
                    random.randint(0, 100),
                    random.randint(0, 100),
                    random.randint(400, 600),
                    random.randint(300, 500)
                ],
                'area': random.randint(5000, 15000),
                'center': [random.randint(100, 500), random.randint(100, 400)],
                'timestamp': datetime.now().isoformat()
            }
            detections.append(smoke_detection)
            
            if smoke_detection['confidence'] > 0.6:
                alerts.append({
                    'id': f"smoke_{int(time.time() * 1000)}",
                    'type': 'smoke',
                    'severity': 'HIGH',
                    'message': f"检测到烟雾，置信度: {smoke_detection['confidence']:.2f}",
                    'timestamp': smoke_detection['timestamp']
                })
                global_stats['smoke_alerts'] += 1
        
        return jsonify({
            'camera_id': camera_id,
            'timestamp': datetime.now().isoformat(),
            'detections': detections,
            'alerts': alerts,
            'processing_time': round(random.uniform(0.1, 0.3), 3)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """获取告警历史 - 模拟数据"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        alert_type = request.args.get('type', 'all')  # all, fall, fire, smoke
        
        # 模拟告警数据
        alerts = []
        alert_types = ['fall', 'fire', 'smoke']
        
        for i in range(min(size, 10)):
            if alert_type == 'all':
                selected_type = random.choice(alert_types)
            else:
                selected_type = alert_type if alert_type in alert_types else 'fall'
            
            # 根据类型生成不同的告警数据
            if selected_type == 'fall':
                alert = {
                    'id': f'fall_{i + 1}',
                    'type': 'fall',
                    'person_id': f'person_{random.randint(1, 3)}',
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'HIGH' if random.random() < 0.7 else 'CRITICAL',
                    'location': f'20{random.randint(1, 3)}房间',
                    'body_angle': round(random.uniform(0.8, 1.4), 2),
                    'duration': round(random.uniform(0, 120), 1),
                    'confidence': round(random.uniform(0.75, 0.95), 2)
                }
            elif selected_type == 'fire':
                alert = {
                    'id': f'fire_{i + 1}',
                    'type': 'fire',
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'CRITICAL',
                    'location': f'20{random.randint(1, 3)}房间',
                    'confidence': round(random.uniform(0.6, 0.9), 2),
                    'area': random.randint(1000, 5000),
                    'temperature': random.randint(45, 80)
                }
            else:  # smoke
                alert = {
                    'id': f'smoke_{i + 1}',
                    'type': 'smoke',
                    'timestamp': datetime.now().isoformat(),
                    'severity': 'HIGH',
                    'location': f'20{random.randint(1, 3)}房间',
                    'confidence': round(random.uniform(0.5, 0.8), 2),
                    'area': random.randint(5000, 15000),
                    'density': round(random.uniform(0.3, 0.8), 2)
                }
            
            alerts.append(alert)
        
        return jsonify({
            'alerts': alerts,
            'page': page,
            'size': size,
            'total': 186,  # 模拟总数（包含火焰和烟雾告警）
            'filter': alert_type
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计数据 - 包含火焰检测统计"""
    try:
        # 基于全局统计数据生成
        today_fall = random.randint(5, 12)
        today_fire = random.randint(1, 3)
        today_smoke = random.randint(2, 5)
        
        return jsonify({
            'today_alerts': today_fall + today_fire + today_smoke,
            'today_fall_alerts': today_fall,
            'today_fire_alerts': today_fire,
            'today_smoke_alerts': today_smoke,
            'total_alerts': global_stats['fall_alerts'] + global_stats['fire_alerts'] + global_stats['smoke_alerts'] + 180,
            'total_fall_alerts': global_stats['fall_alerts'] + 120,
            'total_fire_alerts': global_stats['fire_alerts'] + 15,
            'total_smoke_alerts': global_stats['smoke_alerts'] + 45,
            'total_frames_processed': global_stats['total_frames'] + random.randint(1000, 5000),
            'active_cameras': 1,
            'detection_methods': ['MediaPipe_Fall', 'Traditional_Fire', 'Traditional_Smoke'],
            'system_status': 'online',
            'last_update': datetime.now().isoformat(),
            'alert_rate': round((today_fall + today_fire + today_smoke) / 100, 3)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/fire_statistics', methods=['GET'])
def get_fire_statistics():
    """获取火焰检测专项统计"""
    try:
        return jsonify({
            'fire_detection_enabled': True,
            'fire_model_type': 'Traditional + YOLO (未加载)',
            'fire_alerts_today': random.randint(1, 3),
            'smoke_alerts_today': random.randint(2, 5),
            'false_positive_rate': round(random.uniform(0.02, 0.08), 3),
            'average_detection_time': round(random.uniform(0.15, 0.35), 3),
            'confidence_threshold': {
                'fire': 0.6,
                'smoke': 0.5
            },
            'last_fire_alert': datetime.now().isoformat(),
            'system_temperature': random.randint(25, 35)
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

# 模拟跌倒事件生成
def generate_fall_event():
    """生成模拟跌倒事件"""
    event = {
        'id': int(time.time()),
        'type': 'fall_detected',
        'person_id': f'person_{random.randint(1, 3)}',
        'camera_id': 'camera_1',
        'severity': 'immediate',
        'location': f'20{random.randint(1, 3)}房间',
        'timestamp': datetime.now().isoformat(),
        'body_angle': round(random.uniform(0.8, 1.4), 2),
        'duration': round(random.uniform(0, 30), 1)
    }
    print(f"🚨 模拟跌倒事件: {event}")
    return event

@app.route('/health', methods=['GET'])
def health_simple():
    """简单健康检查"""
    return jsonify({'status': 'ok'})

if __name__ == '__main__':
    print("🚀 启动AI统一检测服务 (演示模式)...")
    print("📍 API地址: http://localhost:5555")
    print("🔥 支持功能: 跌倒检测 + 火焰检测 + 烟雾检测")
    print("⚠️  注意: 当前运行在演示模式，使用模拟数据")
    print("\n📊 API接口:")
    print("  - GET  /health - 健康检查")
    print("  - GET  /api/health - 健康检查")
    print("  - POST /api/process_frame - 图像检测")
    print("  - GET  /api/alerts - 告警历史")
    print("  - GET  /api/statistics - 统计数据")
    print("  - GET  /api/fire_statistics - 火焰检测统计")
    print("\n✅ 服务启动成功!")
    app.run(host='0.0.0.0', port=5555, debug=False)