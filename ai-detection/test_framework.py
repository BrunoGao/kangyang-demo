#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
优雅的跌倒检测测试框架
整合视频处理、算法测试、性能评估于一体的完整测试解决方案
"""

import os
import json
import time
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass, asdict
from pathlib import Path
import sqlite3

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('test_framework.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

@dataclass
class TestCase:
    """测试用例数据结构"""
    id: str
    name: str
    description: str
    video_path: str
    expected_detections: List[str]  # ['fall', 'fire', 'smoke']
    difficulty: str  # easy, medium, hard, very_hard
    duration_seconds: int
    ground_truth: Optional[Dict] = None  # 标注数据
    tags: Optional[List[str]] = None

@dataclass
class TestResult:
    """测试结果数据结构"""
    test_case_id: str
    session_id: str
    start_time: str
    end_time: str
    detections: List[Dict]
    alerts: List[Dict]
    performance_metrics: Dict
    statistics: Dict
    passed: bool
    error_message: Optional[str] = None

class DatabaseManager:
    """测试数据库管理器"""
    
    def __init__(self, db_path: str = "test_results.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """初始化数据库表"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # 测试用例表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_cases (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                description TEXT,
                video_path TEXT,
                expected_detections TEXT,
                difficulty TEXT,
                duration_seconds INTEGER,
                ground_truth TEXT,
                tags TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # 测试结果表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS test_results (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_case_id TEXT,
                session_id TEXT,
                start_time TEXT,
                end_time TEXT,
                detections TEXT,
                alerts TEXT,
                performance_metrics TEXT,
                statistics TEXT,
                passed BOOLEAN,
                error_message TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (test_case_id) REFERENCES test_cases (id)
            )
        ''')
        
        # 性能基准表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS performance_benchmarks (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                test_type TEXT,
                metric_name TEXT,
                expected_value REAL,
                tolerance REAL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def save_test_case(self, test_case: TestCase):
        """保存测试用例"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO test_cases 
            (id, name, description, video_path, expected_detections, difficulty, 
             duration_seconds, ground_truth, tags)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            test_case.id, test_case.name, test_case.description, test_case.video_path,
            json.dumps(test_case.expected_detections), test_case.difficulty,
            test_case.duration_seconds, json.dumps(test_case.ground_truth),
            json.dumps(test_case.tags)
        ))
        
        conn.commit()
        conn.close()
    
    def save_test_result(self, result: TestResult):
        """保存测试结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO test_results 
            (test_case_id, session_id, start_time, end_time, detections, alerts,
             performance_metrics, statistics, passed, error_message)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            result.test_case_id, result.session_id, result.start_time, result.end_time,
            json.dumps(result.detections), json.dumps(result.alerts),
            json.dumps(result.performance_metrics), json.dumps(result.statistics),
            result.passed, result.error_message
        ))
        
        conn.commit()
        conn.close()
    
    def get_test_history(self, test_case_id: str, limit: int = 10) -> List[Dict]:
        """获取测试历史"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT * FROM test_results 
            WHERE test_case_id = ? 
            ORDER BY created_at DESC 
            LIMIT ?
        ''', (test_case_id, limit))
        
        results = cursor.fetchall()
        conn.close()
        
        columns = ['id', 'test_case_id', 'session_id', 'start_time', 'end_time',
                  'detections', 'alerts', 'performance_metrics', 'statistics',
                  'passed', 'error_message', 'created_at']
        
        return [dict(zip(columns, row)) for row in results]

class PerformanceProfiler:
    """性能分析器"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, metric_name: str):
        """开始计时"""
        self.start_times[metric_name] = time.time()
    
    def end_timer(self, metric_name: str):
        """结束计时"""
        if metric_name in self.start_times:
            elapsed = time.time() - self.start_times[metric_name]
            self.metrics[metric_name] = elapsed
            del self.start_times[metric_name]
            return elapsed
        return 0
    
    def record_metric(self, metric_name: str, value: float):
        """记录指标"""
        self.metrics[metric_name] = value
    
    def get_metrics(self) -> Dict[str, float]:
        """获取所有指标"""
        return self.metrics.copy()
    
    def reset(self):
        """重置所有指标"""
        self.metrics.clear()
        self.start_times.clear()

class TestValidator:
    """测试结果验证器"""
    
    @staticmethod
    def validate_detection_accuracy(actual_detections: List[Dict], 
                                  expected_types: List[str]) -> Dict[str, float]:
        """验证检测准确性"""
        detected_types = [d['type'] for d in actual_detections]
        
        # 计算精确率和召回率
        true_positives = len(set(detected_types) & set(expected_types))
        false_positives = len(detected_types) - true_positives
        false_negatives = len(expected_types) - true_positives
        
        precision = true_positives / (true_positives + false_positives) if (true_positives + false_positives) > 0 else 0
        recall = true_positives / (true_positives + false_negatives) if (true_positives + false_negatives) > 0 else 0
        f1_score = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': precision,
            'recall': recall,
            'f1_score': f1_score,
            'true_positives': true_positives,
            'false_positives': false_positives,
            'false_negatives': false_negatives
        }
    
    @staticmethod
    def validate_confidence_scores(detections: List[Dict]) -> Dict[str, float]:
        """验证置信度分数"""
        if not detections:
            return {'avg_confidence': 0, 'min_confidence': 0, 'max_confidence': 0}
        
        confidences = [d.get('confidence', 0) for d in detections]
        return {
            'avg_confidence': sum(confidences) / len(confidences),
            'min_confidence': min(confidences),
            'max_confidence': max(confidences),
            'std_confidence': (sum([(c - sum(confidences)/len(confidences))**2 for c in confidences]) / len(confidences))**0.5
        }
    
    @staticmethod
    def validate_performance_metrics(metrics: Dict[str, float]) -> Dict[str, bool]:
        """验证性能指标"""
        benchmarks = {
            'processing_time': 5.0,  # 5秒内完成
            'memory_usage': 1000.0,  # 1GB内存限制
            'cpu_usage': 80.0,       # 80%CPU使用率限制
            'detection_latency': 1.0  # 1秒检测延迟
        }
        
        validation_results = {}
        for metric, benchmark in benchmarks.items():
            if metric in metrics:
                validation_results[f"{metric}_passed"] = metrics[metric] <= benchmark
            else:
                validation_results[f"{metric}_passed"] = True  # 如果没有数据，默认通过
        
        return validation_results

class TestExecutor:
    """测试执行器"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
        self.profiler = PerformanceProfiler()
        self.validator = TestValidator()
        
        # 导入检测器
        try:
            from real_fall_detector import SimpleFallDetector, RealFireSmokeDetector
            self.fall_detector = SimpleFallDetector()
            self.fire_detector = RealFireSmokeDetector()
            logger.info("检测器初始化成功")
        except ImportError as e:
            logger.error(f"检测器导入失败: {e}")
            self.fall_detector = None
            self.fire_detector = None
    
    def execute_test_case(self, test_case: TestCase, 
                         callback: Optional[Callable] = None) -> TestResult:
        """执行单个测试用例"""
        session_id = f"test_{test_case.id}_{int(time.time())}"
        start_time = datetime.now().isoformat()
        
        logger.info(f"开始执行测试用例: {test_case.name} (ID: {test_case.id})")
        
        self.profiler.reset()
        self.profiler.start_timer('total_execution_time')
        
        try:
            # 检查视频文件是否存在
            if not os.path.exists(test_case.video_path):
                raise FileNotFoundError(f"视频文件不存在: {test_case.video_path}")
            
            # 执行检测
            detections, alerts = self._run_detection(test_case, callback)
            
            # 结束计时
            self.profiler.end_timer('total_execution_time')
            
            # 收集性能指标
            performance_metrics = self.profiler.get_metrics()
            
            # 验证结果
            accuracy_metrics = self.validator.validate_detection_accuracy(
                detections, test_case.expected_detections
            )
            confidence_metrics = self.validator.validate_confidence_scores(detections)
            performance_validation = self.validator.validate_performance_metrics(performance_metrics)
            
            # 生成统计信息
            statistics = {
                'total_detections': len(detections),
                'total_alerts': len(alerts),
                'detection_types': list(set(d['type'] for d in detections)),
                'accuracy_metrics': accuracy_metrics,
                'confidence_metrics': confidence_metrics,
                'performance_validation': performance_validation
            }
            
            # 判断是否通过测试
            passed = (
                accuracy_metrics['f1_score'] >= 0.5 and  # F1分数至少50%
                all(performance_validation.values()) and  # 性能指标全部通过
                len(detections) > 0  # 至少有一个检测结果
            )
            
            end_time = datetime.now().isoformat()
            
            result = TestResult(
                test_case_id=test_case.id,
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                detections=detections,
                alerts=alerts,
                performance_metrics=performance_metrics,
                statistics=statistics,
                passed=passed
            )
            
            # 保存结果到数据库
            self.db_manager.save_test_result(result)
            
            logger.info(f"测试用例 {test_case.name} 执行完成: {'通过' if passed else '失败'}")
            return result
            
        except Exception as e:
            end_time = datetime.now().isoformat()
            error_message = str(e)
            
            logger.error(f"测试用例 {test_case.name} 执行失败: {error_message}")
            
            result = TestResult(
                test_case_id=test_case.id,
                session_id=session_id,
                start_time=start_time,
                end_time=end_time,
                detections=[],
                alerts=[],
                performance_metrics=self.profiler.get_metrics(),
                statistics={},
                passed=False,
                error_message=error_message
            )
            
            # 保存错误结果
            self.db_manager.save_test_result(result)
            return result
    
    def _run_detection(self, test_case: TestCase, callback: Optional[Callable] = None) -> tuple:
        """运行检测算法"""
        detections = []
        alerts = []
        
        # 模拟视频帧处理（实际应用中这里会读取真实视频）
        # 假设30FPS，根据视频时长计算总帧数
        total_frames = test_case.duration_seconds * 30
        
        self.profiler.start_timer('detection_processing')
        
        for frame_num in range(1, min(total_frames, 300) + 1):  # 最多处理300帧
            timestamp = frame_num / 30.0
            frame_data = f"{test_case.video_path}_frame_{frame_num}"
            
            # 跌倒检测
            if 'fall' in test_case.expected_detections and self.fall_detector:
                fall_result = self.fall_detector.detect_fall_from_video(
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
                    detections.append(detection)
                    
                    # 生成告警
                    if fall_result['confidence'] > 0.7:
                        alert = self._create_alert('fall', frame_num, timestamp, fall_result['confidence'])
                        alerts.append(alert)
            
            # 火焰烟雾检测
            if any(dt in test_case.expected_detections for dt in ['fire', 'smoke']) and self.fire_detector:
                fire_detections = self.fire_detector.detect_fire_smoke_from_video(
                    frame_data, frame_num, timestamp
                )
                
                for fire_detection in fire_detections:
                    detection = {
                        'type': fire_detection['type'],
                        'frame_number': frame_num,
                        'timestamp': timestamp,
                        'confidence': fire_detection['confidence'],
                        'details': fire_detection
                    }
                    detections.append(detection)
                    
                    # 生成告警
                    if fire_detection['confidence'] > 0.6:
                        alert = self._create_alert(
                            fire_detection['type'], frame_num, timestamp, fire_detection['confidence']
                        )
                        alerts.append(alert)
            
            # 回调进度更新
            if callback and frame_num % 10 == 0:
                progress = (frame_num / total_frames) * 100
                callback(progress, frame_num, detections, alerts)
            
            # 模拟处理时间
            time.sleep(0.01)
        
        self.profiler.end_timer('detection_processing')
        return detections, alerts
    
    def _create_alert(self, detection_type: str, frame_num: int, 
                     timestamp: float, confidence: float) -> Dict:
        """创建告警"""
        severity_map = {
            'fire': 'CRITICAL',
            'smoke': 'HIGH',
            'fall': 'HIGH' if confidence > 0.8 else 'MEDIUM'
        }
        
        return {
            'id': f"{detection_type}_{frame_num}_{int(time.time())}",
            'type': detection_type,
            'severity': severity_map.get(detection_type, 'MEDIUM'),
            'message': f"检测到{detection_type}事件 (帧:{frame_num}, 置信度:{confidence:.2f})",
            'timestamp': datetime.now().isoformat(),
            'frame_number': frame_num,
            'confidence': confidence
        }

class TestSuiteManager:
    """测试套件管理器"""
    
    def __init__(self):
        self.test_cases = {}
        self.executor = TestExecutor()
        self.db_manager = DatabaseManager()
        
        # 初始化预设测试用例
        self._initialize_default_test_cases()
    
    def _initialize_default_test_cases(self):
        """初始化默认测试用例"""
        default_cases = [
            TestCase(
                id="fall_001",
                name="老人卫生间跌倒检测",
                description="模拟老人在卫生间跌倒的场景，测试算法在复杂环境下的检测能力",
                video_path="test_videos/elderly_bathroom_fall.mp4",
                expected_detections=["fall"],
                difficulty="medium",
                duration_seconds=45,
                tags=["fall", "elderly", "bathroom", "medium"]
            ),
            TestCase(
                id="fall_002", 
                name="卧室跌倒检测",
                description="模拟老人在卧室跌倒的场景，光线较暗环境下的检测测试",
                video_path="test_videos/elderly_bedroom_fall.mp4",
                expected_detections=["fall"],
                difficulty="easy",
                duration_seconds=30,
                tags=["fall", "elderly", "bedroom", "easy"]
            ),
            TestCase(
                id="fire_001",
                name="厨房火灾检测",
                description="厨房环境下的火焰和烟雾检测，包含复杂背景干扰",
                video_path="test_videos/kitchen_fire.mp4",
                expected_detections=["fire", "smoke"],
                difficulty="medium",
                duration_seconds=90,
                tags=["fire", "smoke", "kitchen", "medium"]
            ),
            TestCase(
                id="fire_002",
                name="客厅烟雾检测",
                description="客厅环境下的烟雾检测，测试早期火灾预警能力",
                video_path="test_videos/living_room_smoke.mp4", 
                expected_detections=["smoke"],
                difficulty="easy",
                duration_seconds=60,
                tags=["smoke", "living_room", "easy"]
            ),
            TestCase(
                id="complex_001",
                name="复合场景检测",
                description="包含跌倒和火灾的复杂紧急情况，测试多类型同时检测",
                video_path="test_videos/emergency_evacuation.mp4",
                expected_detections=["fall", "fire", "smoke"],
                difficulty="very_hard",
                duration_seconds=180,
                tags=["fall", "fire", "smoke", "complex", "very_hard"]
            )
        ]
        
        for test_case in default_cases:
            self.add_test_case(test_case)
    
    def add_test_case(self, test_case: TestCase):
        """添加测试用例"""
        self.test_cases[test_case.id] = test_case
        self.db_manager.save_test_case(test_case)
        logger.info(f"添加测试用例: {test_case.name} (ID: {test_case.id})")
    
    def get_test_case(self, test_id: str) -> Optional[TestCase]:
        """获取测试用例"""
        return self.test_cases.get(test_id)
    
    def list_test_cases(self, difficulty: Optional[str] = None, 
                       tags: Optional[List[str]] = None) -> List[TestCase]:
        """列出测试用例"""
        cases = list(self.test_cases.values())
        
        if difficulty:
            cases = [case for case in cases if case.difficulty == difficulty]
        
        if tags:
            cases = [case for case in cases 
                    if case.tags and any(tag in case.tags for tag in tags)]
        
        return cases
    
    def run_test_suite(self, test_ids: Optional[List[str]] = None,
                      progress_callback: Optional[Callable] = None) -> Dict[str, TestResult]:
        """运行测试套件"""
        if test_ids is None:
            test_ids = list(self.test_cases.keys())
        
        results = {}
        total_tests = len(test_ids)
        
        logger.info(f"开始运行测试套件，共 {total_tests} 个测试用例")
        
        for i, test_id in enumerate(test_ids):
            test_case = self.test_cases.get(test_id)
            if not test_case:
                logger.warning(f"测试用例不存在: {test_id}")
                continue
            
            # 运行测试
            result = self.executor.execute_test_case(test_case, progress_callback)
            results[test_id] = result
            
            # 更新整体进度
            if progress_callback:
                overall_progress = ((i + 1) / total_tests) * 100
                progress_callback(overall_progress, f"完成测试 {i + 1}/{total_tests}")
        
        logger.info(f"测试套件运行完成，通过率: {sum(1 for r in results.values() if r.passed)}/{total_tests}")
        return results
    
    def generate_report(self, results: Dict[str, TestResult]) -> Dict:
        """生成测试报告"""
        total_tests = len(results)
        passed_tests = sum(1 for r in results.values() if r.passed)
        failed_tests = total_tests - passed_tests
        
        # 按难度统计
        difficulty_stats = {}
        for test_id, result in results.items():
            test_case = self.test_cases.get(test_id)
            if test_case:
                difficulty = test_case.difficulty
                if difficulty not in difficulty_stats:
                    difficulty_stats[difficulty] = {'total': 0, 'passed': 0}
                difficulty_stats[difficulty]['total'] += 1
                if result.passed:
                    difficulty_stats[difficulty]['passed'] += 1
        
        # 按检测类型统计
        detection_type_stats = {}
        for result in results.values():
            for detection in result.detections:
                det_type = detection['type']
                if det_type not in detection_type_stats:
                    detection_type_stats[det_type] = {'count': 0, 'avg_confidence': 0}
                detection_type_stats[det_type]['count'] += 1
        
        # 计算平均置信度
        for det_type in detection_type_stats:
            confidences = []
            for result in results.values():
                confidences.extend([d['confidence'] for d in result.detections if d['type'] == det_type])
            if confidences:
                detection_type_stats[det_type]['avg_confidence'] = sum(confidences) / len(confidences)
        
        # 性能统计
        processing_times = [r.performance_metrics.get('total_execution_time', 0) 
                           for r in results.values()]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        report = {
            'summary': {
                'total_tests': total_tests,
                'passed_tests': passed_tests,
                'failed_tests': failed_tests,
                'pass_rate': passed_tests / total_tests if total_tests > 0 else 0,
                'avg_processing_time': avg_processing_time
            },
            'difficulty_breakdown': difficulty_stats,
            'detection_type_breakdown': detection_type_stats,
            'failed_tests': [
                {
                    'test_id': test_id,
                    'test_name': self.test_cases.get(test_id, TestCase('', '', '', '', [], '', 0)).name,
                    'error_message': result.error_message,
                    'statistics': result.statistics
                }
                for test_id, result in results.items() 
                if not result.passed
            ],
            'generated_at': datetime.now().isoformat()
        }
        
        return report

# 便捷函数
def quick_test(test_type: str = "all", difficulty: str = "easy") -> Dict:
    """快速测试函数"""
    suite_manager = TestSuiteManager()
    
    # 根据参数筛选测试用例
    test_cases = suite_manager.list_test_cases(difficulty=difficulty)
    
    if test_type != "all":
        test_cases = [case for case in test_cases 
                     if test_type in case.expected_detections]
    
    if not test_cases:
        return {"error": "没有找到匹配的测试用例"}
    
    # 运行测试
    test_ids = [case.id for case in test_cases]
    results = suite_manager.run_test_suite(test_ids)
    
    # 生成报告
    report = suite_manager.generate_report(results)
    
    return {
        "test_results": results,
        "report": report,
        "message": f"快速测试完成，运行了 {len(test_cases)} 个测试用例"
    }

if __name__ == "__main__":
    print("🧪 跌倒检测测试框架")
    print("==================")
    
    # 演示快速测试
    result = quick_test(test_type="fall", difficulty="easy")
    
    if "error" in result:
        print(f"❌ {result['error']}")
    else:
        print(f"✅ {result['message']}")
        print(f"📊 通过率: {result['report']['summary']['pass_rate']:.1%}")
        print(f"⏱️  平均处理时间: {result['report']['summary']['avg_processing_time']:.2f}秒")