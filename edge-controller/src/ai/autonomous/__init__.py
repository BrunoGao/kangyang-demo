#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
康养AI检测系统 - 自主产权算法模块
包含三大核心自主算法：
1. 跌倒检测算法 (关键点+时序分析)
2. 火焰烟雾检测算法 (多模态+规则引擎)  
3. 批处理调度器 (智能负载均衡)
"""

from .fall_detector_v2 import AutonomousFallDetector
from .fire_smoke_detector_v2 import AutonomousFireSmokeDetector
from .batch_scheduler import MultiStreamBatchScheduler
from .rule_engine import FalseAlarmSuppression
from .temporal_analyzer import TemporalSequenceAnalyzer
from .keypoint_extractor import LightweightPoseNet

__version__ = "2.0.0"
__author__ = "康养AI团队"
__copyright__ = "自主产权核心算法模块"

# 自主算法注册表
AUTONOMOUS_ALGORITHMS = {
    'fall_detection_v2': AutonomousFallDetector,
    'fire_smoke_detection_v2': AutonomousFireSmokeDetector,
    'batch_scheduler': MultiStreamBatchScheduler,
    'rule_engine': FalseAlarmSuppression,
    'temporal_analyzer': TemporalSequenceAnalyzer,
    'keypoint_extractor': LightweightPoseNet
}

__all__ = [
    'AutonomousFallDetector',
    'AutonomousFireSmokeDetector', 
    'MultiStreamBatchScheduler',
    'FalseAlarmSuppression',
    'TemporalSequenceAnalyzer',
    'LightweightPoseNet',
    'AUTONOMOUS_ALGORITHMS'
]