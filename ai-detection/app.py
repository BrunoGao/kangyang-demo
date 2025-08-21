from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
import cv2
import numpy as np
import base64
import json
import os
import redis
from fall_detector import FallDetector
import threading
import time
from datetime import datetime

app = Flask(__name__)
app.config['SECRET_KEY'] = 'kangyang-fall-detection'
socketio = SocketIO(app, cors_allowed_origins="*")

# 全局变量
detector = FallDetector()
redis_client = None

try:
    redis_host = os.getenv('REDIS_HOST', 'localhost')
    redis_port = int(os.getenv('REDIS_PORT', '6379'))
    redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
    redis_client.ping()
    print("Redis连接成功")
except:
    print("Redis连接失败，使用内存存储")

def redis_listener():
    """监听Redis告警消息"""
    if not redis_client:
        return
    
    pubsub = redis_client.pubsub()
    pubsub.subscribe('fall_alerts')
    
    for message in pubsub.listen():
        if message['type'] == 'message':
            try:
                alert_data = json.loads(message['data'])
                # 通过WebSocket广播告警
                socketio.emit('fall_alert', alert_data)
            except Exception as e:
                print(f"处理告警消息失败: {e}")

# 启动Redis监听线程
if redis_client:
    listener_thread = threading.Thread(target=redis_listener, daemon=True)
    listener_thread.start()

@app.route('/api/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'AI Fall Detection',
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/process_frame', methods=['POST'])
def process_frame():
    """处理单帧图像"""
    try:
        data = request.json
        if 'image' not in data:
            return jsonify({'error': '缺少图像数据'}), 400
        
        # 解码base64图像
        image_data = base64.b64decode(data['image'].split(',')[1])
        nparr = np.frombuffer(image_data, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        # 处理图像
        processed_frame, detections = detector.process_frame(frame, data.get('camera_id', 'camera_1'))
        
        # 编码处理后的图像
        _, buffer = cv2.imencode('.jpg', processed_frame)
        processed_image = base64.b64encode(buffer).decode('utf-8')
        
        return jsonify({
            'processed_image': f"data:image/jpeg;base64,{processed_image}",
            'detections': detections,
            'timestamp': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/alerts', methods=['GET'])
def get_alerts():
    """获取告警历史"""
    try:
        page = int(request.args.get('page', 1))
        size = int(request.args.get('size', 20))
        
        alerts = []
        if redis_client:
            start = (page - 1) * size
            end = start + size - 1
            alert_data = redis_client.lrange('fall_events', start, end)
            alerts = [json.loads(alert) for alert in alert_data]
        
        return jsonify({
            'alerts': alerts,
            'page': page,
            'size': size,
            'total': redis_client.llen('fall_events') if redis_client else 0
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/statistics', methods=['GET'])
def get_statistics():
    """获取统计数据"""
    try:
        today_alerts = 0
        total_alerts = 0
        
        if redis_client:
            total_alerts = redis_client.llen('fall_events')
            # 简化统计，实际应该按日期过滤
            today_alerts = min(total_alerts, 10)  # 模拟今日告警数
        
        return jsonify({
            'today_alerts': today_alerts,
            'total_alerts': total_alerts,
            'active_cameras': 1,  # 演示数据
            'system_status': 'online',
            'last_update': datetime.now().isoformat()
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@socketio.on('connect')
def handle_connect():
    """WebSocket连接"""
    print('客户端已连接')
    emit('status', {'message': 'AI检测服务已连接'})

@socketio.on('disconnect')
def handle_disconnect():
    """WebSocket断开"""
    print('客户端已断开')

@socketio.on('start_detection')
def handle_start_detection(data):
    """开始检测"""
    camera_id = data.get('camera_id', 'camera_1')
    emit('detection_started', {'camera_id': camera_id})

@socketio.on('stop_detection')
def handle_stop_detection(data):
    """停止检测"""
    camera_id = data.get('camera_id', 'camera_1')
    emit('detection_stopped', {'camera_id': camera_id})

# 模拟实时数据推送
def send_mock_data():
    """发送模拟数据"""
    while True:
        try:
            stats = {
                'timestamp': datetime.now().isoformat(),
                'active_cameras': 1,
                'total_detections': np.random.randint(0, 100),
                'system_load': round(np.random.uniform(0.1, 0.8), 2)
            }
            socketio.emit('system_stats', stats)
            time.sleep(5)
        except:
            break

# 启动模拟数据线程
mock_thread = threading.Thread(target=send_mock_data, daemon=True)
mock_thread.start()

if __name__ == '__main__':
    print("启动AI跌倒检测服务...")
    print("API地址: http://localhost:5000")
    print("WebSocket地址: ws://localhost:5000")
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)