from flask import Flask, request, jsonify, send_file, render_template_string
from flask_cors import CORS
import json
import random
import time
import os
import tempfile
from datetime import datetime
from werkzeug.utils import secure_filename

app = Flask(__name__)
# 配置CORS以允许从前端系统访问
CORS(app, origins=['*'], 
     allow_headers=['Content-Type', 'Authorization'], 
     methods=['GET', 'POST', 'OPTIONS'])
app.config['SECRET_KEY'] = 'kangyang-fall-detection-demo'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB max file size

# 支持的视频格式
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/test', methods=['GET'])
def test():
    """测试页面"""
    with open('test.html', 'r', encoding='utf-8') as f:
        return f.read()

@app.route('/', methods=['GET'])
def index():
    """首页 - 跌倒检测专业测试平台"""
    with open('fall_detection_professional_test.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    # 修改API地址为相对路径，因为现在同在一个服务器
    html_content = html_content.replace('http://localhost:6000', '')
    html_content = html_content.replace("const apiBase = '';", "const apiBase = window.location.origin;")
    # 简单直接的修复 - 隐藏加载层
    html_content = html_content.replace(
        '<div id="loadingOverlay" class="loading-overlay hidden">',
        '<div id="loadingOverlay" class="loading-overlay hidden" style="display: none !important;">'
    )
    return html_content

@app.route('/health', methods=['GET'])
def health_check():
    """健康检查"""
    return jsonify({
        'status': 'healthy',
        'service': 'Fall Detection Demo API',
        'version': '2.0.0',
        'features': ['video_upload', 'fall_detection', 'real_time_analysis'],
        'timestamp': datetime.now().isoformat()
    })

@app.route('/api/video/info', methods=['GET'])
def get_default_video_info():
    """获取默认测试视频信息"""
    try:
        # 模拟默认视频信息
        return jsonify({
            'filename': 'falldown.mp4',
            'file_size_mb': 85.5,
            'resolution': '1920x1080',
            'duration_seconds': 45.2,
            'fps': 30.0,
            'total_frames': 1356,
            'video_type': 'default'
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/video/upload', methods=['POST'])
def upload_video():
    """上传视频文件"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': '没有上传视频文件'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            # 安全的文件名
            filename = secure_filename(file.filename)
            
            # 创建临时文件保存上传的视频
            temp_dir = tempfile.gettempdir()
            filepath = os.path.join(temp_dir, f"uploaded_{int(time.time())}_{filename}")
            file.save(filepath)
            
            # 获取文件信息
            file_size = os.path.getsize(filepath)
            
            # 模拟视频分析（实际应用中这里会调用视频分析库）
            video_info = {
                'id': f"video_{int(time.time())}",
                'filename': filename,
                'filepath': filepath,
                'file_size_mb': round(file_size / (1024 * 1024), 2),
                'resolution': '1920x1080',  # 模拟分辨率
                'duration_seconds': random.uniform(30, 120),  # 模拟时长
                'fps': 30.0,
                'total_frames': int(random.uniform(30, 120) * 30),
                'upload_time': datetime.now().isoformat(),
                'status': 'uploaded'
            }
            
            return jsonify({
                'success': True,
                'message': f'视频 {filename} 上传成功',
                'video_info': video_info
            })
        else:
            return jsonify({'error': '不支持的文件格式'}), 400
            
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/video/process', methods=['POST'])
def process_video():
    """处理视频并进行跌倒检测"""
    try:
        data = request.json
        if not data:
            return jsonify({'error': '缺少处理参数'}), 400
        
        # 获取配置参数
        confidence_threshold = data.get('confidence_threshold', 0.8)
        detection_interval = data.get('detection_interval', 5)
        detection_mode = data.get('detection_mode', 'standard')
        test_environment = data.get('test_environment', 'laboratory')
        video_id = data.get('video_id', 'default')
        
        # 模拟处理时间
        processing_time = random.uniform(2.5, 5.0)
        time.sleep(0.5)  # 模拟处理延迟
        
        # 生成模拟检测结果
        detections = generate_fall_detections(confidence_threshold, detection_mode)
        
        # 计算统计信息
        fall_events = len(detections)
        
        results = {
            'success': True,
            'video_id': video_id,
            'processing_time': round(processing_time, 2),
            'fall_events': fall_events,
            'detections': detections,
            'config': {
                'confidence_threshold': confidence_threshold,
                'detection_interval': detection_interval,
                'detection_mode': detection_mode,
                'test_environment': test_environment
            },
            'analysis': {
                'total_frames_analyzed': random.randint(800, 1500),
                'detection_accuracy': round(random.uniform(88.5, 95.2), 1),
                'processing_speed': f"{random.uniform(25, 35):.1f} FPS",
                'memory_usage': f"{random.randint(245, 380)} MB"
            },
            'timestamp': datetime.now().isoformat()
        }
        
        return jsonify({'results': results})
        
    except Exception as e:
        return jsonify({
            'success': False,
            'error': f'视频处理失败: {str(e)}'
        }), 500

def generate_fall_detections(confidence_threshold, detection_mode):
    """生成模拟的跌倒检测结果"""
    detections = []
    
    # 根据检测模式调整检测数量和质量
    if detection_mode == 'high_accuracy':
        num_events = random.randint(2, 4)
        confidence_base = 0.85
    elif detection_mode == 'elderly_optimized':
        num_events = random.randint(3, 6)
        confidence_base = 0.80
    elif detection_mode == 'real_time':
        num_events = random.randint(1, 3)
        confidence_base = 0.75
    else:  # standard
        num_events = random.randint(2, 5)
        confidence_base = 0.82
    
    # 生成检测事件
    for i in range(num_events):
        # 随机时间点，确保不重叠
        start_time = random.uniform(5 + i * 8, 10 + i * 8)
        duration = random.uniform(1.5, 4.0)
        end_time = start_time + duration
        
        # 置信度要高于阈值
        confidence = max(confidence_threshold + 0.01, 
                        random.uniform(confidence_base, 0.95))
        
        # 跌倒类型
        fall_types = ['backward_fall', 'forward_fall', 'side_fall']
        fall_directions = ['backward', 'forward', 'side']
        severities = ['HIGH', 'CRITICAL', 'MEDIUM']
        
        detection = {
            'id': f'fall_{i+1}',
            'type': 'fall',
            'subtype': random.choice(fall_types),
            'start_time': round(start_time, 2),
            'end_time': round(end_time, 2),
            'duration': round(duration, 1),
            'confidence': round(confidence, 3),
            'severity': random.choice(severities),
            'fall_direction': random.choice(fall_directions),
            'body_angle': round(random.uniform(0.8, 1.4), 2),
            'start_frame': int(start_time * 30),
            'end_frame': int(end_time * 30),
            'bbox': [
                random.randint(200, 400),  # x1
                random.randint(150, 300),  # y1
                random.randint(500, 700),  # x2
                random.randint(400, 600)   # y2
            ],
            'center_point': [
                random.randint(300, 600),
                random.randint(250, 450)
            ],
            'person_id': f'person_{random.randint(1, 3)}',
            'timestamp': datetime.now().isoformat()
        }
        
        detections.append(detection)
    
    # 按时间排序
    detections.sort(key=lambda x: x['start_time'])
    
    return detections

@app.route('/api/algorithm/comparison', methods=['GET'])
def get_algorithm_comparison():
    """获取算法对比数据"""
    try:
        comparison_data = {
            'our_algorithm': {
                'name': '康养AI跌倒检测算法',
                'accuracy': 94.8,
                'precision': 92.3,
                'recall': 89.7,
                'f1_score': 91.0,
                'processing_speed': '28.5 FPS',
                'false_positive_rate': 0.048
            },
            'competitor_a': {
                'name': '传统算法A',
                'accuracy': 87.2,
                'precision': 85.1,
                'recall': 82.4,
                'f1_score': 83.7,
                'processing_speed': '22.1 FPS',
                'false_positive_rate': 0.128
            },
            'competitor_b': {
                'name': '传统算法B',
                'accuracy': 89.5,
                'precision': 88.3,
                'recall': 84.7,
                'f1_score': 86.5,
                'processing_speed': '19.8 FPS',
                'false_positive_rate': 0.095
            },
            'competitor_c': {
                'name': '深度学习算法C',
                'accuracy': 91.2,
                'precision': 89.8,
                'recall': 87.2,
                'f1_score': 88.5,
                'processing_speed': '15.3 FPS',
                'false_positive_rate': 0.072
            }
        }
        
        test_scenarios = [
            {
                'name': '老年人环境',
                'our_score': 95.2,
                'competitor_avg': 86.8
            },
            {
                'name': '低光照条件',
                'our_score': 91.5,
                'competitor_avg': 78.3
            },
            {
                'name': '多人场景',
                'our_score': 88.9,
                'competitor_avg': 82.1
            },
            {
                'name': '复杂背景',
                'our_score': 93.1,
                'competitor_avg': 84.7
            }
        ]
        
        return jsonify({
            'comparison_data': comparison_data,
            'test_scenarios': test_scenarios,
            'benchmark_date': datetime.now().isoformat()
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    print("🚀 启动康养AI跌倒检测演示API...")
    print("📍 API地址: http://localhost:8080")
    print("🎥 新功能: 支持视频上传和自定义处理")
    print("⚠️  注意: 这是演示版本，使用模拟数据")
    print("\n📊 API接口:")
    print("  - GET  /health - 健康检查")
    print("  - GET  /api/video/info - 默认视频信息")
    print("  - POST /api/video/upload - 上传视频文件")
    print("  - POST /api/video/process - 处理视频检测")
    print("  - GET  /api/algorithm/comparison - 算法对比")
    print("\n✅ 服务启动成功!")
    
    app.run(host='0.0.0.0', port=8080, debug=False)