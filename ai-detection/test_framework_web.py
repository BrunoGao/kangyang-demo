#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试框架Web界面
提供友好的Web界面来使用测试框架功能
"""

from flask import Flask, request, jsonify, render_template_string
import os
import json
import threading
import time
from datetime import datetime
from werkzeug.utils import secure_filename

# 导入测试框架
from test_framework import TestSuiteManager, TestCase, quick_test

app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-framework-2024'
app.config['MAX_CONTENT_LENGTH'] = 500 * 1024 * 1024  # 500MB

# 全局测试套件管理器
suite_manager = TestSuiteManager()
active_test_sessions = {}

@app.route('/')
def index():
    """测试框架主页"""
    return render_template_string(TEST_FRAMEWORK_HTML)

@app.route('/api/test_cases')
def list_test_cases():
    """获取测试用例列表"""
    try:
        difficulty = request.args.get('difficulty')
        tags = request.args.getlist('tags')
        
        test_cases = suite_manager.list_test_cases(difficulty=difficulty, tags=tags if tags else None)
        
        # 转换为字典格式
        cases_data = []
        for case in test_cases:
            case_dict = {
                'id': case.id,
                'name': case.name,
                'description': case.description,
                'video_path': case.video_path,
                'expected_detections': case.expected_detections,
                'difficulty': case.difficulty,
                'duration_seconds': case.duration_seconds,
                'tags': case.tags or []
            }
            cases_data.append(case_dict)
        
        return jsonify({
            'test_cases': cases_data,
            'total': len(cases_data)
        })
    
    except Exception as e:
        return jsonify({'error': f'获取测试用例失败: {str(e)}'}), 500

@app.route('/api/test_case/<test_id>')
def get_test_case_detail(test_id):
    """获取测试用例详情"""
    try:
        test_case = suite_manager.get_test_case(test_id)
        
        if not test_case:
            return jsonify({'error': '测试用例不存在'}), 404
        
        # 获取历史测试结果
        history = suite_manager.db_manager.get_test_history(test_id, limit=5)
        
        return jsonify({
            'test_case': {
                'id': test_case.id,
                'name': test_case.name,
                'description': test_case.description,
                'video_path': test_case.video_path,
                'expected_detections': test_case.expected_detections,
                'difficulty': test_case.difficulty,
                'duration_seconds': test_case.duration_seconds,
                'tags': test_case.tags or []
            },
            'history': history
        })
    
    except Exception as e:
        return jsonify({'error': f'获取测试用例详情失败: {str(e)}'}), 500

@app.route('/api/add_test_case', methods=['POST'])
def add_test_case():
    """添加新测试用例"""
    try:
        data = request.json
        
        test_case = TestCase(
            id=data['id'],
            name=data['name'],
            description=data.get('description', ''),
            video_path=data['video_path'],
            expected_detections=data['expected_detections'],
            difficulty=data.get('difficulty', 'medium'),
            duration_seconds=int(data.get('duration_seconds', 60)),
            tags=data.get('tags', [])
        )
        
        suite_manager.add_test_case(test_case)
        
        return jsonify({
            'success': True,
            'message': f'测试用例 {test_case.name} 添加成功',
            'test_case_id': test_case.id
        })
    
    except Exception as e:
        return jsonify({'error': f'添加测试用例失败: {str(e)}'}), 500

@app.route('/api/run_single_test', methods=['POST'])
def run_single_test():
    """运行单个测试用例"""
    try:
        data = request.json
        test_id = data.get('test_id')
        
        if not test_id:
            return jsonify({'error': '测试用例ID不能为空'}), 400
        
        test_case = suite_manager.get_test_case(test_id)
        if not test_case:
            return jsonify({'error': '测试用例不存在'}), 404
        
        # 创建测试会话
        session_id = f"single_test_{int(time.time())}"
        
        def run_test():
            try:
                active_test_sessions[session_id] = {
                    'status': 'running',
                    'test_id': test_id,
                    'start_time': datetime.now().isoformat(),
                    'progress': 0
                }
                
                # 执行测试
                def progress_callback(progress, frame_num, detections, alerts):
                    active_test_sessions[session_id]['progress'] = progress
                    active_test_sessions[session_id]['current_frame'] = frame_num
                    active_test_sessions[session_id]['current_detections'] = len(detections)
                    active_test_sessions[session_id]['current_alerts'] = len(alerts)
                
                result = suite_manager.executor.execute_test_case(test_case, progress_callback)
                
                active_test_sessions[session_id]['status'] = 'completed'
                active_test_sessions[session_id]['result'] = {
                    'test_case_id': result.test_case_id,
                    'session_id': result.session_id,
                    'passed': result.passed,
                    'detections': result.detections,
                    'alerts': result.alerts,
                    'statistics': result.statistics,
                    'performance_metrics': result.performance_metrics,
                    'error_message': result.error_message
                }
                
            except Exception as e:
                active_test_sessions[session_id]['status'] = 'failed'
                active_test_sessions[session_id]['error'] = str(e)
        
        # 启动测试线程
        thread = threading.Thread(target=run_test)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'测试已启动: {test_case.name}'
        })
    
    except Exception as e:
        return jsonify({'error': f'启动测试失败: {str(e)}'}), 500

@app.route('/api/run_test_suite', methods=['POST'])
def run_test_suite():
    """运行测试套件"""
    try:
        data = request.json
        test_ids = data.get('test_ids', [])
        difficulty = data.get('difficulty')
        tags = data.get('tags', [])
        
        # 如果没有指定测试用例，根据条件筛选
        if not test_ids:
            test_cases = suite_manager.list_test_cases(difficulty=difficulty, tags=tags if tags else None)
            test_ids = [case.id for case in test_cases]
        
        if not test_ids:
            return jsonify({'error': '没有找到匹配的测试用例'}), 400
        
        # 创建测试会话
        session_id = f"suite_test_{int(time.time())}"
        
        def run_suite():
            try:
                active_test_sessions[session_id] = {
                    'status': 'running',
                    'test_ids': test_ids,
                    'start_time': datetime.now().isoformat(),
                    'progress': 0,
                    'current_test': '',
                    'completed_tests': 0,
                    'total_tests': len(test_ids)
                }
                
                def progress_callback(progress, message):
                    active_test_sessions[session_id]['progress'] = progress
                    active_test_sessions[session_id]['current_message'] = message
                
                # 运行测试套件
                results = suite_manager.run_test_suite(test_ids, progress_callback)
                
                # 生成报告
                report = suite_manager.generate_report(results)
                
                active_test_sessions[session_id]['status'] = 'completed'
                active_test_sessions[session_id]['results'] = {
                    test_id: {
                        'passed': result.passed,
                        'detections': len(result.detections),
                        'alerts': len(result.alerts),
                        'processing_time': result.performance_metrics.get('total_execution_time', 0),
                        'error_message': result.error_message
                    }
                    for test_id, result in results.items()
                }
                active_test_sessions[session_id]['report'] = report
                
            except Exception as e:
                active_test_sessions[session_id]['status'] = 'failed'
                active_test_sessions[session_id]['error'] = str(e)
        
        # 启动测试线程
        thread = threading.Thread(target=run_suite)
        thread.daemon = True
        thread.start()
        
        return jsonify({
            'success': True,
            'session_id': session_id,
            'message': f'测试套件已启动，包含 {len(test_ids)} 个测试用例'
        })
    
    except Exception as e:
        return jsonify({'error': f'启动测试套件失败: {str(e)}'}), 500

@app.route('/api/test_session/<session_id>')
def get_test_session_status(session_id):
    """获取测试会话状态"""
    if session_id not in active_test_sessions:
        return jsonify({'error': '测试会话不存在'}), 404
    
    return jsonify(active_test_sessions[session_id])

@app.route('/api/quick_test', methods=['POST'])
def api_quick_test():
    """快速测试API"""
    try:
        data = request.json
        test_type = data.get('test_type', 'all')
        difficulty = data.get('difficulty', 'easy')
        
        result = quick_test(test_type=test_type, difficulty=difficulty)
        return jsonify(result)
    
    except Exception as e:
        return jsonify({'error': f'快速测试失败: {str(e)}'}), 500

@app.route('/api/statistics')
def get_statistics():
    """获取统计信息"""
    try:
        # 获取数据库中的统计信息
        import sqlite3
        conn = sqlite3.connect('test_results.db')
        cursor = conn.cursor()
        
        # 总测试次数
        cursor.execute('SELECT COUNT(*) FROM test_results')
        total_tests = cursor.fetchone()[0]
        
        # 通过的测试次数
        cursor.execute('SELECT COUNT(*) FROM test_results WHERE passed = 1')
        passed_tests = cursor.fetchone()[0]
        
        # 最近24小时的测试
        cursor.execute('''
            SELECT COUNT(*) FROM test_results 
            WHERE created_at > datetime('now', '-24 hours')
        ''')
        recent_tests = cursor.fetchone()[0]
        
        # 按难度统计
        cursor.execute('''
            SELECT tc.difficulty, COUNT(*), SUM(tr.passed)
            FROM test_results tr
            JOIN test_cases tc ON tr.test_case_id = tc.id
            GROUP BY tc.difficulty
        ''')
        difficulty_stats = {}
        for row in cursor.fetchall():
            difficulty, total, passed = row
            difficulty_stats[difficulty] = {
                'total': total,
                'passed': passed or 0,
                'pass_rate': (passed or 0) / total if total > 0 else 0
            }
        
        conn.close()
        
        return jsonify({
            'total_tests': total_tests,
            'passed_tests': passed_tests,
            'failed_tests': total_tests - passed_tests,
            'overall_pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
            'recent_24h_tests': recent_tests,
            'difficulty_breakdown': difficulty_stats
        })
    
    except Exception as e:
        return jsonify({'error': f'获取统计信息失败: {str(e)}'}), 500

# HTML模板
TEST_FRAMEWORK_HTML = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>🧪 AI检测算法测试框架</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            color: white;
            padding: 20px;
        }
        .container { max-width: 1400px; margin: 0 auto; }
        .header { text-align: center; margin-bottom: 40px; }
        .header h1 { font-size: 2.8em; margin-bottom: 10px; text-shadow: 2px 2px 4px rgba(0,0,0,0.3); }
        .section {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 15px;
            padding: 30px;
            margin-bottom: 30px;
            backdrop-filter: blur(10px);
            box-shadow: 0 8px 32px 0 rgba(31, 38, 135, 0.37);
            border: 1px solid rgba(255, 255, 255, 0.18);
        }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(350px, 1fr)); gap: 20px; }
        .btn {
            background: rgba(255, 255, 255, 0.2);
            color: white;
            border: none;
            padding: 12px 24px;
            border-radius: 25px;
            cursor: pointer;
            font-size: 16px;
            margin: 10px 5px;
            transition: all 0.3s ease;
            border: 1px solid rgba(255, 255, 255, 0.3);
        }
        .btn:hover { 
            background: rgba(255, 255, 255, 0.3);
            transform: translateY(-2px);
            box-shadow: 0 4px 15px rgba(0,0,0,0.2);
        }
        .btn-primary { background: linear-gradient(45deg, #4CAF50, #45a049); }
        .btn-primary:hover { background: linear-gradient(45deg, #45a049, #4CAF50); }
        .btn-warning { background: linear-gradient(45deg, #FF9800, #F57C00); }
        .btn-warning:hover { background: linear-gradient(45deg, #F57C00, #FF9800); }
        .btn-danger { background: linear-gradient(45deg, #f44336, #da190b); }
        .btn-danger:hover { background: linear-gradient(45deg, #da190b, #f44336); }
        .btn-info { background: linear-gradient(45deg, #2196F3, #1976D2); }
        .btn-info:hover { background: linear-gradient(45deg, #1976D2, #2196F3); }
        
        .alert {
            padding: 15px;
            margin: 10px 0;
            border-radius: 8px;
            border-left: 4px solid;
            animation: fadeIn 0.3s ease-in;
        }
        .alert-success { background: rgba(76, 175, 80, 0.3); border-color: #4CAF50; }
        .alert-warning { background: rgba(255, 152, 0, 0.3); border-color: #FF9800; }
        .alert-error { background: rgba(244, 67, 54, 0.3); border-color: #f44336; }
        .alert-info { background: rgba(33, 150, 243, 0.3); border-color: #2196F3; }
        
        .stats-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; }
        .stat-card {
            background: rgba(255, 255, 255, 0.15);
            border-radius: 12px;
            padding: 20px;
            text-align: center;
            transition: transform 0.3s ease;
        }
        .stat-card:hover { transform: scale(1.05); }
        .stat-number { font-size: 2.2em; font-weight: bold; color: #4CAF50; margin-bottom: 5px; }
        .stat-label { font-size: 0.9em; opacity: 0.8; }
        
        .test-case-card {
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            padding: 20px;
            margin: 15px 0;
            border-left: 4px solid;
            transition: all 0.3s ease;
        }
        .test-case-card:hover { 
            background: rgba(255, 255, 255, 0.2);
            transform: translateX(5px);
        }
        .test-case-card.easy { border-color: #4CAF50; }
        .test-case-card.medium { border-color: #FF9800; }
        .test-case-card.hard { border-color: #f44336; }
        .test-case-card.very_hard { border-color: #9C27B0; }
        
        .difficulty-badge { 
            padding: 5px 12px; 
            border-radius: 15px; 
            font-size: 0.8em; 
            display: inline-block;
            margin: 5px;
        }
        .difficulty-easy { background: #4CAF50; }
        .difficulty-medium { background: #FF9800; }
        .difficulty-hard { background: #f44336; }
        .difficulty-very_hard { background: #9C27B0; }
        
        .progress {
            background: rgba(255, 255, 255, 0.2);
            border-radius: 10px;
            height: 25px;
            margin: 15px 0;
            overflow: hidden;
        }
        .progress-bar {
            background: linear-gradient(45deg, #4CAF50, #45a049);
            height: 100%;
            width: 0%;
            transition: width 0.5s ease;
            border-radius: 10px;
            display: flex;
            align-items: center;
            justify-content: center;
            color: white;
            font-weight: bold;
            font-size: 0.9em;
        }
        
        .form-group { margin: 15px 0; }
        .form-group label { display: block; margin-bottom: 5px; font-weight: bold; }
        .form-control {
            width: 100%;
            padding: 12px;
            border: 1px solid rgba(255, 255, 255, 0.3);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.1);
            color: white;
            font-size: 16px;
        }
        .form-control::placeholder { color: rgba(255, 255, 255, 0.7); }
        .form-control:focus {
            outline: none;
            border-color: #4CAF50;
            background: rgba(255, 255, 255, 0.15);
        }
        
        select.form-control option { background: #333; color: white; }
        
        .tag { 
            background: rgba(255, 255, 255, 0.2);
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin: 2px;
            display: inline-block;
        }
        
        .test-result {
            background: rgba(0, 0, 0, 0.3);
            border-radius: 10px;
            padding: 20px;
            margin-top: 20px;
            max-height: 500px;
            overflow-y: auto;
        }
        
        .loading {
            display: inline-block;
            width: 20px;
            height: 20px;
            border: 3px solid rgba(255, 255, 255, 0.3);
            border-radius: 50%;
            border-top-color: #4CAF50;
            animation: spin 1s ease-in-out infinite;
        }
        
        @keyframes fadeIn {
            from { opacity: 0; transform: translateY(-10px); }
            to { opacity: 1; transform: translateY(0); }
        }
        
        @keyframes spin {
            to { transform: rotate(360deg); }
        }
        
        .hidden { display: none; }
        
        .tabs {
            display: flex;
            background: rgba(255, 255, 255, 0.1);
            border-radius: 10px;
            margin-bottom: 20px;
        }
        .tab {
            flex: 1;
            padding: 15px;
            text-align: center;
            cursor: pointer;
            border-radius: 10px;
            transition: background 0.3s ease;
        }
        .tab.active { background: rgba(255, 255, 255, 0.2); }
        .tab:hover { background: rgba(255, 255, 255, 0.15); }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🧪 AI检测算法测试框架</h1>
            <p>专业的跌倒检测和火焰检测算法测试平台，提供完整的测试用例管理和性能评估</p>
        </div>

        <!-- 统计概览 -->
        <div class="section">
            <h2>📊 测试统计概览</h2>
            <div class="stats-grid" id="statsGrid">
                <div class="stat-card">
                    <div class="stat-number" id="totalTests">0</div>
                    <div class="stat-label">总测试次数</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="passedTests">0</div>
                    <div class="stat-label">通过测试</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="passRate">0%</div>
                    <div class="stat-label">通过率</div>
                </div>
                <div class="stat-card">
                    <div class="stat-number" id="recentTests">0</div>
                    <div class="stat-label">24小时内测试</div>
                </div>
            </div>
        </div>

        <!-- 主功能区 -->
        <div class="tabs">
            <div class="tab active" onclick="showTab('quick-test')">⚡ 快速测试</div>
            <div class="tab" onclick="showTab('test-cases')">📋 测试用例</div>
            <div class="tab" onclick="showTab('test-suite')">🧪 测试套件</div>
            <div class="tab" onclick="showTab('add-case')">➕ 添加用例</div>
        </div>

        <!-- 快速测试 -->
        <div id="quick-test" class="section tab-content">
            <h2>⚡ 快速测试</h2>
            <div class="grid">
                <div>
                    <h3>测试配置</h3>
                    <div class="form-group">
                        <label>检测类型</label>
                        <select id="quickTestType" class="form-control">
                            <option value="all">全部检测</option>
                            <option value="fall">仅跌倒检测</option>
                            <option value="fire">仅火焰检测</option>
                            <option value="smoke">仅烟雾检测</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>难度等级</label>
                        <select id="quickTestDifficulty" class="form-control">
                            <option value="easy">简单</option>
                            <option value="medium">中等</option>
                            <option value="hard">困难</option>
                            <option value="very_hard">非常困难</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="runQuickTest()">🚀 开始快速测试</button>
                </div>
                <div>
                    <h3>测试状态</h3>
                    <div id="quickTestStatus">等待启动测试...</div>
                    <div id="quickTestProgress" class="hidden">
                        <div class="progress">
                            <div class="progress-bar" id="quickProgressBar">0%</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="test-result" id="quickTestResult"></div>
        </div>

        <!-- 测试用例管理 -->
        <div id="test-cases" class="section tab-content hidden">
            <h2>📋 测试用例管理</h2>
            <div class="form-group">
                <label>筛选条件</label>
                <div style="display: flex; gap: 10px; flex-wrap: wrap;">
                    <select id="filterDifficulty" class="form-control" style="flex: 1; min-width: 150px;">
                        <option value="">全部难度</option>
                        <option value="easy">简单</option>
                        <option value="medium">中等</option>
                        <option value="hard">困难</option>
                        <option value="very_hard">非常困难</option>
                    </select>
                    <button class="btn" onclick="loadTestCases()">🔄 刷新列表</button>
                </div>
            </div>
            <div id="testCasesList">加载中...</div>
        </div>

        <!-- 测试套件 -->
        <div id="test-suite" class="section tab-content hidden">
            <h2>🧪 测试套件运行</h2>
            <div class="grid">
                <div>
                    <h3>套件配置</h3>
                    <div class="form-group">
                        <label>测试范围</label>
                        <select id="suiteTestType" class="form-control">
                            <option value="all">全部测试</option>
                            <option value="fall">仅跌倒测试</option>
                            <option value="fire">仅火焰测试</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>难度筛选</label>
                        <select id="suiteDifficulty" class="form-control">
                            <option value="">不限难度</option>
                            <option value="easy">简单</option>
                            <option value="medium">中等</option>
                            <option value="hard">困难</option>
                            <option value="very_hard">非常困难</option>
                        </select>
                    </div>
                    <button class="btn btn-primary" onclick="runTestSuite()">🚀 运行测试套件</button>
                </div>
                <div>
                    <h3>执行状态</h3>
                    <div id="suiteTestStatus">等待启动测试套件...</div>
                    <div id="suiteTestProgress" class="hidden">
                        <div class="progress">
                            <div class="progress-bar" id="suiteProgressBar">0%</div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="test-result" id="suiteTestResult"></div>
        </div>

        <!-- 添加测试用例 -->
        <div id="add-case" class="section tab-content hidden">
            <h2>➕ 添加新测试用例</h2>
            <div class="grid">
                <div>
                    <div class="form-group">
                        <label>用例ID</label>
                        <input type="text" id="newCaseId" class="form-control" placeholder="例: fall_custom_001">
                    </div>
                    <div class="form-group">
                        <label>用例名称</label>
                        <input type="text" id="newCaseName" class="form-control" placeholder="例: 客厅跌倒检测">
                    </div>
                    <div class="form-group">
                        <label>描述</label>
                        <textarea id="newCaseDescription" class="form-control" rows="3" placeholder="详细描述测试场景..."></textarea>
                    </div>
                    <div class="form-group">
                        <label>视频路径</label>
                        <input type="text" id="newCaseVideoPath" class="form-control" placeholder="例: test_videos/custom_fall.mp4">
                    </div>
                </div>
                <div>
                    <div class="form-group">
                        <label>预期检测类型</label>
                        <div>
                            <label><input type="checkbox" id="expectedFall"> 跌倒检测</label><br>
                            <label><input type="checkbox" id="expectedFire"> 火焰检测</label><br>
                            <label><input type="checkbox" id="expectedSmoke"> 烟雾检测</label>
                        </div>
                    </div>
                    <div class="form-group">
                        <label>难度等级</label>
                        <select id="newCaseDifficulty" class="form-control">
                            <option value="easy">简单</option>
                            <option value="medium">中等</option>
                            <option value="hard">困难</option>
                            <option value="very_hard">非常困难</option>
                        </select>
                    </div>
                    <div class="form-group">
                        <label>视频时长(秒)</label>
                        <input type="number" id="newCaseDuration" class="form-control" value="60" min="1">
                    </div>
                    <div class="form-group">
                        <label>标签 (用逗号分隔)</label>
                        <input type="text" id="newCaseTags" class="form-control" placeholder="例: fall, elderly, indoor">
                    </div>
                </div>
            </div>
            <div style="text-align: center; margin-top: 20px;">
                <button class="btn btn-primary" onclick="addTestCase()">✅ 添加测试用例</button>
                <button class="btn" onclick="clearNewCaseForm()">🗑️ 清空表单</button>
            </div>
            <div id="addCaseStatus"></div>
        </div>
    </div>

    <script>
        let currentSession = null;
        let testCases = [];

        // 页面加载完成后初始化
        window.onload = function() {
            loadStatistics();
            loadTestCases();
        };

        // Tab切换
        function showTab(tabName) {
            // 隐藏所有内容
            document.querySelectorAll('.tab-content').forEach(el => el.classList.add('hidden'));
            document.querySelectorAll('.tab').forEach(el => el.classList.remove('active'));
            
            // 显示选中内容
            document.getElementById(tabName).classList.remove('hidden');
            document.querySelector(`[onclick="showTab('${tabName}')"]`).classList.add('active');
        }

        // 加载统计信息
        function loadStatistics() {
            fetch('/api/statistics')
            .then(response => response.json())
            .then(data => {
                if (!data.error) {
                    document.getElementById('totalTests').textContent = data.total_tests;
                    document.getElementById('passedTests').textContent = data.passed_tests;
                    document.getElementById('passRate').textContent = 
                        Math.round(data.overall_pass_rate * 100) + '%';
                    document.getElementById('recentTests').textContent = data.recent_24h_tests;
                }
            })
            .catch(error => console.error('加载统计信息失败:', error));
        }

        // 加载测试用例
        function loadTestCases() {
            const difficulty = document.getElementById('filterDifficulty').value;
            let url = '/api/test_cases';
            if (difficulty) {
                url += `?difficulty=${difficulty}`;
            }

            fetch(url)
            .then(response => response.json())
            .then(data => {
                testCases = data.test_cases || [];
                displayTestCases(testCases);
            })
            .catch(error => {
                document.getElementById('testCasesList').innerHTML = 
                    '<div class="alert alert-error">加载测试用例失败: ' + error + '</div>';
            });
        }

        // 显示测试用例列表
        function displayTestCases(cases) {
            const container = document.getElementById('testCasesList');
            
            if (cases.length === 0) {
                container.innerHTML = '<div class="alert alert-info">没有找到匹配的测试用例</div>';
                return;
            }

            let html = '';
            cases.forEach(testCase => {
                html += `
                    <div class="test-case-card ${testCase.difficulty}">
                        <div style="display: flex; justify-content: between; align-items: center;">
                            <div style="flex: 1;">
                                <h4>${testCase.name}</h4>
                                <p>${testCase.description}</p>
                                <div style="margin-top: 10px;">
                                    <span class="difficulty-badge difficulty-${testCase.difficulty}">${testCase.difficulty}</span>
                                    ${testCase.expected_detections.map(type => `<span class="tag">${type}</span>`).join('')}
                                    <span class="tag">⏱️ ${testCase.duration_seconds}s</span>
                                </div>
                                <small style="opacity: 0.7;">视频: ${testCase.video_path}</small>
                            </div>
                            <div style="margin-left: 20px;">
                                <button class="btn btn-info" onclick="runSingleTest('${testCase.id}')">🧪 单独测试</button>
                                <button class="btn" onclick="viewTestCaseDetail('${testCase.id}')">📊 查看详情</button>
                            </div>
                        </div>
                    </div>
                `;
            });

            container.innerHTML = html;
        }

        // 运行快速测试
        function runQuickTest() {
            const testType = document.getElementById('quickTestType').value;
            const difficulty = document.getElementById('quickTestDifficulty').value;

            document.getElementById('quickTestStatus').innerHTML = 
                '<div class="alert alert-info"><div class="loading"></div> 快速测试进行中...</div>';
            
            document.getElementById('quickTestProgress').classList.remove('hidden');
            document.getElementById('quickProgressBar').style.width = '10%';
            document.getElementById('quickProgressBar').textContent = '10%';

            fetch('/api/quick_test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    test_type: testType,
                    difficulty: difficulty
                })
            })
            .then(response => response.json())
            .then(data => {
                document.getElementById('quickProgressBar').style.width = '100%';
                document.getElementById('quickProgressBar').textContent = '100%';
                
                setTimeout(() => {
                    document.getElementById('quickTestProgress').classList.add('hidden');
                }, 1000);

                if (data.error) {
                    document.getElementById('quickTestStatus').innerHTML = 
                        '<div class="alert alert-error">测试失败: ' + data.error + '</div>';
                } else {
                    document.getElementById('quickTestStatus').innerHTML = 
                        '<div class="alert alert-success">✅ ' + data.message + '</div>';
                    displayTestReport(data.report, 'quickTestResult');
                }
            })
            .catch(error => {
                document.getElementById('quickTestStatus').innerHTML = 
                    '<div class="alert alert-error">网络错误: ' + error + '</div>';
            });
        }

        // 运行单个测试
        function runSingleTest(testId) {
            fetch('/api/run_single_test', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({test_id: testId})
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentSession = data.session_id;
                    monitorTestSession(data.session_id, 'single');
                } else {
                    alert('启动测试失败: ' + data.error);
                }
            })
            .catch(error => alert('网络错误: ' + error));
        }

        // 运行测试套件
        function runTestSuite() {
            const difficulty = document.getElementById('suiteDifficulty').value;
            const testType = document.getElementById('suiteTestType').value;

            document.getElementById('suiteTestStatus').innerHTML = 
                '<div class="alert alert-info"><div class="loading"></div> 启动测试套件...</div>';

            fetch('/api/run_test_suite', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({
                    difficulty: difficulty || undefined,
                    tags: testType === 'all' ? [] : [testType]
                })
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    currentSession = data.session_id;
                    document.getElementById('suiteTestStatus').innerHTML = 
                        '<div class="alert alert-success">✅ ' + data.message + '</div>';
                    document.getElementById('suiteTestProgress').classList.remove('hidden');
                    monitorTestSession(data.session_id, 'suite');
                } else {
                    document.getElementById('suiteTestStatus').innerHTML = 
                        '<div class="alert alert-error">启动失败: ' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('suiteTestStatus').innerHTML = 
                    '<div class="alert alert-error">网络错误: ' + error + '</div>';
            });
        }

        // 监控测试会话
        function monitorTestSession(sessionId, type) {
            const checkStatus = () => {
                fetch(`/api/test_session/${sessionId}`)
                .then(response => response.json())
                .then(data => {
                    if (data.status === 'completed') {
                        if (type === 'suite') {
                            document.getElementById('suiteTestStatus').innerHTML = 
                                '<div class="alert alert-success">测试套件完成</div>';
                            document.getElementById('suiteTestProgress').classList.add('hidden');
                            displaySuiteResults(data);
                        }
                    } else if (data.status === 'failed') {
                        const statusElement = type === 'suite' ? 
                            document.getElementById('suiteTestStatus') : 
                            document.getElementById('quickTestStatus');
                        statusElement.innerHTML = 
                            '<div class="alert alert-error">测试失败: ' + data.error + '</div>';
                    } else if (data.status === 'running') {
                        if (type === 'suite' && data.progress) {
                            const progressBar = document.getElementById('suiteProgressBar');
                            progressBar.style.width = data.progress + '%';
                            progressBar.textContent = Math.round(data.progress) + '%';
                        }
                        setTimeout(checkStatus, 2000);
                    } else {
                        setTimeout(checkStatus, 1000);
                    }
                })
                .catch(error => {
                    console.error('监控会话失败:', error);
                    setTimeout(checkStatus, 5000);
                });
            };

            checkStatus();
        }

        // 显示测试报告
        function displayTestReport(report, containerId) {
            const container = document.getElementById(containerId);
            const summary = report.summary;

            let html = `
                <h3>📊 测试总结</h3>
                <div class="stats-grid">
                    <div class="stat-card">
                        <div class="stat-number">${summary.total_tests}</div>
                        <div class="stat-label">总测试数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${summary.passed_tests}</div>
                        <div class="stat-label">通过数</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${Math.round(summary.pass_rate * 100)}%</div>
                        <div class="stat-label">通过率</div>
                    </div>
                    <div class="stat-card">
                        <div class="stat-number">${summary.avg_processing_time.toFixed(2)}s</div>
                        <div class="stat-label">平均处理时间</div>
                    </div>
                </div>
            `;

            // 难度分解
            if (report.difficulty_breakdown) {
                html += '<h4>🎯 难度分解</h4>';
                Object.keys(report.difficulty_breakdown).forEach(difficulty => {
                    const stats = report.difficulty_breakdown[difficulty];
                    html += `
                        <div class="alert alert-info">
                            <strong>${difficulty.toUpperCase()}</strong>: 
                            ${stats.passed}/${stats.total} 通过 
                            (${Math.round((stats.passed/stats.total)*100)}%)
                        </div>
                    `;
                });
            }

            // 失败测试
            if (report.failed_tests && report.failed_tests.length > 0) {
                html += '<h4>❌ 失败测试</h4>';
                report.failed_tests.forEach(failed => {
                    html += `
                        <div class="alert alert-error">
                            <strong>${failed.test_name}</strong><br>
                            错误: ${failed.error_message || '未知错误'}
                        </div>
                    `;
                });
            }

            container.innerHTML = html;
        }

        // 显示套件测试结果
        function displaySuiteResults(sessionData) {
            const container = document.getElementById('suiteTestResult');
            
            if (sessionData.report) {
                displayTestReport(sessionData.report, 'suiteTestResult');
            } else if (sessionData.results) {
                let html = '<h3>📊 详细结果</h3>';
                Object.keys(sessionData.results).forEach(testId => {
                    const result = sessionData.results[testId];
                    const testCase = testCases.find(tc => tc.id === testId);
                    
                    html += `
                        <div class="test-case-card ${result.passed ? 'easy' : 'hard'}">
                            <h4>${testCase ? testCase.name : testId} ${result.passed ? '✅' : '❌'}</h4>
                            <p>检测: ${result.detections} | 告警: ${result.alerts} | 
                               处理时间: ${result.processing_time.toFixed(2)}s</p>
                            ${result.error_message ? '<p style="color: #f44336;">错误: ' + result.error_message + '</p>' : ''}
                        </div>
                    `;
                });
                container.innerHTML = html;
            }
        }

        // 添加测试用例
        function addTestCase() {
            const expectedDetections = [];
            if (document.getElementById('expectedFall').checked) expectedDetections.push('fall');
            if (document.getElementById('expectedFire').checked) expectedDetections.push('fire');
            if (document.getElementById('expectedSmoke').checked) expectedDetections.push('smoke');

            if (expectedDetections.length === 0) {
                document.getElementById('addCaseStatus').innerHTML = 
                    '<div class="alert alert-error">请至少选择一种预期检测类型</div>';
                return;
            }

            const tags = document.getElementById('newCaseTags').value.split(',')
                .map(tag => tag.trim()).filter(tag => tag.length > 0);

            const testCaseData = {
                id: document.getElementById('newCaseId').value,
                name: document.getElementById('newCaseName').value,
                description: document.getElementById('newCaseDescription').value,
                video_path: document.getElementById('newCaseVideoPath').value,
                expected_detections: expectedDetections,
                difficulty: document.getElementById('newCaseDifficulty').value,
                duration_seconds: parseInt(document.getElementById('newCaseDuration').value),
                tags: tags
            };

            if (!testCaseData.id || !testCaseData.name || !testCaseData.video_path) {
                document.getElementById('addCaseStatus').innerHTML = 
                    '<div class="alert alert-error">请填写必填字段：用例ID、名称、视频路径</div>';
                return;
            }

            fetch('/api/add_test_case', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(testCaseData)
            })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    document.getElementById('addCaseStatus').innerHTML = 
                        '<div class="alert alert-success">✅ ' + data.message + '</div>';
                    clearNewCaseForm();
                    // 刷新测试用例列表
                    loadTestCases();
                } else {
                    document.getElementById('addCaseStatus').innerHTML = 
                        '<div class="alert alert-error">添加失败: ' + data.error + '</div>';
                }
            })
            .catch(error => {
                document.getElementById('addCaseStatus').innerHTML = 
                    '<div class="alert alert-error">网络错误: ' + error + '</div>';
            });
        }

        // 清空新用例表单
        function clearNewCaseForm() {
            document.getElementById('newCaseId').value = '';
            document.getElementById('newCaseName').value = '';
            document.getElementById('newCaseDescription').value = '';
            document.getElementById('newCaseVideoPath').value = '';
            document.getElementById('expectedFall').checked = false;
            document.getElementById('expectedFire').checked = false;
            document.getElementById('expectedSmoke').checked = false;
            document.getElementById('newCaseDifficulty').value = 'medium';
            document.getElementById('newCaseDuration').value = '60';
            document.getElementById('newCaseTags').value = '';
        }

        // 查看测试用例详情
        function viewTestCaseDetail(testId) {
            fetch(`/api/test_case/${testId}`)
            .then(response => response.json())
            .then(data => {
                if (data.error) {
                    alert('获取详情失败: ' + data.error);
                    return;
                }
                
                // 创建详情弹窗内容
                let historyHtml = '<h4>📈 历史记录</h4>';
                if (data.history && data.history.length > 0) {
                    data.history.forEach(record => {
                        const detections = JSON.parse(record.detections || '[]');
                        const alerts = JSON.parse(record.alerts || '[]');
                        historyHtml += `
                            <div class="alert ${record.passed ? 'alert-success' : 'alert-error'}">
                                <strong>${record.passed ? '✅ 通过' : '❌ 失败'}</strong> - 
                                ${record.start_time}<br>
                                检测: ${detections.length} | 告警: ${alerts.length}
                                ${record.error_message ? '<br>错误: ' + record.error_message : ''}
                            </div>
                        `;
                    });
                } else {
                    historyHtml += '<p>暂无历史记录</p>';
                }
                
                alert(`测试用例详情：\n\n名称: ${data.test_case.name}\n描述: ${data.test_case.description}\n难度: ${data.test_case.difficulty}\n预期检测: ${data.test_case.expected_detections.join(', ')}\n\n${historyHtml.replace(/<[^>]*>/g, '')}`);
            })
            .catch(error => {
                alert('网络错误: ' + error);
            });
        }

        // 定期刷新统计信息
        setInterval(loadStatistics, 30000); // 每30秒刷新一次
    </script>
</body>
</html>
'''

if __name__ == '__main__':
    print("🧪 启动测试框架Web界面...")
    print("📍 访问地址: http://localhost:5558")
    print("🎯 功能特性:")
    print("  - 完整的测试用例管理")
    print("  - 优雅的测试框架设计")
    print("  - 实时测试进度监控")
    print("  - 详细的性能评估报告")
    print("  - 历史测试记录查询")
    
    app.run(host='0.0.0.0', port=5558, debug=False)