#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频测试API服务
支持上传视频文件进行跌倒和火焰检测测试
"""

from flask import Flask, request, jsonify, render_template_string
import os
import json
import base64
import threading
import time
from datetime import datetime
from werkzeug.utils import secure_filename

# 导入检测器
from video_processor import VideoProcessor
from real_fall_detector import SimpleFallDetector, RealFireSmokeDetector

app = Flask(__name__)
app.config['SECRET_KEY'] = 'video-test-2024'
app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024  # 100MB max file size

# 上传配置
UPLOAD_FOLDER = 'test_videos'
ALLOWED_EXTENSIONS = {'mp4', 'avi', 'mov', 'mkv', 'wmv'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 全局处理器
video_processor = VideoProcessor()

# 活跃的测试会话
active_sessions = {}

def allowed_file(filename):
    """检查文件类型是否允许"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/')
def index():
    """视频测试主页"""
    return render_template_string(VIDEO_TEST_HTML)

@app.route('/api/upload_video', methods=['POST'])
def upload_video():
    """上传视频文件"""
    try:
        if 'video' not in request.files:
            return jsonify({'error': '没有选择视频文件'}), 400
        
        file = request.files['video']
        if file.filename == '':
            return jsonify({'error': '没有选择文件'}), 400
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{timestamp}_{filename}"
            
            filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            file.save(filepath)
            
            # 获取视频信息
            video_info = {
                'filename': filename,
                'filepath': filepath,
                'upload_time': datetime.now().isoformat(),
                'size': os.path.getsize(filepath),
                'status': 'uploaded'
            }
            
            return jsonify({
                'success': True,
                'video_info': video_info,
                'message': '视频上传成功'
            })
        else:
            return jsonify({'error': '不支持的文件格式'}), 400
    
    except Exception as e:
        return jsonify({'error': f'上传失败: {str(e)}'}), 500

@app.route('/api/test_video', methods=['POST'])
def test_video():
    """测试视频检测"""
    try:
        data = request.json
        filename = data.get('filename')
        test_type = data.get('test_type', 'all')  # all, fall, fire
        
        if not filename:
            return jsonify({'error': '缺少文件名'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '视频文件不存在'}), 404
        
        # 创建测试会话
        session_id = f"test_{int(time.time())}"
        
        # 配置检测选项
        enable_fall = test_type in ['all', 'fall']
        enable_fire = test_type in ['all', 'fire']
        
        # 启动后台处理
        def process_video():
            try:
                result = video_processor.process_video_file(
                    filepath, 
                    session_id,
                    enable_fall=enable_fall,
                    enable_fire=enable_fire,
                    save_results=True
                )
                
                # 更新会话状态
                active_sessions[session_id]['status'] = 'completed'
                active_sessions[session_id]['result'] = result
                
            except Exception as e:
                active_sessions[session_id]['status'] = 'failed'
                active_sessions[session_id]['error'] = str(e)
        
        # 初始化会话
        active_sessions[session_id] = {
            'filename': filename,
            'test_type': test_type,
            'status': 'processing',
            'start_time': datetime.now().isoformat(),
            'progress': 0
        }
        
        # 启动处理线程
        thread = threading.Thread(target=process_video)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': '视频检测已启动',
            'test_config': {
                'enable_fall': enable_fall,
                'enable_fire': enable_fire
            }
        })
    
    except Exception as e:
        return jsonify({'error': f'测试启动失败: {str(e)}'}), 500

@app.route('/api/test_status/<session_id>')
def get_test_status(session_id):
    """获取测试状态"""
    if session_id not in active_sessions:
        return jsonify({'error': '会话不存在'}), 404
    
    session = active_sessions[session_id]
    return jsonify(session)

@app.route('/api/test_result/<session_id>')
def get_test_result(session_id):
    """获取测试结果"""
    if session_id not in active_sessions:
        return jsonify({'error': '会话不存在'}), 404
    
    session = active_sessions[session_id]
    if session['status'] != 'completed':
        return jsonify({'error': '测试尚未完成'}), 400
    
    return jsonify(session.get('result', {}))

@app.route('/api/demo_test', methods=['POST'])
def demo_test():
    """演示测试 - 使用模拟视频数据"""
    try:
        data = request.json
        test_type = data.get('test_type', 'all')
        frame_count = data.get('frame_count', 100)
        
        # 创建检测器
        fall_detector = SimpleFallDetector()
        fire_detector = RealFireSmokeDetector()
        
        results = {
            'test_type': test_type,
            'frame_count': frame_count,
            'detections': [],
            'alerts': [],
            'statistics': {},
            'start_time': datetime.now().isoformat()
        }
        
        # 模拟处理帧
        for frame_num in range(1, frame_count + 1):
            frame_data = f"demo_frame_{frame_num}"
            timestamp = frame_num / 30.0  # 30FPS
            
            # 跌倒检测
            if test_type in ['all', 'fall']:
                fall_result = fall_detector.detect_fall_from_video(
                    frame_data, frame_num, timestamp
                )
                
                if fall_result['is_fall']:
                    detection = {
                        'type': 'fall',
                        'frame_number': frame_num,
                        'timestamp': timestamp,
                        'confidence': fall_result['confidence'],
                        'details': fall_result
                    }
                    results['detections'].append(detection)
                    
                    # 生成告警
                    if fall_result['confidence'] > 0.8:
                        alert = {
                            'id': f"fall_alert_{frame_num}",
                            'type': 'fall',
                            'severity': 'HIGH',
                            'message': f"检测到跌倒事件 (帧:{frame_num})",
                            'timestamp': datetime.now().isoformat(),
                            'confidence': fall_result['confidence']
                        }
                        results['alerts'].append(alert)
            
            # 火焰烟雾检测
            if test_type in ['all', 'fire']:
                fire_detections = fire_detector.detect_fire_smoke_from_video(
                    frame_data, frame_num, timestamp
                )
                
                for detection in fire_detections:
                    det_record = {
                        'type': detection['type'],
                        'frame_number': frame_num,
                        'timestamp': timestamp,
                        'confidence': detection['confidence'],
                        'details': detection
                    }
                    results['detections'].append(det_record)
                    
                    # 生成告警
                    if detection['confidence'] > 0.6:
                        severity = 'CRITICAL' if detection['type'] == 'fire' else 'HIGH'
                        alert = {
                            'id': f"{detection['type']}_alert_{frame_num}",
                            'type': detection['type'],
                            'severity': severity,
                            'message': f"检测到{detection['type']} (帧:{frame_num})",
                            'timestamp': datetime.now().isoformat(),
                            'confidence': detection['confidence']
                        }
                        results['alerts'].append(alert)
        
        # 收集统计信息
        if test_type in ['all', 'fall']:
            results['statistics']['fall'] = fall_detector.get_detection_statistics()
        if test_type in ['all', 'fire']:
            results['statistics']['fire'] = fire_detector.get_detection_statistics()
        
        results['end_time'] = datetime.now().isoformat()
        results['summary'] = {
            'total_detections': len(results['detections']),
            'total_alerts': len(results['alerts']),
            'detection_types': list(set(d['type'] for d in results['detections']))
        }
        
        return jsonify(results)
    
    except Exception as e:
        return jsonify({'error': f'演示测试失败: {str(e)}'}), 500

@app.route('/api/realtime_test', methods=['POST'])
def start_realtime_test():
    """启动实时测试"""
    try:
        data = request.json
        filename = data.get('filename')
        
        if not filename:
            return jsonify({'error': '缺少文件名'}), 400
        
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        if not os.path.exists(filepath):
            return jsonify({'error': '视频文件不存在'}), 404
        
        # 启动实时处理
        session_id = f"realtime_{int(time.time())}"
        
        def alert_callback(result):
            """告警回调函数"""
            alerts = result.get('alerts', [])
            if alerts:
                print(f"🚨 实时告警: {len(alerts)} 个")
                for alert in alerts:
                    print(f"  - {alert['severity']}: {alert['message']}")
        
        success = video_processor.process_video_realtime(
            filepath, session_id, callback=alert_callback
        )
        
        if success:
            active_sessions[session_id] = {
                'type': 'realtime',
                'filename': filename,
                'status': 'running',
                'start_time': datetime.now().isoformat()
            }
            
            return jsonify({
                'success': True,
                'session_id': session_id,
                'message': '实时测试已启动'
            })
        else:
            return jsonify({'error': '实时测试启动失败'}), 500
    
    except Exception as e:
        return jsonify({'error': f'实时测试失败: {str(e)}'}), 500

@app.route('/api/stop_realtime/<session_id>', methods=['POST'])
def stop_realtime_test(session_id):
    """停止实时测试"""
    try:
        if session_id not in active_sessions:
            return jsonify({'error': '会话不存在'}), 404
        
        video_processor.stop_realtime_processing()
        
        active_sessions[session_id]['status'] = 'stopped'
        active_sessions[session_id]['end_time'] = datetime.now().isoformat()
        
        return jsonify({'success': True, 'message': '实时测试已停止'})
    
    except Exception as e:
        return jsonify({'error': f'停止失败: {str(e)}'}), 500

@app.route('/api/get_realtime_result/<session_id>')
def get_realtime_result(session_id):
    """获取实时检测结果"""
    try:
        result = video_processor.get_latest_result()
        if result:
            return jsonify(result)
        else:
            return jsonify({'message': '暂无新结果'})
    
    except Exception as e:
        return jsonify({'error': f'获取结果失败: {str(e)}'}), 500

@app.route('/api/list_videos')
def list_videos():
    """列出已上传的视频"""
    try:
        videos = []
        for filename in os.listdir(app.config['UPLOAD_FOLDER']):
            if allowed_file(filename):
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                videos.append({
                    'filename': filename,
                    'size': os.path.getsize(filepath),
                    'modified': datetime.fromtimestamp(
                        os.path.getmtime(filepath)
                    ).isoformat()
                })
        
        return jsonify({'videos': videos})
    
    except Exception as e:
        return jsonify({'error': f'获取视频列表失败: {str(e)}'}), 500

# HTML模板
VIDEO_TEST_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🎬 康养视频检测测试平台</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
        }
        .container { max-width: 1200px; margin: 0 auto; padding: 20px; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 2.5em; margin-bottom: 10px; }
        .section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
        }
        .upload-area {
            border: 3px dashed rgba(255, 255, 255, 0.5);
            border-radius: 10px;
            padding: 40px;
            text-align: center;
            margin-bottom: 20px;
            transition: border-color 0.3s;
        }
        .upload-area:hover { border-color: rgba(255, 255, 255, 0.8); }
        .btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px;
            transition: background 0.3s;
        }
        .btn:hover { background: rgba(255, 255, 255, 0.3); }
        .btn-primary { background: #4CAF50; }
        .btn-primary:hover { background: #45a049; }
        .btn-danger { background: #f44336; }
        .btn-danger:hover { background: #da190b; }
        .result-area {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            max-height: 400px;
            overflow-y: auto;
        }
        .alert {
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
        }
        .alert-success { background: rgba(76, 175, 80, 0.3); border-color: #4CAF50; }
        .alert-warning { background: rgba(255, 152, 0, 0.3); border-color: #FF9800; }
        .alert-error { background: rgba(244, 67, 54, 0.3); border-color: #f44336; }
        .progress {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            height: 20px;
            margin: 10px 0;
        }
        .progress-bar {
            background: #4CAF50;
            height: 100%;
            border-radius: 10px;
            transition: width 0.3s;
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; }
        .stats { display: flex; justify-content: space-around; flex-wrap: wrap; }
        .stat-item { text-align: center; margin: 10px; }
        .stat-number { font-size: 2em; font-weight: bold; color: #4CAF50; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🎬 康养视频检测测试平台</h1>
            <p>上传真实视频进行跌倒检测和火焰烟雾检测算法测试</p>
        </div>

        <div class="grid">
            <!-- 视频上传区域 -->
            <div class="section">
                <h2>📤 视频上传</h2>
                <div class="upload-area" id="uploadArea">
                    <p>拖拽视频文件到此处，或点击选择文件</p>
                    <p>支持格式: MP4, AVI, MOV, MKV, WMV</p>
                    <input type="file" id="videoFile" accept="video/*" style="display: none;">
                    <button class="btn" onclick="document.getElementById('videoFile').click()">选择视频</button>
                </div>
                <div id="uploadStatus"></div>
            </div>

            <!-- 测试控制区域 -->
            <div class="section">
                <h2>🧪 检测测试</h2>
                <div>
                    <label>测试类型:</label><br>
                    <select id="testType" class="btn">
                        <option value="all">全部检测</option>
                        <option value="fall">仅跌倒检测</option>
                        <option value="fire">仅火焰检测</option>
                    </select>
                </div>
                <div style="margin-top: 20px;">
                    <button class="btn btn-primary" onclick="startTest()">开始检测</button>
                    <button class="btn" onclick="demoTest()">演示测试</button>
                    <button class="btn btn-danger" onclick="stopTest()">停止测试</button>
                </div>
                <div id="testStatus"></div>
            </div>
        </div>

        <!-- 结果显示区域 -->
        <div class="section">
            <h2>📊 检测结果</h2>
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
            </div>
            <div class="result-area" id="resultArea">
                <p>等待测试结果...</p>
            </div>
        </div>
    </div>

    <script>
        let currentSessionId = null;
        let currentFilename = null;

        // 文件上传处理
        document.getElementById('videoFile').addEventListener('change', uploadVideo);
        
        function uploadVideo() {
            const fileInput = document.getElementById('videoFile');
            const file = fileInput.files[0];
            
            if (!file) return;
            
            const formData = new FormData();
            formData.append('video', file);
            
            document.getElementById('uploadStatus').innerHTML = 
                '<div class="alert alert-warning">上传中...</div>';
            
            fetch('/api/upload_video', {
                method: 'POST',
                body: formData
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentFilename = data.video_info.filename;
                    document.getElementById('uploadStatus').innerHTML = 
                        '<div class="alert alert-success">上传成功: ' + data.video_info.filename + '</div>';
                } else {
                    document.getElementById('uploadStatus').innerHTML = 
                        '<div class="alert alert-error">上传失败: ' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('uploadStatus').innerHTML = 
                    '<div class="alert alert-error">上传错误: ' + error + '</div>';
            });
        }

        function startTest() {
            if (!currentFilename) {
                alert('请先上传视频文件');
                return;
            }
            
            const testType = document.getElementById('testType').value;
            
            fetch('/api/test_video', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    filename: currentFilename,
                    test_type: testType
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentSessionId = data.session_id;
                    document.getElementById('testStatus').innerHTML = 
                        '<div class="alert alert-success">检测已启动，会话ID: ' + data.session_id + '</div>';
                    monitorTest();
                } else {
                    document.getElementById('testStatus').innerHTML = 
                        '<div class="alert alert-error">启动失败: ' + data.error + '</div>';
                }
            });
        }

        function demoTest() {
            const testType = document.getElementById('testType').value;
            
            document.getElementById('testStatus').innerHTML = 
                '<div class="alert alert-warning">演示测试进行中...</div>';
            
            fetch('/api/demo_test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    test_type: testType,
                    frame_count: 50
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('testStatus').innerHTML = 
                    '<div class="alert alert-success">演示测试完成</div>';
                displayResults(data);
            });
        }

        function monitorTest() {
            if (!currentSessionId) return;
            
            const checkStatus = () => {
                fetch('/api/test_status/' + currentSessionId)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'completed') {
                        document.getElementById('testStatus').innerHTML = 
                            '<div class="alert alert-success">检测完成</div>';
                        
                        // 获取结果
                        fetch('/api/test_result/' + currentSessionId)
                        .then(response => response.json())
                        .then(result => displayResults(result));
                        
                    } else if (data.status === 'failed') {
                        document.getElementById('testStatus').innerHTML = 
                            '<div class="alert alert-error">检测失败: ' + data.error + '</div>';
                    } else {
                        setTimeout(checkStatus, 2000); // 2秒后重新检查
                    }
                });
            };
            
            checkStatus();
        }

        function displayResults(data) {
            // 更新统计数据
            const detections = data.detections || [];
            const alerts = data.alerts || [];
            
            document.getElementById('totalDetections').textContent = detections.length;
            document.getElementById('totalAlerts').textContent = alerts.length;
            
            let avgConf = 0;
            if (detections.length > 0) {
                avgConf = detections.reduce((sum, d) => sum + (d.confidence || 0), 0) / detections.length;
            }
            document.getElementById('avgConfidence').textContent = Math.round(avgConf * 100) + '%';
            
            // 显示详细结果
            let resultHtml = '<h3>检测详情:</h3>';
            
            detections.forEach((detection, index) => {
                resultHtml += `
                    <div class="alert alert-success">
                        <strong>${detection.type.toUpperCase()}</strong> - 
                        帧${detection.frame_number} - 
                        置信度: ${(detection.confidence * 100).toFixed(1)}%
                    </div>
                `;
            });
            
            if (alerts.length > 0) {
                resultHtml += '<h3>告警信息:</h3>';
                alerts.forEach(alert => {
                    resultHtml += `
                        <div class="alert alert-warning">
                            <strong>${alert.severity}</strong>: ${alert.message}
                        </div>
                    `;
                });
            }
            
            document.getElementById('resultArea').innerHTML = resultHtml;
        }

        function stopTest() {
            if (currentSessionId) {
                fetch('/api/stop_realtime/' + currentSessionId, {method: 'POST'})
                .then(response => response.json())
                .then(data => {
                    document.getElementById('testStatus').innerHTML = 
                        '<div class="alert alert-warning">测试已停止</div>';
                });
            }
        }
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🎬 启动视频测试API服务...")
    print("📍 访问地址: http://localhost:5556")
    print("📤 支持上传视频格式: MP4, AVI, MOV, MKV, WMV")
    print("🔥 检测功能: 跌倒检测 + 火焰烟雾检测")
    print("📊 提供实时告警和统计分析")
    
    app.run(host='0.0.0.0', port=5556, debug=False)