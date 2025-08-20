#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
简化视频测试服务 
不依赖OpenCV，模拟真实视频检测测试
"""

from flask import Flask, request, jsonify, render_template_string
import os
import json
import time
import threading
from datetime import datetime
from werkzeug.utils import secure_filename
from real_fall_detector import SimpleFallDetector, RealFireSmokeDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'simple-video-test-2024'
app.config['MAX_CONTENT_LENGTH'] = 200 * 1024 * 1024  # 200MB max file size

# 上传文件夹配置
UPLOAD_FOLDER = 'test_videos'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv', 'flv', 'm4v'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 测试会话存储
test_sessions = {}

class SimpleVideoTester:
    """简化视频测试器"""
    
    def __init__(self):
        self.fall_detector = SimpleFallDetector()
        self.fire_detector = RealFireSmokeDetector()
    
    def test_video_simulation(self, video_name: str, test_type: str = 'all', 
                            frame_count: int = 100) -> dict:
        """模拟视频测试"""
        results = {
            'video_name': video_name,
            'test_type': test_type,
            'frame_count': frame_count,
            'detections': [],
            'alerts': [],
            'statistics': {},
            'start_time': datetime.now().isoformat()
        }
        
        print(f"🎬 开始测试视频: {video_name}")
        
        # 模拟逐帧处理
        for frame_num in range(1, frame_count + 1):
            frame_data = f"{video_name}_frame_{frame_num}"
            timestamp = frame_num / 30.0  # 假设30FPS
            
            # 跌倒检测
            if test_type in ['all', 'fall']:
                fall_result = self.fall_detector.detect_fall_from_video(
                    frame_data, frame_num, timestamp
                )
                
                if fall_result['is_fall']:
                    detection = {
                        'type': 'fall',
                        'frame_number': frame_num,
                        'timestamp': timestamp,
                        'confidence': fall_result['confidence'],
                        'person_id': fall_result.get('person_id'),
                        'severity': fall_result.get('severity'),
                        'details': fall_result
                    }
                    results['detections'].append(detection)
                    
                    # 生成告警
                    if fall_result['confidence'] > 0.7:
                        alert = {
                            'id': f"fall_{frame_num}_{int(time.time())}",
                            'type': 'fall',
                            'severity': 'HIGH' if fall_result['confidence'] > 0.8 else 'MEDIUM',
                            'message': f"检测到跌倒事件 (帧:{frame_num}, 置信度:{fall_result['confidence']:.2f})",
                            'timestamp': datetime.now().isoformat(),
                            'frame_number': frame_num,
                            'confidence': fall_result['confidence']
                        }
                        results['alerts'].append(alert)
                        print(f"🚨 {alert['severity']} 告警: {alert['message']}")
            
            # 火焰烟雾检测
            if test_type in ['all', 'fire']:
                fire_detections = self.fire_detector.detect_fire_smoke_from_video(
                    frame_data, frame_num, timestamp
                )
                
                for detection in fire_detections:
                    det_record = {
                        'type': detection['type'],
                        'frame_number': frame_num,
                        'timestamp': timestamp,
                        'confidence': detection['confidence'],
                        'bbox': detection.get('bbox'),
                        'area': detection.get('area'),
                        'features': detection.get('features'),
                        'details': detection
                    }
                    results['detections'].append(det_record)
                    
                    # 生成告警
                    if detection['confidence'] > 0.6:
                        severity = 'CRITICAL' if detection['type'] == 'fire' else 'HIGH'
                        alert = {
                            'id': f"{detection['type']}_{frame_num}_{int(time.time())}",
                            'type': detection['type'],
                            'severity': severity,
                            'message': f"检测到{detection['type']} (帧:{frame_num}, 置信度:{detection['confidence']:.2f})",
                            'timestamp': datetime.now().isoformat(),
                            'frame_number': frame_num,
                            'confidence': detection['confidence']
                        }
                        results['alerts'].append(alert)
                        print(f"🔥 {alert['severity']} 告警: {alert['message']}")
            
            # 每10帧显示进度
            if frame_num % 10 == 0:
                progress = (frame_num / frame_count) * 100
                print(f"📊 处理进度: {progress:.1f}% (帧 {frame_num}/{frame_count})")
            
            # 模拟处理时间
            time.sleep(0.01)
        
        # 收集统计信息
        if test_type in ['all', 'fall']:
            results['statistics']['fall'] = self.fall_detector.get_detection_statistics()
        if test_type in ['all', 'fire']:
            results['statistics']['fire'] = self.fire_detector.get_detection_statistics()
        
        results['end_time'] = datetime.now().isoformat()
        
        # 生成汇总
        detection_summary = {}
        for detection in results['detections']:
            det_type = detection['type']
            if det_type not in detection_summary:
                detection_summary[det_type] = {'count': 0, 'avg_confidence': 0}
            detection_summary[det_type]['count'] += 1
        
        # 计算平均置信度
        for det_type, summary in detection_summary.items():
            confidences = [d['confidence'] for d in results['detections'] if d['type'] == det_type]
            if confidences:
                summary['avg_confidence'] = sum(confidences) / len(confidences)
        
        results['summary'] = {
            'total_detections': len(results['detections']),
            'total_alerts': len(results['alerts']),
            'detection_summary': detection_summary,
            'processing_time': (datetime.fromisoformat(results['end_time']) - 
                              datetime.fromisoformat(results['start_time'])).total_seconds()
        }
        
        print(f"✅ 视频测试完成: {len(results['detections'])} 检测, {len(results['alerts'])} 告警")
        return results

def allowed_file(filename):
    """检查文件扩展名是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def get_file_size_mb(filepath):
    """获取文件大小(MB)"""
    return round(os.path.getsize(filepath) / (1024 * 1024), 2)

# 初始化测试器
video_tester = SimpleVideoTester()

@app.route('/')
def index():
    """测试主页"""
    return render_template_string(SIMPLE_TEST_HTML)

@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    """上传视频文件"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': '没有选择视频文件'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': '文件名为空'}), 400
        
        if file and allowed_file(file.filename):
            # 安全的文件名处理
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            # 保持原始文件名，但添加时间戳避免冲突
            name, ext = os.path.splitext(filename)
            safe_filename = f"{name}_{timestamp}{ext}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], safe_filename)
            file.save(filepath)
            
            file_size = get_file_size_mb(filepath)
            
            return jsonify({
                'success': True,
                'filename': safe_filename,
                'original_name': filename,
                'size_mb': file_size,
                'message': f'视频上传成功: {filename} ({file_size}MB)'
            })
        else:
            return jsonify({'error': '不支持的文件格式，请上传MP4、AVI、MOV等视频文件'}), 400
    
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/list_videos')
def list_uploaded_videos():
    """列出已上传的视频文件"""
    try:
        videos = []
        upload_dir = app.config['UPLOAD_FOLDER']
        
        if os.path.exists(upload_dir):
            for filename in os.listdir(upload_dir):
                if allowed_file(filename):
                    filepath = os.path.join(upload_dir, filename)
                    file_stats = os.stat(filepath)
                    
                    videos.append({
                        'filename': filename,
                        'size_mb': get_file_size_mb(filepath),
                        'upload_time': datetime.fromtimestamp(file_stats.st_mtime).strftime('%Y-%m-%d %H:%M:%S'),
                        'extension': filename.rsplit('.', 1)[1].lower()
                    })
        
        # 按上传时间排序
        videos.sort(key=lambda x: x['upload_time'], reverse=True)
        
        return jsonify({
            'videos': videos,
            'total': len(videos)
        })
    
    except Exception as e:
        return jsonify({'error': f'获取视频列表失败: {str(e)}'}), 500

@app.route('/api/delete_video', methods=['POST'])
def delete_video():
    """删除视频文件"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': '文件名不能为空'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({'success': True, 'message': f'文件 {filename} 删除成功'})
        else:
            return jsonify({'error': '文件不存在'}), 404
    
    except Exception as e:
        return jsonify({'error': f'删除失败: {str(e)}'}), 500

@app.route('/api/test_video', methods=['POST'])
def test_video():
    """测试视频检测"""
    try:
        data = request.json
        video_name = data.get('video_name', 'test_video.mp4')
        test_type = data.get('test_type', 'all')
        frame_count = data.get('frame_count', 100)
        
        # 创建测试会话
        session_id = f"test_{int(time.time())}"
        
        # 启动后台测试
        def run_test():
            try:
                test_sessions[session_id]['status'] = 'processing'
                result = video_tester.test_video_simulation(video_name, test_type, frame_count)
                test_sessions[session_id]['status'] = 'completed'
                test_sessions[session_id]['result'] = result
            except Exception as e:
                test_sessions[session_id]['status'] = 'failed'
                test_sessions[session_id]['error'] = str(e)
        
        # 初始化会话
        test_sessions[session_id] = {
            'video_name': video_name,
            'test_type': test_type,
            'frame_count': frame_count,
            'status': 'starting',
            'start_time': datetime.now().isoformat()
        }
        
        # 启动测试线程
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'视频检测测试已启动: {video_name}'
        })
    
    except Exception as e:
        return jsonify({'error': f'测试启动失败: {str(e)}'}), 500

@app.route('/api/test_status/<session_id>')
def get_test_status(session_id):
    """获取测试状态"""
    if session_id not in test_sessions:
        return jsonify({'error': '测试会话不存在'}), 404
    
    return jsonify(test_sessions[session_id])

@app.route('/api/test_result/<session_id>')
def get_test_result(session_id):
    """获取测试结果"""
    if session_id not in test_sessions:
        return jsonify({'error': '测试会话不存在'}), 404
    
    session = test_sessions[session_id]
    if session['status'] != 'completed':
        return jsonify({'error': '测试尚未完成'}), 400
    
    return jsonify(session.get('result', {}))

@app.route('/api/quick_test', methods=['POST'])
def quick_test():
    """快速测试"""
    try:
        data = request.json
        test_type = data.get('test_type', 'all')
        
        # 执行快速测试
        result = video_tester.test_video_simulation(
            'quick_test_video.mp4', test_type, 30
        )
        
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'快速测试失败: {str(e)}'}), 500

@app.route('/api/test_scenarios')
def get_test_scenarios():
    """获取测试场景"""
    scenarios = {
        'fall_scenarios': [
            {
                'name': 'elderly_bathroom_fall.mp4',
                'description': '老人卫生间跌倒场景',
                'expected_detections': ['fall'],
                'difficulty': 'medium',
                'duration': '45秒'
            },
            {
                'name': 'elderly_bedroom_fall.mp4',
                'description': '老人卧室跌倒场景',
                'expected_detections': ['fall'],
                'difficulty': 'easy',
                'duration': '30秒'
            },
            {
                'name': 'complex_movement_fall.mp4',
                'description': '复杂运动中的跌倒',
                'expected_detections': ['fall'],
                'difficulty': 'hard',
                'duration': '60秒'
            }
        ],
        'fire_scenarios': [
            {
                'name': 'kitchen_fire.mp4',
                'description': '厨房火灾场景',
                'expected_detections': ['fire', 'smoke'],
                'difficulty': 'medium',
                'duration': '90秒'
            },
            {
                'name': 'living_room_smoke.mp4',
                'description': '客厅烟雾检测',
                'expected_detections': ['smoke'],
                'difficulty': 'easy',
                'duration': '60秒'
            },
            {
                'name': 'electrical_fire.mp4',
                'description': '电器火灾场景',
                'expected_detections': ['fire', 'smoke'],
                'difficulty': 'hard',
                'duration': '120秒'
            }
        ],
        'mixed_scenarios': [
            {
                'name': 'emergency_evacuation.mp4',
                'description': '紧急疏散场景（跌倒+火灾）',
                'expected_detections': ['fall', 'fire', 'smoke'],
                'difficulty': 'very_hard',
                'duration': '180秒'
            }
        ]
    }
    
    return jsonify(scenarios)

@app.route('/api/session_list')
def list_sessions():
    """列出所有测试会话"""
    return jsonify({'sessions': test_sessions})

# HTML模板
SIMPLE_TEST_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎬 视频检测算法测试平台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
            transition: background 0.3s;
        }
        .btn:hover { background: rgba(255, 255, 255, 0.3); }
        .btn-primary { background: #4CAF50; }
        .btn-primary:hover { background: #45a049; }
        .btn-warning { background: #FF9800; }
        .btn-warning:hover { background: #F57C00; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .alert {
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .alert-success { background: rgba(76, 175, 80, 0.3); border-color: #4CAF50; }
        .alert-warning { background: rgba(255, 152, 0, 0.3); border-color: #FF9800; }
        .alert-error { background: rgba(244, 67, 54, 0.3); border-color: #f44336; }
        .alert-info { background: rgba(33, 150, 243, 0.3); border-color: #2196F3; }
        .result-area {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        .stats { display: flex; justify-content: space-around; flex-wrap: wrap; margin: 20px 0; }
        .stat-item { text-align: center; margin: 10px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #4CAF50; }
        .scenario-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            border-left: 4px solid #4CAF50;
        }
        .difficulty { padding: 5px 10px; border-radius: 15px; font-size: 0.8em; display: inline-block; }
        .difficulty-easy { background: #4CAF50; }
        .difficulty-medium { background: #FF9800; }
        .difficulty-hard { background: #f44336; }
        .difficulty-very_hard { background: #9C27B0; }
        input, select { padding: 10px; margin: 5px; border-radius: 5px; border: none; }
        .upload-area {
            border: 3px dashed rgba(255, 255, 255, 0.5);
            border-radius: 15px;
            margin: 20px 0;
            transition: all 0.3s ease;
            cursor: pointer;
        }
        .upload-area:hover { border-color: rgba(255, 255, 255, 0.8); background: rgba(255, 255, 255, 0.05); }
        .upload-area.dragover { border-color: #4CAF50; background: rgba(76, 175, 80, 0.1); }
        .progress {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
            overflow: hidden;
        }
        .progress-bar {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            height: 100%;
            width: 0%;
            transition: width 0.3s ease;
            border-radius: 10px;
        }
        .video-item {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 15px;
            margin: 10px 0;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .video-info { flex: 1; }
        .video-actions { margin-left: 15px; }
        .btn-small { padding: 8px 16px; font-size: 14px; }
        .btn-danger { background: #f44336; }
        .btn-danger:hover { background: #da190b; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 视频检测算法测试平台</h1>
            <p>模拟真实视频场景，测试跌倒检测和火焰烟雾检测算法效果</p>
        </div>

        <div class="grid">
            <!-- 视频上传区域 -->
            <div class="section">
                <h2>📤 视频上传</h2>
                <div class="upload-area" id="uploadArea">
                    <div style="text-align: center; padding: 20px;">
                        <p>📁 拖拽MP4视频文件到此处，或点击选择文件</p>
                        <p style="font-size: 0.9em; opacity: 0.8;">支持格式: MP4, AVI, MOV, MKV, WMV (最大200MB)</p>
                        <input type="file" id="videoFile" accept="video/*" style="display: none;">
                        <button class="btn btn-primary" onclick="document.getElementById('videoFile').click()">选择视频文件</button>
                    </div>
                </div>
                <div id="uploadStatus"></div>
                <div id="uploadProgress" style="display: none;">
                    <div class="progress">
                        <div class="progress-bar" id="progressBar"></div>
                    </div>
                </div>
            </div>

            <!-- 快速测试区域 -->
            <div class="section">
                <h2>⚡ 快速测试</h2>
                <p>选择检测类型进行快速算法测试</p>
                <div>
                    <select id="quickTestType" class="btn">
                        <option value="all">全部检测</option>
                        <option value="fall">仅跌倒检测</option>
                        <option value="fire">仅火焰检测</option>
                    </select>
                    <button class="btn btn-primary" onclick="runQuickTest()">开始快速测试</button>
                </div>
                <div id="quickTestResult"></div>
            </div>
        </div>

        <!-- 自定义测试区域 -->
        <div class="section">
            <h2>🧪 自定义测试</h2>
            <div class="grid">
                <div>
                    <h4>📹 选择视频文件</h4>
                    <select id="videoName" class="btn" style="width: 100%; margin: 10px 0;">
                        <option value="">选择已上传的视频...</option>
                    </select>
                    <button class="btn" onclick="refreshVideoList()">🔄 刷新列表</button>
                </div>
                <div>
                    <h4>⚙️ 测试配置</h4>
                    <select id="testType" class="btn" style="width: 100%; margin: 10px 0;">
                        <option value="all">全部检测</option>
                        <option value="fall">仅跌倒检测</option>
                        <option value="fire">仅火焰检测</option>
                    </select>
                    <input type="number" id="frameCount" placeholder="处理帧数" value="100" min="10" max="1000" style="width: 100%; margin: 10px 0;">
                </div>
            </div>
            <div style="text-align: center; margin: 20px 0;">
                <button class="btn btn-primary" onclick="startCustomTest()">🚀 开始自定义测试</button>
            </div>
            <div id="customTestStatus"></div>
            
            <!-- 已上传视频列表 -->
            <div id="videoListSection" style="margin-top: 30px;">
                <h4>📂 已上传的视频文件</h4>
                <div id="videoList">
                    <p style="opacity: 0.7;">正在加载视频列表...</p>
                </div>
            </div>
        </div>

        <!-- 测试场景展示 -->
        <div class="section">
            <h2>📋 预设测试场景</h2>
            <div id="scenariosList">加载中...</div>
        </div>

        <!-- 结果展示区域 -->
        <div class="section">
            <h2>📊 测试结果</h2>
            <div class="stats" id="statsArea">
                <div class="stat-item">
                    <div class="stat-number" id="totalDetections">0</div>
                    <div>总检测数</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="totalAlerts">0</div>
                    <div>告警数量</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="avgConfidence">0%</div>
                    <div>平均置信度</div>
                </div>
                <div class="stat-item">
                    <div class="stat-number" id="processingTime">0s</div>
                    <div>处理时间</div>
                </div>
            </div>
            <div class="result-area" id="resultArea">
                <p>等待测试结果...</p>
            </div>
        </div>
    </div>

    <script>
        // 页面加载时初始化
        window.onload = function() {
            loadTestScenarios();
            refreshVideoList();
            setupFileUpload();
        };

        // 设置文件上传功能
        function setupFileUpload() {
            const uploadArea = document.getElementById('uploadArea');
            const fileInput = document.getElementById('videoFile');

            // 文件选择事件
            fileInput.addEventListener('change', handleFileSelect);

            // 拖拽事件
            uploadArea.addEventListener('dragover', handleDragOver);
            uploadArea.addEventListener('dragleave', handleDragLeave);
            uploadArea.addEventListener('drop', handleFileDrop);
            
            // 点击上传区域选择文件
            uploadArea.addEventListener('click', function() {
                fileInput.click();
            });
        }

        function handleDragOver(e) {
            e.preventDefault();
            document.getElementById('uploadArea').classList.add('dragover');
        }

        function handleDragLeave(e) {
            e.preventDefault();
            document.getElementById('uploadArea').classList.remove('dragover');
        }

        function handleFileDrop(e) {
            e.preventDefault();
            document.getElementById('uploadArea').classList.remove('dragover');
            
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                uploadVideoFile(files[0]);
            }
        }

        function handleFileSelect(e) {
            const file = e.target.files[0];
            if (file) {
                uploadVideoFile(file);
            }
        }

        function uploadVideoFile(file) {
            // 检查文件类型
            const allowedTypes = ['video/mp4', 'video/avi', 'video/mov', 'video/mkv', 'video/wmv'];
            if (!allowedTypes.some(type => file.type.startsWith('video/'))) {
                document.getElementById('uploadStatus').innerHTML = 
                    '<div class="alert alert-error">请选择视频文件 (MP4, AVI, MOV等格式)</div>';
                return;
            }

            // 检查文件大小 (200MB)
            if (file.size > 200 * 1024 * 1024) {
                document.getElementById('uploadStatus').innerHTML = 
                    '<div class="alert alert-error">文件大小超过200MB限制</div>';
                return;
            }

            const formData = new FormData();
            formData.append('video', file);

            document.getElementById('uploadStatus').innerHTML = 
                '<div class="alert alert-info">上传中...</div>';
            
            document.getElementById('uploadProgress').style.display = 'block';

            // 创建 XMLHttpRequest 以支持进度显示
            const xhr = new XMLHttpRequest();
            
            xhr.upload.addEventListener('progress', function(e) {
                if (e.lengthComputable) {
                    const percentComplete = (e.loaded / e.total) * 100;
                    document.getElementById('progressBar').style.width = percentComplete + '%';
                }
            });

            xhr.onload = function() {
                document.getElementById('uploadProgress').style.display = 'none';
                
                if (xhr.status === 200) {
                    const response = JSON.parse(xhr.responseText);
                    if (response.success) {
                        document.getElementById('uploadStatus').innerHTML = 
                            '<div class="alert alert-success">' + response.message + '</div>';
                        refreshVideoList(); // 刷新视频列表
                    } else {
                        document.getElementById('uploadStatus').innerHTML = 
                            '<div class="alert alert-error">上传失败: ' + response.error + '</div>';
                    }
                } else {
                    document.getElementById('uploadStatus').innerHTML = 
                        '<div class="alert alert-error">上传失败，请重试</div>';
                }
            };

            xhr.onerror = function() {
                document.getElementById('uploadProgress').style.display = 'none';
                document.getElementById('uploadStatus').innerHTML = 
                    '<div class="alert alert-error">上传过程中发生错误</div>';
            };

            xhr.open('POST', '/api/upload_video');
            xhr.send(formData);
        }

        function refreshVideoList() {
            fetch('/api/list_videos')
            .then(response => response.json())
            .then(data => {
                const videoSelect = document.getElementById('videoName');
                const videoListDiv = document.getElementById('videoList');
                
                // 更新下拉选择框
                videoSelect.innerHTML = '<option value="">选择已上传的视频...</option>';
                
                if (data.videos && data.videos.length > 0) {
                    data.videos.forEach(video => {
                        const option = document.createElement('option');
                        option.value = video.filename;
                        option.textContent = `${video.filename} (${video.size_mb}MB)`;
                        videoSelect.appendChild(option);
                    });

                    // 更新视频列表显示
                    let listHtml = '';
                    data.videos.forEach(video => {
                        listHtml += `
                            <div class="video-item">
                                <div class="video-info">
                                    <strong>📹 ${video.filename}</strong><br>
                                    <small>大小: ${video.size_mb}MB | 上传时间: ${video.upload_time} | 格式: ${video.extension.toUpperCase()}</small>
                                </div>
                                <div class="video-actions">
                                    <button class="btn btn-small" onclick="selectVideo('${video.filename}')">选择</button>
                                    <button class="btn btn-small btn-danger" onclick="deleteVideo('${video.filename}')">删除</button>
                                </div>
                            </div>
                        `;
                    });
                    videoListDiv.innerHTML = listHtml;
                } else {
                    videoListDiv.innerHTML = '<p style="opacity: 0.7; text-align: center;">暂无上传的视频文件</p>';
                }
            })
            .catch(error => {
                console.error('获取视频列表失败:', error);
                document.getElementById('videoList').innerHTML = 
                    '<div class="alert alert-error">获取视频列表失败</div>';
            });
        }

        function selectVideo(filename) {
            document.getElementById('videoName').value = filename;
            document.getElementById('customTestStatus').innerHTML = 
                '<div class="alert alert-success">已选择视频: ' + filename + '</div>';
        }

        function deleteVideo(filename) {
            if (confirm('确定要删除视频文件 "' + filename + '" 吗？')) {
                fetch('/api/delete_video', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({filename: filename})
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        document.getElementById('customTestStatus').innerHTML = 
                            '<div class="alert alert-success">' + data.message + '</div>';
                        refreshVideoList();
                    } else {
                        document.getElementById('customTestStatus').innerHTML = 
                            '<div class="alert alert-error">删除失败: ' + data.error + '</div>';
                    }
                });
            }
        }

        function loadTestScenarios() {
            fetch('/api/test_scenarios')
            .then(response => response.json())
            .then(data => {
                let html = '';
                
                // 跌倒场景
                html += '<h3>🤕 跌倒检测场景</h3>';
                data.fall_scenarios.forEach(scenario => {
                    html += createScenarioCard(scenario);
                });
                
                // 火灾场景  
                html += '<h3>🔥 火焰烟雾检测场景</h3>';
                data.fire_scenarios.forEach(scenario => {
                    html += createScenarioCard(scenario);
                });
                
                // 混合场景
                html += '<h3>⚡ 复合场景</h3>';
                data.mixed_scenarios.forEach(scenario => {
                    html += createScenarioCard(scenario);
                });
                
                document.getElementById('scenariosList').innerHTML = html;
            });
        }

        function createScenarioCard(scenario) {
            return `
                <div class="scenario-card">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <div>
                            <strong>${scenario.name}</strong>
                            <span class="difficulty difficulty-${scenario.difficulty}">${scenario.difficulty}</span>
                        </div>
                        <button class="btn" onclick="testScenario('${scenario.name}')">测试</button>
                    </div>
                    <p>${scenario.description}</p>
                    <small>预期检测: ${scenario.expected_detections.join(', ')} | 时长: ${scenario.duration}</small>
                </div>
            `;
        }

        function runQuickTest() {
            const testType = document.getElementById('quickTestType').value;
            
            document.getElementById('quickTestResult').innerHTML = 
                '<div class="alert alert-info">快速测试进行中...</div>';
            
            fetch('/api/quick_test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({test_type: testType})
            })
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    document.getElementById('quickTestResult').innerHTML = 
                        '<div class="alert alert-error">测试失败: ' + data.error + '</div>';
                } else {
                    document.getElementById('quickTestResult').innerHTML = 
                        '<div class="alert alert-success">快速测试完成</div>';
                    displayResults(data);
                }
            });
        }

        function startCustomTest() {
            const videoName = document.getElementById('videoName').value;
            const testType = document.getElementById('testType').value;
            const frameCount = parseInt(document.getElementById('frameCount').value);
            
            // 验证输入
            if (!videoName) {
                document.getElementById('customTestStatus').innerHTML = 
                    '<div class="alert alert-error">请先选择或上传视频文件</div>';
                return;
            }
            
            if (frameCount < 10 || frameCount > 1000) {
                document.getElementById('customTestStatus').innerHTML = 
                    '<div class="alert alert-error">处理帧数必须在10-1000之间</div>';
                return;
            }
            
            document.getElementById('customTestStatus').innerHTML = 
                '<div class="alert alert-info">🚀 启动自定义测试: ' + videoName + '</div>';
            
            fetch('/api/test_video', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    video_name: videoName,
                    test_type: testType,
                    frame_count: frameCount
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('customTestStatus').innerHTML = 
                        '<div class="alert alert-success">✅ 测试已启动，会话ID: ' + data.session_id + '</div>';
                    monitorTest(data.session_id);
                } else {
                    document.getElementById('customTestStatus').innerHTML = 
                        '<div class="alert alert-error">❌ 启动失败: ' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('customTestStatus').innerHTML = 
                    '<div class="alert alert-error">❌ 网络错误: ' + error + '</div>';
            });
        }

        function testScenario(videoName) {
            // 根据视频名称推断测试类型
            let testType = 'all';
            if (videoName.includes('fall')) testType = 'fall';
            else if (videoName.includes('fire') || videoName.includes('smoke')) testType = 'fire';
            
            document.getElementById('videoName').value = videoName;
            document.getElementById('testType').value = testType;
            startCustomTest();
        }

        function monitorTest(sessionId) {
            const checkStatus = () => {
                fetch('/api/test_status/' + sessionId)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'completed') {
                        document.getElementById('customTestStatus').innerHTML = 
                            '<div class="alert alert-success">测试完成</div>';
                        
                        fetch('/api/test_result/' + sessionId)
                        .then(response => response.json())
                        .then(result => displayResults(result));
                        
                    } else if (data.status === 'failed') {
                        document.getElementById('customTestStatus').innerHTML = 
                            '<div class="alert alert-error">测试失败: ' + data.error + '</div>';
                    } else if (data.status === 'processing') {
                        document.getElementById('customTestStatus').innerHTML = 
                            '<div class="alert alert-info">测试进行中...</div>';
                        setTimeout(checkStatus, 2000);
                    } else {
                        setTimeout(checkStatus, 1000);
                    }
                });
            };
            
            checkStatus();
        }

        function displayResults(data) {
            // 更新统计数据
            const detections = data.detections || [];
            const alerts = data.alerts || [];
            const summary = data.summary || {};
            
            document.getElementById('totalDetections').textContent = summary.total_detections || detections.length;
            document.getElementById('totalAlerts').textContent = summary.total_alerts || alerts.length;
            document.getElementById('processingTime').textContent = (summary.processing_time || 0).toFixed(1) + 's';
            
            // 计算平均置信度
            let avgConf = 0;
            if (detections.length > 0) {
                avgConf = detections.reduce((sum, d) => sum + (d.confidence || 0), 0) / detections.length;
            }
            document.getElementById('avgConfidence').textContent = Math.round(avgConf * 100) + '%';
            
            // 显示详细结果
            let resultHtml = '<h3>🔍 检测详情:</h3>';
            
            // 按类型分组显示检测结果
            const detectionsByType = {};
            detections.forEach(detection => {
                const type = detection.type;
                if (!detectionsByType[type]) detectionsByType[type] = [];
                detectionsByType[type].push(detection);
            });
            
            Object.keys(detectionsByType).forEach(type => {
                const typeDetections = detectionsByType[type];
                const typeIcon = type === 'fall' ? '🤕' : (type === 'fire' ? '🔥' : '💨');
                
                resultHtml += `<h4>${typeIcon} ${type.toUpperCase()} 检测 (${typeDetections.length}次)</h4>`;
                
                typeDetections.slice(0, 5).forEach(detection => {
                    resultHtml += `
                        <div class="alert alert-info">
                            帧 ${detection.frame_number} - 置信度: ${(detection.confidence * 100).toFixed(1)}% 
                            (时间: ${detection.timestamp.toFixed(1)}s)
                        </div>
                    `;
                });
                
                if (typeDetections.length > 5) {
                    resultHtml += `<p>... 还有 ${typeDetections.length - 5} 个检测结果</p>`;
                }
            });
            
            // 显示告警
            if (alerts.length > 0) {
                resultHtml += '<h3>🚨 告警信息:</h3>';
                alerts.slice(0, 10).forEach(alert => {
                    const alertClass = alert.severity === 'CRITICAL' ? 'alert-error' : 
                                     alert.severity === 'HIGH' ? 'alert-warning' : 'alert-info';
                    resultHtml += `
                        <div class="alert ${alertClass}">
                            <strong>${alert.severity}</strong>: ${alert.message}
                        </div>
                    `;
                });
                
                if (alerts.length > 10) {
                    resultHtml += `<p>... 还有 ${alerts.length - 10} 个告警</p>`;
                }
            }
            
            // 显示统计信息
            if (data.statistics) {
                resultHtml += '<h3>📈 算法统计:</h3>';
                Object.keys(data.statistics).forEach(key => {
                    const stats = data.statistics[key];
                    resultHtml += `<h4>${key.toUpperCase()} 检测器:</h4>`;
                    resultHtml += '<div style="margin-left: 20px;">';
                    Object.keys(stats).forEach(statKey => {
                        resultHtml += `<p>${statKey}: ${stats[statKey]}</p>`;
                    });
                    resultHtml += '</div>';
                });
            }
            
            document.getElementById('resultArea').innerHTML = resultHtml;
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🎬 启动简化视频测试服务...")
    print("📍 访问地址: http://localhost:5557")
    print("🧪 支持功能:")
    print("  - 跌倒检测算法测试")
    print("  - 火焰烟雾检测算法测试")
    print("  - 预设测试场景")
    print("  - 实时告警模拟")
    print("  - 检测统计分析")
    
    app.run(host='0.0.0.0', port=5557, debug=False)