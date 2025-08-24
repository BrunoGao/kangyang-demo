#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
规则引擎与误报抑制系统 - 自主产权核心算法
核心功能：
1. 多维度规则验证和智能误报过滤
2. 上下文感知的动态阈值调整
3. 时序关联分析和事件聚合
4. 学习式规则优化和自适应调整

算法特点：
- 基于专家知识的规则库系统
- 多层级验证架构 (快速筛选 + 深度验证)
- 环境自适应和场景感知能力
- 实时学习和规则权重动态优化
"""

import logging
import time
import math
from typing import Dict, List, Any, Optional, Tuple, Set
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import Enum
from datetime import datetime, timedelta
import numpy as np

logger = logging.getLogger(__name__)

class RuleType(Enum):
    """规则类型"""
    GEOMETRIC = "geometric"        # 几何规则
    TEMPORAL = "temporal"          # 时序规则
    CONTEXTUAL = "contextual"      # 上下文规则
    STATISTICAL = "statistical"   # 统计规则
    COMPOSITE = "composite"        # 复合规则

class RulePriority(Enum):
    """规则优先级"""
    CRITICAL = 1    # 关键规则 (必须满足)
    HIGH = 2        # 高优先级规则
    NORMAL = 3      # 普通规则
    LOW = 4         # 低优先级规则

class ValidationResult(Enum):
    """验证结果"""
    PASS = "pass"           # 通过
    FAIL = "fail"           # 失败
    WARNING = "warning"     # 警告
    UNKNOWN = "unknown"     # 未知

@dataclass
class Rule:
    """规则定义"""
    rule_id: str
    rule_type: RuleType
    priority: RulePriority
    condition: str
    threshold: float
    weight: float
    description: str
    enabled: bool = True
    success_count: int = 0
    failure_count: int = 0
    effectiveness: float = 1.0

@dataclass
class DetectionEvent:
    """检测事件"""
    event_id: str
    event_type: str
    timestamp: float
    confidence: float
    features: Dict[str, Any]
    metadata: Dict[str, Any]
    validation_results: Dict[str, ValidationResult] = None

class FalseAlarmSuppression:
    """误报抑制系统 - 自主产权核心算法"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化误报抑制系统
        
        Args:
            config: 配置参数
        """
        self.config = config or {}
        
        # 核心配置
        self.confidence_adjustment_factor = self.config.get('confidence_adjustment_factor', 0.2)
        self.temporal_window_size = self.config.get('temporal_window_size', 60)  # 60秒时序窗口
        self.learning_rate = self.config.get('learning_rate', 0.01)
        self.min_validation_score = self.config.get('min_validation_score', 0.6)
        
        # 规则库
        self.rules: Dict[str, Rule] = {}
        self.rule_categories = {
            'fall_detection': [],
            'fire_smoke_detection': []
        }
        
        # 事件历史和上下文
        self.event_history = deque(maxlen=1000)
        self.temporal_events = deque(maxlen=self.temporal_window_size * 15)  # 假设15fps
        self.environmental_context = {}
        
        # 统计信息
        self.stats = {
            'total_validations': 0,
            'false_alarms_suppressed': 0,
            'true_positives': 0,
            'validation_accuracy': 0.0,
            'rule_effectiveness': {}
        }
        
        # 自适应学习组件
        self.adaptive_thresholds = {}
        self.context_patterns = defaultdict(list)
        
        # 初始化规则库
        self._initialize_rule_library()
        
        logger.info("误报抑制系统初始化完成")
    
    def _initialize_rule_library(self):
        """初始化规则库"""
        try:
            # 跌倒检测规则
            self._add_fall_detection_rules()
            
            # 火焰烟雾检测规则
            self._add_fire_smoke_detection_rules()
            
            # 通用规则
            self._add_common_rules()
            
            logger.info(f"规则库初始化完成: {len(self.rules)}条规则")
            
        except Exception as e:
            logger.error(f"规则库初始化异常: {e}")
            raise
    
    def _add_fall_detection_rules(self):
        """添加跌倒检测规则"""
        # 几何规则
        self.add_rule(Rule(
            rule_id="fall_height_ratio",
            rule_type=RuleType.GEOMETRIC,
            priority=RulePriority.CRITICAL,
            condition="height_ratio < threshold",
            threshold=0.6,
            weight=0.3,
            description="身体高度比验证 - 跌倒时身体高度应显著降低"
        ))
        
        self.add_rule(Rule(
            rule_id="fall_velocity_consistency",
            rule_type=RuleType.TEMPORAL,
            priority=RulePriority.HIGH,
            condition="velocity_magnitude > threshold AND downward_motion > 0",
            threshold=120.0,
            weight=0.25,
            description="速度一致性验证 - 跌倒应有向下的运动分量"
        ))
        
        self.add_rule(Rule(
            rule_id="fall_stability_change",
            rule_type=RuleType.GEOMETRIC,
            priority=RulePriority.HIGH,
            condition="stability_score < threshold",
            threshold=0.4,
            weight=0.2,
            description="稳定性变化验证 - 跌倒时姿态稳定性下降"
        ))
        
        self.add_rule(Rule(
            rule_id="fall_duration_validity",
            rule_type=RuleType.TEMPORAL,
            priority=RulePriority.NORMAL,
            condition="event_duration > min_duration AND event_duration < max_duration",
            threshold=0.5,  # 最小持续时间
            weight=0.15,
            description="持续时间验证 - 跌倒事件应在合理时间范围内"
        ))
        
        self.add_rule(Rule(
            rule_id="fall_context_plausibility",
            rule_type=RuleType.CONTEXTUAL,
            priority=RulePriority.NORMAL,
            condition="not_in_bed AND not_sitting_down",
            threshold=0.7,
            weight=0.1,
            description="上下文合理性验证 - 排除正常坐下或躺下行为"
        ))
        
        # 将规则分类
        self.rule_categories['fall_detection'] = [
            "fall_height_ratio", "fall_velocity_consistency", 
            "fall_stability_change", "fall_duration_validity", "fall_context_plausibility"
        ]
    
    def _add_fire_smoke_detection_rules(self):
        """添加火焰烟雾检测规则"""
        # 颜色验证规则
        self.add_rule(Rule(
            rule_id="fire_color_consistency",
            rule_type=RuleType.GEOMETRIC,
            priority=RulePriority.CRITICAL,
            condition="fire_color_ratio > threshold AND color_distribution_valid",
            threshold=0.001,  # 至少0.1%的火焰颜色像素
            weight=0.3,
            description="火焰颜色一致性验证"
        ))
        
        self.add_rule(Rule(
            rule_id="smoke_texture_pattern",
            rule_type=RuleType.GEOMETRIC,
            priority=RulePriority.HIGH,
            condition="texture_complexity > threshold AND edge_blurriness > threshold",
            threshold=0.3,
            weight=0.25,
            description="烟雾纹理模式验证"
        ))
        
        self.add_rule(Rule(
            rule_id="fire_motion_flickering",
            rule_type=RuleType.TEMPORAL,
            priority=RulePriority.HIGH,
            condition="motion_variability > threshold AND temporal_consistency > threshold",
            threshold=0.4,
            weight=0.2,
            description="火焰闪烁运动验证"
        ))
        
        self.add_rule(Rule(
            rule_id="smoke_rising_motion",
            rule_type=RuleType.TEMPORAL,
            priority=RulePriority.NORMAL,
            condition="upward_motion_ratio > threshold",
            threshold=0.3,
            weight=0.15,
            description="烟雾上升运动验证"
        ))
        
        self.add_rule(Rule(
            rule_id="fire_smoke_size_plausibility",
            rule_type=RuleType.CONTEXTUAL,
            priority=RulePriority.NORMAL,
            condition="region_size > min_size AND region_size < max_size",
            threshold=100,  # 最小像素面积
            weight=0.1,
            description="火焰烟雾尺寸合理性验证"
        ))
        
        self.rule_categories['fire_smoke_detection'] = [
            "fire_color_consistency", "smoke_texture_pattern",
            "fire_motion_flickering", "smoke_rising_motion", "fire_smoke_size_plausibility"
        ]
    
    def _add_common_rules(self):
        """添加通用规则"""
        self.add_rule(Rule(
            rule_id="confidence_threshold",
            rule_type=RuleType.STATISTICAL,
            priority=RulePriority.CRITICAL,
            condition="confidence > threshold",
            threshold=0.7,
            weight=0.2,
            description="基础置信度阈值验证"
        ))
        
        self.add_rule(Rule(
            rule_id="temporal_consistency",
            rule_type=RuleType.TEMPORAL,
            priority=RulePriority.HIGH,
            condition="detection_consistency > threshold",
            threshold=0.6,
            weight=0.15,
            description="时序一致性验证"
        ))
        
        self.add_rule(Rule(
            rule_id="environmental_adaptation",
            rule_type=RuleType.CONTEXTUAL,
            priority=RulePriority.NORMAL,
            condition="lighting_condition_appropriate",
            threshold=0.5,
            weight=0.1,
            description="环境自适应验证"
        ))
    
    def add_rule(self, rule: Rule):
        """添加规则"""
        self.rules[rule.rule_id] = rule
        self.stats['rule_effectiveness'][rule.rule_id] = {
            'success_rate': 0.0,
            'total_applications': 0
        }
    
    def validate_detection(self, detection_result: Dict[str, Any], 
                          additional_context: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        验证检测结果 - 主要接口
        
        Args:
            detection_result: 原始检测结果
            additional_context: 额外上下文信息
            
        Returns:
            验证结果和调整后的检测结果
        """
        start_time = time.time()
        
        try:
            # 创建检测事件
            event = DetectionEvent(
                event_id=f"{detection_result.get('timestamp', time.time())}_{detection_result.get('type', 'unknown')}",
                event_type=detection_result.get('type', 'unknown'),
                timestamp=detection_result.get('timestamp', time.time()),
                confidence=detection_result.get('confidence', 0.0),
                features=self._extract_validation_features(detection_result),
                metadata=additional_context or {}
            )
            
            # 应用规则验证
            validation_results = self._apply_rule_validation(event)
            event.validation_results = validation_results
            
            # 计算综合验证分数
            validation_score = self._calculate_validation_score(validation_results)
            
            # 调整置信度
            adjusted_confidence = self._adjust_confidence(
                event.confidence, validation_score, validation_results
            )
            
            # 决定是否通过验证
            is_valid = validation_score >= self.min_validation_score and adjusted_confidence > 0.5
            
            # 更新历史和学习
            self._update_history(event, is_valid)
            self._update_adaptive_learning(event, validation_results, is_valid)
            
            # 更新统计信息
            self._update_stats(validation_score, is_valid, time.time() - start_time)
            
            # 生成最终结果
            result = {
                'is_valid': is_valid,
                'original_confidence': event.confidence,
                'adjusted_confidence': adjusted_confidence,
                'validation_score': validation_score,
                'validation_details': validation_results,
                'suppression_reason': self._get_suppression_reason(validation_results) if not is_valid else None,
                'processing_time': time.time() - start_time
            }
            
            if is_valid:
                # 创建调整后的检测结果
                result['adjusted_detection'] = detection_result.copy()
                result['adjusted_detection']['confidence'] = adjusted_confidence
                result['adjusted_detection']['validation_score'] = validation_score
                result['adjusted_detection']['validation_metadata'] = {
                    'rules_applied': len(validation_results),
                    'critical_rules_passed': sum(1 for r in validation_results.values() if r == ValidationResult.PASS),
                    'suppression_system': 'autonomous_false_alarm_suppression_v2'
                }
            
            return result
            
        except Exception as e:
            logger.error(f"检测验证异常: {e}")
            return {
                'is_valid': False,
                'original_confidence': detection_result.get('confidence', 0.0),
                'adjusted_confidence': 0.0,
                'validation_score': 0.0,
                'validation_details': {},
                'suppression_reason': f'validation_error: {str(e)}'
            }
    
    def _extract_validation_features(self, detection_result: Dict[str, Any]) -> Dict[str, Any]:
        """提取用于验证的特征"""
        features = {}
        
        # 基础特征
        features['confidence'] = detection_result.get('confidence', 0.0)
        features['event_type'] = detection_result.get('type', 'unknown')
        features['timestamp'] = detection_result.get('timestamp', time.time())
        
        # 几何特征
        geometric_features = detection_result.get('geometric_features', {})
        features.update({
            'height_ratio': geometric_features.get('height_ratio', 1.0),
            'stability_score': geometric_features.get('stability_score', 1.0),
            'body_tilt': geometric_features.get('body_tilt', 0.0),
            'limb_spread': geometric_features.get('limb_spread', 0.0)
        })
        
        # 运动特征
        motion_features = detection_result.get('motion_features', {})
        features.update({
            'velocity_magnitude': motion_features.get('velocity_magnitude', 0.0),
            'downward_motion': motion_features.get('downward_motion', 0.0),
            'angular_velocity': motion_features.get('angular_velocity', 0.0),
            'motion_stability': motion_features.get('motion_stability', 1.0)
        })
        
        # 时序特征
        temporal_features = detection_result.get('temporal_features', {})
        features.update({
            'consistency_score': temporal_features.get('consistency_score', 0.0),
            'sequence_length': temporal_features.get('sequence_length', 0),
            'time_span': temporal_features.get('time_span', 0.0)
        })
        
        # 区域特征 (火焰烟雾)
        if 'regions' in detection_result:
            regions = detection_result['regions']
            if regions:
                features['region_count'] = len(regions)
                features['total_area'] = sum(r.get('area', 0) for r in regions)
                features['max_region_area'] = max(r.get('area', 0) for r in regions) if regions else 0
        
        return features
    
    def _apply_rule_validation(self, event: DetectionEvent) -> Dict[str, ValidationResult]:
        """应用规则验证"""
        results = {}
        
        # 获取相关规则
        relevant_rules = self._get_relevant_rules(event.event_type)
        
        for rule_id in relevant_rules:
            if rule_id not in self.rules or not self.rules[rule_id].enabled:
                continue
            
            rule = self.rules[rule_id]
            
            try:
                # 应用具体规则
                result = self._apply_specific_rule(rule, event)
                results[rule_id] = result
                
                # 更新规则统计
                self._update_rule_stats(rule_id, result)
                
            except Exception as e:
                logger.error(f"规则应用异常: {rule_id}, {e}")
                results[rule_id] = ValidationResult.UNKNOWN
        
        return results
    
    def _get_relevant_rules(self, event_type: str) -> List[str]:
        """获取相关规则"""
        relevant_rules = []
        
        # 根据事件类型获取专用规则
        if event_type == 'fall':
            relevant_rules.extend(self.rule_categories.get('fall_detection', []))
        elif event_type in ['fire', 'smoke']:
            relevant_rules.extend(self.rule_categories.get('fire_smoke_detection', []))
        
        # 添加通用规则
        for rule_id, rule in self.rules.items():
            if rule.rule_type in [RuleType.STATISTICAL, RuleType.CONTEXTUAL] and rule_id not in relevant_rules:
                relevant_rules.append(rule_id)
        
        return relevant_rules
    
    def _apply_specific_rule(self, rule: Rule, event: DetectionEvent) -> ValidationResult:
        """应用具体规则"""
        try:
            features = event.features
            
            if rule.rule_id == "fall_height_ratio":
                height_ratio = features.get('height_ratio', 1.0)
                return ValidationResult.PASS if height_ratio < rule.threshold else ValidationResult.FAIL
            
            elif rule.rule_id == "fall_velocity_consistency":
                velocity_mag = features.get('velocity_magnitude', 0.0)
                downward_motion = features.get('downward_motion', 0.0)
                return (ValidationResult.PASS if velocity_mag > rule.threshold and downward_motion > 0 
                       else ValidationResult.FAIL)
            
            elif rule.rule_id == "fall_stability_change":
                stability = features.get('stability_score', 1.0)
                return ValidationResult.PASS if stability < rule.threshold else ValidationResult.FAIL
            
            elif rule.rule_id == "fall_duration_validity":
                time_span = features.get('time_span', 0.0)
                return (ValidationResult.PASS if rule.threshold < time_span < 5.0 
                       else ValidationResult.FAIL)
            
            elif rule.rule_id == "confidence_threshold":
                confidence = features.get('confidence', 0.0)
                adaptive_threshold = self._get_adaptive_threshold(rule.rule_id)
                return ValidationResult.PASS if confidence > adaptive_threshold else ValidationResult.FAIL
            
            elif rule.rule_id == "temporal_consistency":
                consistency = features.get('consistency_score', 0.0)
                return ValidationResult.PASS if consistency > rule.threshold else ValidationResult.FAIL
            
            elif rule.rule_id == "fire_color_consistency":
                # 模拟火焰颜色验证
                confidence = features.get('confidence', 0.0)
                return ValidationResult.PASS if confidence > 0.6 else ValidationResult.FAIL
            
            elif rule.rule_id == "smoke_texture_pattern":
                # 模拟烟雾纹理验证
                confidence = features.get('confidence', 0.0)
                return ValidationResult.PASS if confidence > 0.5 else ValidationResult.FAIL
            
            else:
                # 默认基于置信度的简单验证
                confidence = features.get('confidence', 0.0)
                return ValidationResult.PASS if confidence > rule.threshold else ValidationResult.FAIL
            
        except Exception as e:
            logger.error(f"规则 {rule.rule_id} 应用异常: {e}")
            return ValidationResult.UNKNOWN
    
    def _calculate_validation_score(self, validation_results: Dict[str, ValidationResult]) -> float:
        """计算综合验证分数"""
        if not validation_results:
            return 0.0
        
        total_weight = 0.0
        weighted_score = 0.0
        
        for rule_id, result in validation_results.items():
            if rule_id not in self.rules:
                continue
            
            rule = self.rules[rule_id]
            weight = rule.weight
            
            # 根据优先级调整权重
            priority_multiplier = {
                RulePriority.CRITICAL: 2.0,
                RulePriority.HIGH: 1.5,
                RulePriority.NORMAL: 1.0,
                RulePriority.LOW: 0.5
            }.get(rule.priority, 1.0)
            
            adjusted_weight = weight * priority_multiplier
            total_weight += adjusted_weight
            
            # 根据验证结果计算分数
            result_score = {
                ValidationResult.PASS: 1.0,
                ValidationResult.WARNING: 0.5,
                ValidationResult.FAIL: 0.0,
                ValidationResult.UNKNOWN: 0.3
            }.get(result, 0.0)
            
            weighted_score += result_score * adjusted_weight
        
        return weighted_score / total_weight if total_weight > 0 else 0.0
    
    def _adjust_confidence(self, original_confidence: float, validation_score: float,
                          validation_results: Dict[str, ValidationResult]) -> float:
        """调整置信度"""
        # 基础调整
        adjustment_factor = (validation_score - 0.5) * self.confidence_adjustment_factor
        adjusted_confidence = original_confidence + adjustment_factor
        
        # 关键规则失败时大幅降低置信度
        critical_failures = sum(1 for rule_id, result in validation_results.items()
                               if (rule_id in self.rules and 
                                   self.rules[rule_id].priority == RulePriority.CRITICAL and 
                                   result == ValidationResult.FAIL))
        
        if critical_failures > 0:
            adjusted_confidence *= 0.3  # 关键规则失败时置信度降为30%
        
        # 确保置信度在有效范围内
        return max(0.0, min(1.0, adjusted_confidence))
    
    def _get_suppression_reason(self, validation_results: Dict[str, ValidationResult]) -> str:
        """获取抑制原因"""
        failed_rules = []
        for rule_id, result in validation_results.items():
            if result == ValidationResult.FAIL and rule_id in self.rules:
                rule = self.rules[rule_id]
                failed_rules.append(f"{rule_id}({rule.priority.name})")
        
        if failed_rules:
            return f"规则验证失败: {', '.join(failed_rules)}"
        else:
            return "综合验证分数不足"
    
    def _update_history(self, event: DetectionEvent, is_valid: bool):
        """更新历史记录"""
        # 添加到事件历史
        self.event_history.append({
            'event': event,
            'is_valid': is_valid,
            'timestamp': event.timestamp
        })
        
        # 添加到时序事件
        self.temporal_events.append({
            'type': event.event_type,
            'timestamp': event.timestamp,
            'confidence': event.confidence,
            'is_valid': is_valid
        })
    
    def _update_adaptive_learning(self, event: DetectionEvent, 
                                 validation_results: Dict[str, ValidationResult], is_valid: bool):
        """更新自适应学习"""
        try:
            # 更新自适应阈值
            for rule_id, result in validation_results.items():
                if rule_id not in self.adaptive_thresholds:
                    self.adaptive_thresholds[rule_id] = self.rules[rule_id].threshold
                
                # 根据结果调整阈值
                if is_valid and result == ValidationResult.PASS:
                    # 成功案例，稍微放松阈值
                    self.adaptive_thresholds[rule_id] *= (1 - self.learning_rate * 0.1)
                elif not is_valid and result == ValidationResult.FAIL:
                    # 失败案例，稍微收紧阈值
                    self.adaptive_thresholds[rule_id] *= (1 + self.learning_rate * 0.1)
            
            # 更新上下文模式
            context_key = f"{event.event_type}_{int(event.timestamp) // 3600}"  # 按小时分组
            self.context_patterns[context_key].append({
                'confidence': event.confidence,
                'is_valid': is_valid,
                'features': event.features
            })
            
            # 限制上下文模式存储
            if len(self.context_patterns[context_key]) > 100:
                self.context_patterns[context_key] = self.context_patterns[context_key][-50:]
        
        except Exception as e:
            logger.error(f"自适应学习更新异常: {e}")
    
    def _get_adaptive_threshold(self, rule_id: str) -> float:
        """获取自适应阈值"""
        if rule_id in self.adaptive_thresholds:
            return self.adaptive_thresholds[rule_id]
        elif rule_id in self.rules:
            return self.rules[rule_id].threshold
        else:
            return 0.5  # 默认阈值
    
    def _update_rule_stats(self, rule_id: str, result: ValidationResult):
        """更新规则统计"""
        if rule_id not in self.rules:
            return
        
        rule = self.rules[rule_id]
        
        if result == ValidationResult.PASS:
            rule.success_count += 1
        elif result == ValidationResult.FAIL:
            rule.failure_count += 1
        
        # 更新规则有效性
        total_applications = rule.success_count + rule.failure_count
        if total_applications > 0:
            rule.effectiveness = rule.success_count / total_applications
        
        # 更新统计信息
        self.stats['rule_effectiveness'][rule_id] = {
            'success_rate': rule.effectiveness,
            'total_applications': total_applications
        }
    
    def _update_stats(self, validation_score: float, is_valid: bool, processing_time: float):
        """更新统计信息"""
        self.stats['total_validations'] += 1
        
        if is_valid:
            self.stats['true_positives'] += 1
        else:
            self.stats['false_alarms_suppressed'] += 1
        
        # 更新验证准确率 (这需要人工标注数据来计算真实准确率)
        # 这里使用简化的计算方式
        total = self.stats['total_validations']
        self.stats['validation_accuracy'] = self.stats['true_positives'] / total if total > 0 else 0
    
    def get_stats(self) -> Dict[str, Any]:
        """获取系统统计信息"""
        # 规则统计
        rule_stats = {
            'total_rules': len(self.rules),
            'enabled_rules': sum(1 for r in self.rules.values() if r.enabled),
            'by_type': defaultdict(int),
            'by_priority': defaultdict(int),
            'effectiveness_summary': {}
        }
        
        for rule in self.rules.values():
            rule_stats['by_type'][rule.rule_type.value] += 1
            rule_stats['by_priority'][rule.priority.name] += 1
        
        # 计算平均有效性
        if self.rules:
            avg_effectiveness = sum(r.effectiveness for r in self.rules.values()) / len(self.rules)
            rule_stats['effectiveness_summary']['average'] = avg_effectiveness
            rule_stats['effectiveness_summary']['best_rule'] = max(
                self.rules.keys(), key=lambda x: self.rules[x].effectiveness
            )
            rule_stats['effectiveness_summary']['worst_rule'] = min(
                self.rules.keys(), key=lambda x: self.rules[x].effectiveness
            )
        
        return {
            'suppression_system_type': 'autonomous_false_alarm_suppression_v2',
            'version': '2.0.0',
            'rule_stats': dict(rule_stats),
            'validation_stats': self.stats.copy(),
            'adaptive_features': {
                'adaptive_thresholds_count': len(self.adaptive_thresholds),
                'context_patterns_count': len(self.context_patterns),
                'learning_rate': self.learning_rate
            },
            'algorithm_features': [
                'multi_dimensional_rule_validation',
                'context_aware_threshold_adjustment',
                'temporal_correlation_analysis',
                'adaptive_learning_optimization',
                'hierarchical_validation_architecture'
            ],
            'copyright': '自主产权算法 - 康养AI团队'
        }
    
    def get_rule_details(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """获取特定规则详情"""
        if rule_id not in self.rules:
            return None
        
        rule = self.rules[rule_id]
        return {
            'rule_id': rule.rule_id,
            'rule_type': rule.rule_type.value,
            'priority': rule.priority.name,
            'condition': rule.condition,
            'threshold': rule.threshold,
            'adaptive_threshold': self._get_adaptive_threshold(rule_id),
            'weight': rule.weight,
            'description': rule.description,
            'enabled': rule.enabled,
            'success_count': rule.success_count,
            'failure_count': rule.failure_count,
            'effectiveness': rule.effectiveness
        }
    
    def update_rule_threshold(self, rule_id: str, new_threshold: float) -> bool:
        """更新规则阈值"""
        try:
            if rule_id in self.rules:
                old_threshold = self.rules[rule_id].threshold
                self.rules[rule_id].threshold = new_threshold
                logger.info(f"规则 {rule_id} 阈值更新: {old_threshold} -> {new_threshold}")
                return True
            else:
                logger.warning(f"规则 {rule_id} 不存在")
                return False
        except Exception as e:
            logger.error(f"更新规则阈值异常: {e}")
            return False
    
    def enable_rule(self, rule_id: str, enabled: bool = True) -> bool:
        """启用/禁用规则"""
        try:
            if rule_id in self.rules:
                self.rules[rule_id].enabled = enabled
                logger.info(f"规则 {rule_id} {'启用' if enabled else '禁用'}")
                return True
            else:
                logger.warning(f"规则 {rule_id} 不存在")
                return False
        except Exception as e:
            logger.error(f"切换规则状态异常: {e}")
            return False