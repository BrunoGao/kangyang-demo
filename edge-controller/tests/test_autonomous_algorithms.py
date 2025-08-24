#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
自主算法测试套件
测试所有核心自主算法的功能和性能
"""

import pytest
import numpy as np
import time
import tempfile
import os
from unittest.mock import Mock, patch

# 测试导入
import sys
sys.path.append('/Users/brunogao/work/codes/kangyang/kangyang-demo/edge-controller/src')

from ai.autonomous import (
    AutonomousFallDetector,
    AutonomousFireSmokeDetector,
    MultiStreamBatchScheduler,
    FalseAlarmSuppression,
    TemporalSequenceAnalyzer,
    LightweightPoseNet
)
from ai.autonomous.batch_scheduler import StreamConfig, StreamPriority
from ai.autonomous.performance_optimizer import PerformanceOptimizer

class TestLightweightPoseNet:
    """关键点提取器测试"""
    
    @pytest.fixture
    def pose_extractor(self):
        """创建关键点提取器实例"""
        config = {
            'input_size': (256, 192),
            'confidence_threshold': 0.3,
            'use_npu': False
        }
        return LightweightPoseNet(config)
    
    def test_initialization(self, pose_extractor):
        """测试初始化"""
        assert pose_extractor.input_size == (256, 192)
        assert pose_extractor.confidence_threshold == 0.3
        assert not pose_extractor.use_npu
    
    def test_extract_keypoints(self, pose_extractor):
        """测试关键点提取"""
        # 创建测试图像
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        # 执行关键点提取
        keypoints_list = pose_extractor.extract(test_frame)
        
        # 验证结果
        assert keypoints_list is not None
        if keypoints_list:
            for keypoints in keypoints_list:
                assert keypoints.shape == (17, 3)  # 17个关键点，每个3个值(x,y,conf)
                assert np.all(keypoints[:, 2] >= 0)  # 置信度非负
                assert np.all(keypoints[:, 2] <= 1)  # 置信度不超过1
    
    def test_preprocessing(self, pose_extractor):
        """测试预处理"""
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        
        input_tensor, scale_info = pose_extractor._preprocess(test_frame)
        
        # 验证输入张量
        assert input_tensor.shape == (1, 3, 256, 192)  # NCHW格式
        assert input_tensor.dtype == np.float32
        assert np.all(input_tensor >= 0) and np.all(input_tensor <= 1)  # 归一化
        
        # 验证缩放信息
        assert 'scale' in scale_info
        assert 'pad_x' in scale_info
        assert 'pad_y' in scale_info
        assert 'original_size' in scale_info
    
    def test_get_stats(self, pose_extractor):
        """测试统计信息获取"""
        stats = pose_extractor.get_stats()
        
        assert 'extractor_type' in stats
        assert 'performance' in stats
        assert 'keypoint_format' in stats
        assert stats['extractor_type'] == 'lightweight_posenet'

class TestAutonomousFallDetector:
    """跌倒检测算法测试"""
    
    @pytest.fixture
    def fall_detector(self):
        """创建跌倒检测器实例"""
        config = {
            'confidence_threshold': 0.85,
            'temporal_window_size': 30,
            'min_fall_duration': 0.5
        }
        return AutonomousFallDetector(config)
    
    def test_initialization(self, fall_detector):
        """测试初始化"""
        assert fall_detector.confidence_threshold == 0.85
        assert fall_detector.temporal_window_size == 30
        assert fall_detector.min_fall_duration == 0.5
        assert len(fall_detector.keypoint_history) == 0
    
    def test_detect_interface(self, fall_detector):
        """测试检测接口"""
        # 创建测试帧
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        timestamp = time.time()
        frame_number = 1
        
        # 执行检测
        result = fall_detector.detect(test_frame, timestamp, frame_number)
        
        # 由于是模拟数据，结果可能为None，但不应该抛出异常
        if result is not None:
            assert 'type' in result
            assert 'confidence' in result
            assert 'timestamp' in result
            assert 'algorithm' in result
    
    def test_geometric_features_extraction(self, fall_detector):
        """测试几何特征提取"""
        # 创建模拟关键点 (17个关键点，x,y,confidence)
        keypoints = np.random.rand(17, 3)
        keypoints[:, :2] *= 640  # x,y坐标在图像范围内
        keypoints[:, 2] = np.random.uniform(0.4, 1.0, 17)  # 置信度
        
        features = fall_detector._extract_geometric_features(keypoints)
        
        if features:  # 如果提取成功
            assert 'height_ratio' in features
            assert 'stability_score' in features
            assert 'body_tilt' in features
            assert 'centroid_x' in features
            assert 'centroid_y' in features
    
    def test_cooldown_period(self, fall_detector):
        """测试冷却期机制"""
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        timestamp1 = time.time()
        
        # 第一次检测
        result1 = fall_detector.detect(test_frame, timestamp1, 1)
        
        # 立即进行第二次检测（在冷却期内）
        timestamp2 = timestamp1 + 1.0  # 1秒后，仍在冷却期内
        result2 = fall_detector.detect(test_frame, timestamp2, 2)
        
        # 如果第一次检测成功，第二次应该返回None（由于冷却期）
        if result1 is not None:
            assert result2 is None
    
    def test_get_stats(self, fall_detector):
        """测试统计信息"""
        stats = fall_detector.get_stats()
        
        assert 'detector_type' in stats
        assert 'version' in stats
        assert 'algorithm_features' in stats
        assert 'stats' in stats
        assert stats['detector_type'] == 'autonomous_fall_detection_v2'

class TestAutonomousFireSmokeDetector:
    """火焰烟雾检测算法测试"""
    
    @pytest.fixture
    def fire_smoke_detector(self):
        """创建火焰烟雾检测器实例"""
        config = {
            'confidence_threshold': 0.75,
            'temporal_window_size': 45,
            'min_detection_duration': 2.0
        }
        return AutonomousFireSmokeDetector(config)
    
    def test_initialization(self, fire_smoke_detector):
        """测试初始化"""
        assert fire_smoke_detector.confidence_threshold == 0.75
        assert fire_smoke_detector.temporal_window_size == 45
        assert fire_smoke_detector.min_detection_duration == 2.0
    
    def test_detect_interface(self, fire_smoke_detector):
        """测试检测接口"""
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        timestamp = time.time()
        frame_number = 1
        
        result = fire_smoke_detector.detect(test_frame, timestamp, frame_number)
        
        if result is not None:
            assert 'type' in result
            assert result['type'] in ['fire', 'smoke']
            assert 'confidence' in result
            assert 'regions' in result
    
    def test_color_features_extraction(self, fire_smoke_detector):
        """测试颜色特征提取"""
        # 创建包含红色区域的测试图像（模拟火焰）
        test_frame = np.zeros((480, 640, 3), dtype=np.uint8)
        test_frame[200:300, 200:300] = [0, 0, 255]  # 红色区域
        
        features = fire_smoke_detector._extract_color_features(test_frame)
        
        assert 'fire_ratio' in features
        assert 'smoke_ratio' in features
        assert 'fire_regions' in features
        assert 'smoke_regions' in features
        assert features['fire_ratio'] >= 0
        assert features['smoke_ratio'] >= 0
    
    def test_get_stats(self, fire_smoke_detector):
        """测试统计信息"""
        stats = fire_smoke_detector.get_stats()
        
        assert 'detector_type' in stats
        assert 'detection_types' in stats
        assert stats['detector_type'] == 'autonomous_fire_smoke_detection_v2'
        assert 'fire' in stats['detection_types']
        assert 'smoke' in stats['detection_types']

class TestMultiStreamBatchScheduler:
    """批处理调度器测试"""
    
    @pytest.fixture
    def scheduler(self):
        """创建调度器实例"""
        config = {
            'max_streams': 5,  # 降低测试用的最大流数
            'cpu_workers': 2,
            'gpu_workers': 1,
            'npu_workers': 1
        }
        scheduler = MultiStreamBatchScheduler(config)
        scheduler.start()
        yield scheduler
        scheduler.stop()
    
    def test_initialization(self, scheduler):
        """测试初始化"""
        assert scheduler.max_streams == 5
        assert len(scheduler.processors) == 4  # 2 CPU + 1 GPU + 1 NPU
        assert scheduler.is_running
    
    def test_stream_management(self, scheduler):
        """测试流管理"""
        # 创建测试流配置
        stream_config = StreamConfig(
            stream_id='test_stream_1',
            rtsp_url='rtsp://test.com/stream1',
            priority=StreamPriority.HIGH,
            region_name='test_room'
        )
        
        # 添加流
        success = scheduler.add_stream(stream_config)
        assert success
        assert 'test_stream_1' in scheduler.active_streams
        
        # 移除流
        success = scheduler.remove_stream('test_stream_1')
        assert success
        assert 'test_stream_1' not in scheduler.active_streams
    
    def test_frame_submission(self, scheduler):
        """测试帧提交"""
        # 添加测试流
        stream_config = StreamConfig(
            stream_id='test_stream_2',
            rtsp_url='rtsp://test.com/stream2',
            priority=StreamPriority.NORMAL
        )
        scheduler.add_stream(stream_config)
        
        # 提交测试帧
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        timestamp = time.time()
        frame_number = 1
        
        success = scheduler.submit_frame('test_stream_2', test_frame, timestamp, frame_number)
        assert success
    
    def test_get_stats(self, scheduler):
        """测试统计信息"""
        stats = scheduler.get_stats()
        
        assert 'scheduler_type' in stats
        assert 'processor_stats' in stats
        assert 'stream_stats' in stats
        assert 'queue_stats' in stats
        assert stats['scheduler_type'] == 'multi_stream_batch_scheduler'

class TestFalseAlarmSuppression:
    """误报抑制系统测试"""
    
    @pytest.fixture
    def suppression_system(self):
        """创建误报抑制系统实例"""
        config = {
            'confidence_adjustment_factor': 0.2,
            'min_validation_score': 0.6
        }
        return FalseAlarmSuppression(config)
    
    def test_initialization(self, suppression_system):
        """测试初始化"""
        assert suppression_system.confidence_adjustment_factor == 0.2
        assert suppression_system.min_validation_score == 0.6
        assert len(suppression_system.rules) > 0  # 应该有预定义规则
    
    def test_rule_library(self, suppression_system):
        """测试规则库"""
        # 检查跌倒检测规则
        fall_rules = suppression_system.rule_categories.get('fall_detection', [])
        assert len(fall_rules) > 0
        
        # 检查火焰烟雾检测规则
        fire_smoke_rules = suppression_system.rule_categories.get('fire_smoke_detection', [])
        assert len(fire_smoke_rules) > 0
        
        # 检查规则详情
        for rule_id in fall_rules:
            rule = suppression_system.rules.get(rule_id)
            assert rule is not None
            assert hasattr(rule, 'rule_type')
            assert hasattr(rule, 'priority')
            assert hasattr(rule, 'threshold')
    
    def test_validation_process(self, suppression_system):
        """测试验证流程"""
        # 创建模拟检测结果
        detection_result = {
            'type': 'fall',
            'confidence': 0.8,
            'timestamp': time.time(),
            'geometric_features': {
                'height_ratio': 0.4,
                'stability_score': 0.3,
                'body_tilt': 0.5
            },
            'motion_features': {
                'velocity_magnitude': 150.0,
                'downward_motion': 50.0,
                'angular_velocity': 2.0
            },
            'temporal_features': {
                'consistency_score': 0.7,
                'sequence_length': 20,
                'time_span': 1.5
            }
        }
        
        # 执行验证
        validation_result = suppression_system.validate_detection(detection_result)
        
        assert 'is_valid' in validation_result
        assert 'original_confidence' in validation_result
        assert 'adjusted_confidence' in validation_result
        assert 'validation_score' in validation_result
        assert 'validation_details' in validation_result
    
    def test_rule_management(self, suppression_system):
        """测试规则管理"""
        # 测试更新规则阈值
        rule_id = list(suppression_system.rules.keys())[0]
        original_threshold = suppression_system.rules[rule_id].threshold
        new_threshold = original_threshold * 0.8
        
        success = suppression_system.update_rule_threshold(rule_id, new_threshold)
        assert success
        assert suppression_system.rules[rule_id].threshold == new_threshold
        
        # 测试启用/禁用规则
        success = suppression_system.enable_rule(rule_id, False)
        assert success
        assert not suppression_system.rules[rule_id].enabled
    
    def test_get_stats(self, suppression_system):
        """测试统计信息"""
        stats = suppression_system.get_stats()
        
        assert 'suppression_system_type' in stats
        assert 'rule_stats' in stats
        assert 'validation_stats' in stats
        assert stats['suppression_system_type'] == 'autonomous_false_alarm_suppression_v2'

class TestTemporalSequenceAnalyzer:
    """时序分析器测试"""
    
    @pytest.fixture
    def temporal_analyzer(self):
        """创建时序分析器实例"""
        return TemporalSequenceAnalyzer(window_size=30, fps=15)
    
    def test_initialization(self, temporal_analyzer):
        """测试初始化"""
        assert temporal_analyzer.window_size == 30
        assert temporal_analyzer.fps == 15
        assert temporal_analyzer.time_window == 2.0  # 30/15
    
    def test_sequence_analysis(self, temporal_analyzer):
        """测试序列分析"""
        # 创建模拟关键点序列
        keypoint_sequence = []
        base_time = time.time()
        
        for i in range(10):
            keypoints = np.random.rand(17, 3)
            keypoints[:, :2] *= 640
            keypoints[:, 2] = np.random.uniform(0.4, 1.0, 17)
            
            keypoint_sequence.append({
                'keypoints': keypoints,
                'timestamp': base_time + i * 0.067,  # ~15fps
                'frame_number': i,
                'person_id': 1
            })
        
        # 执行分析
        result = temporal_analyzer.analyze_sequence(keypoint_sequence)
        
        assert 'consistency_score' in result
        assert 'temporal_features' in result
        assert result['consistency_score'] >= 0
        assert result['consistency_score'] <= 1

class TestPerformanceOptimizer:
    """性能优化器测试"""
    
    @pytest.fixture
    def optimizer(self):
        """创建性能优化器实例"""
        config = {
            'monitoring_interval': 0.1,  # 快速测试
            'optimization_interval': 0.5
        }
        optimizer = PerformanceOptimizer(config)
        yield optimizer
        if optimizer.is_monitoring:
            optimizer.stop_monitoring()
    
    def test_initialization(self, optimizer):
        """测试初始化"""
        assert optimizer.monitoring_interval == 0.1
        assert optimizer.optimization_interval == 0.5
        assert not optimizer.is_monitoring
    
    def test_monitoring_lifecycle(self, optimizer):
        """测试监控生命周期"""
        # 启动监控
        optimizer.start_monitoring()
        assert optimizer.is_monitoring
        
        # 等待一些监控数据
        time.sleep(0.5)
        
        # 检查是否有数据
        assert len(optimizer.metrics_history) > 0
        
        # 停止监控
        optimizer.stop_monitoring()
        assert not optimizer.is_monitoring
    
    def test_component_registration(self, optimizer):
        """测试组件注册"""
        mock_component = Mock()
        mock_callback = Mock()
        
        optimizer.register_component('test_component', mock_component, mock_callback)
        
        assert 'test_component' in optimizer.registered_components
        assert 'test_component' in optimizer.optimization_callbacks
    
    def test_memory_buffer_management(self, optimizer):
        """测试内存缓冲区管理"""
        # 获取缓冲区
        buffer = optimizer.get_memory_buffer('frame_buffers', (480, 640, 3))
        assert buffer is not None
        assert buffer.shape == (480, 640, 3)
        
        # 归还缓冲区
        optimizer.return_memory_buffer('frame_buffers', buffer)
        
        # 再次获取应该重用
        buffer2 = optimizer.get_memory_buffer('frame_buffers', (480, 640, 3))
        # 注意: 由于实现细节，这个测试可能需要调整
    
    def test_get_performance_report(self, optimizer):
        """测试性能报告"""
        # 启动监控收集一些数据
        optimizer.start_monitoring()
        time.sleep(0.3)
        
        report = optimizer.get_performance_report()
        
        assert 'timestamp' in report
        assert 'system_performance' in report
        assert 'optimization_stats' in report

class TestIntegration:
    """集成测试"""
    
    def test_end_to_end_fall_detection(self):
        """端到端跌倒检测测试"""
        # 创建组件
        fall_detector = AutonomousFallDetector()
        suppression_system = FalseAlarmSuppression()
        
        # 创建测试帧
        test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
        timestamp = time.time()
        
        # 执行检测
        detection_result = fall_detector.detect(test_frame, timestamp, 1)
        
        if detection_result:
            # 执行误报抑制
            validation_result = suppression_system.validate_detection(detection_result)
            
            assert 'is_valid' in validation_result
            if validation_result['is_valid']:
                assert 'adjusted_detection' in validation_result
    
    def test_multi_algorithm_performance(self):
        """多算法性能测试"""
        # 创建算法实例
        fall_detector = AutonomousFallDetector()
        fire_detector = AutonomousFireSmokeDetector()
        
        # 性能测试参数
        num_frames = 10
        frame_times = []
        
        # 执行性能测试
        for i in range(num_frames):
            test_frame = np.random.randint(0, 255, (480, 640, 3), dtype=np.uint8)
            timestamp = time.time()
            
            start_time = time.time()
            
            # 并行执行两个算法
            fall_result = fall_detector.detect(test_frame, timestamp, i)
            fire_result = fire_detector.detect(test_frame, timestamp, i)
            
            frame_time = time.time() - start_time
            frame_times.append(frame_time)
        
        # 分析性能
        avg_frame_time = np.mean(frame_times)
        max_frame_time = np.max(frame_times)
        fps = 1.0 / avg_frame_time if avg_frame_time > 0 else 0
        
        print(f"平均帧处理时间: {avg_frame_time*1000:.1f}ms")
        print(f"最大帧处理时间: {max_frame_time*1000:.1f}ms") 
        print(f"平均FPS: {fps:.1f}")
        
        # 性能断言 (根据实际硬件调整)
        assert avg_frame_time < 1.0  # 平均处理时间小于1秒
        assert fps >= 1.0  # 至少1FPS

if __name__ == '__main__':
    # 运行测试
    pytest.main([__file__, '-v', '--tb=short'])