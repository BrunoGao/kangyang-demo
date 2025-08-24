#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
多流批处理调度器 - 自主产权核心算法
核心功能：
1. 22路RTSP视频流智能负载均衡
2. 动态资源分配和优先级调度
3. NPU硬件资源池化管理
4. 实时性能监控和自适应优化

算法特点：
- 支持720p@15FPS多路并发处理
- 智能队列管理和流量控制
- 内存池化和GPU/NPU资源复用
- 故障恢复和降级处理机制
"""

import asyncio
import threading
import time
import logging
from typing import Dict, List, Any, Optional, Tuple, Callable
from collections import deque, defaultdict
from dataclasses import dataclass
from enum import Enum
import numpy as np
from concurrent.futures import ThreadPoolExecutor
import queue
import cv2

logger = logging.getLogger(__name__)

class StreamPriority(Enum):
    """流优先级"""
    CRITICAL = 1    # 关键区域 (如病房、楼梯间)
    HIGH = 2        # 高优先级 (如走廊、大厅)
    NORMAL = 3      # 普通优先级 (如花园、休息区)
    LOW = 4         # 低优先级 (如储藏室等)

class ProcessorStatus(Enum):
    """处理器状态"""
    IDLE = "idle"
    PROCESSING = "processing" 
    OVERLOADED = "overloaded"
    ERROR = "error"

@dataclass
class StreamConfig:
    """视频流配置"""
    stream_id: str
    rtsp_url: str
    priority: StreamPriority
    target_fps: int = 15
    resolution: Tuple[int, int] = (1280, 720)
    algorithms: List[str] = None
    region_name: str = ""
    
    def __post_init__(self):
        if self.algorithms is None:
            self.algorithms = ['fall_detection_v2']

@dataclass
class ProcessingTask:
    """处理任务"""
    stream_id: str
    frame: np.ndarray
    timestamp: float
    frame_number: int
    priority: StreamPriority
    algorithms: List[str]
    retry_count: int = 0

@dataclass
class ProcessorResource:
    """处理器资源"""
    processor_id: str
    processor_type: str  # 'cpu', 'gpu', 'npu_ascend', 'npu_cambricon'
    status: ProcessorStatus
    current_load: float
    max_concurrent: int
    current_tasks: int
    total_processed: int
    average_processing_time: float

class MultiStreamBatchScheduler:
    """多流批处理调度器 - 自主产权核心算法"""
    
    def __init__(self, config: Dict[str, Any] = None):
        """
        初始化批处理调度器
        
        Args:
            config: 调度器配置参数
        """
        self.config = config or {}
        
        # 核心配置
        self.max_streams = self.config.get('max_streams', 22)
        self.max_queue_size = self.config.get('max_queue_size', 1000)
        self.processing_timeout = self.config.get('processing_timeout', 5.0)
        self.load_balance_interval = self.config.get('load_balance_interval', 10.0)
        
        # 硬件资源配置
        self.cpu_workers = self.config.get('cpu_workers', 4)
        self.gpu_workers = self.config.get('gpu_workers', 2) 
        self.npu_workers = self.config.get('npu_workers', 4)
        
        # 流管理
        self.active_streams: Dict[str, StreamConfig] = {}
        self.stream_metrics: Dict[str, Dict] = {}
        
        # 任务队列系统
        self.priority_queues = {
            StreamPriority.CRITICAL: queue.PriorityQueue(),
            StreamPriority.HIGH: queue.PriorityQueue(),
            StreamPriority.NORMAL: queue.PriorityQueue(), 
            StreamPriority.LOW: queue.PriorityQueue()
        }
        
        # 处理器资源池
        self.processors: Dict[str, ProcessorResource] = {}
        self.processor_pool = ThreadPoolExecutor(max_workers=self.cpu_workers + self.gpu_workers + self.npu_workers)
        
        # 算法实例池
        self.algorithm_instances = {}
        
        # 调度器状态
        self.is_running = False
        self.scheduler_thread = None
        self.load_balancer_thread = None
        
        # 统计信息
        self.stats = {
            'total_frames_processed': 0,
            'total_processing_time': 0.0,
            'queue_overflow_count': 0,
            'error_count': 0,
            'average_latency': 0.0,
            'throughput_fps': 0.0
        }
        
        # 初始化组件
        self._initialize_processors()
        self._initialize_algorithms()
        
        logger.info(f"多流批处理调度器初始化完成: 最大流数={self.max_streams}, "
                   f"CPU工作器={self.cpu_workers}, GPU工作器={self.gpu_workers}, NPU工作器={self.npu_workers}")
    
    def _initialize_processors(self):
        """初始化处理器资源池"""
        try:
            # CPU处理器
            for i in range(self.cpu_workers):
                processor_id = f"cpu_{i}"
                self.processors[processor_id] = ProcessorResource(
                    processor_id=processor_id,
                    processor_type='cpu',
                    status=ProcessorStatus.IDLE,
                    current_load=0.0,
                    max_concurrent=2,  # CPU可以处理2个并发任务
                    current_tasks=0,
                    total_processed=0,
                    average_processing_time=0.0
                )
            
            # GPU处理器
            for i in range(self.gpu_workers):
                processor_id = f"gpu_{i}"
                self.processors[processor_id] = ProcessorResource(
                    processor_id=processor_id,
                    processor_type='gpu',
                    status=ProcessorStatus.IDLE,
                    current_load=0.0,
                    max_concurrent=4,  # GPU可以处理更多并发任务
                    current_tasks=0,
                    total_processed=0,
                    average_processing_time=0.0
                )
            
            # NPU处理器 (昇腾/寒武纪)
            for i in range(self.npu_workers):
                processor_id = f"npu_{i}"
                npu_type = 'npu_ascend' if i < self.npu_workers // 2 else 'npu_cambricon'
                self.processors[processor_id] = ProcessorResource(
                    processor_id=processor_id,
                    processor_type=npu_type,
                    status=ProcessorStatus.IDLE,
                    current_load=0.0,
                    max_concurrent=6,  # NPU处理能力最强
                    current_tasks=0,
                    total_processed=0,
                    average_processing_time=0.0
                )
            
            logger.info(f"处理器资源池初始化完成: {len(self.processors)}个处理器")
            
        except Exception as e:
            logger.error(f"处理器初始化异常: {e}")
            raise
    
    def _initialize_algorithms(self):
        """初始化算法实例池"""
        try:
            from .fall_detector_v2 import AutonomousFallDetector
            from .fire_smoke_detector_v2 import AutonomousFireSmokeDetector
            
            # 为每种处理器类型创建算法实例
            for processor_type in ['cpu', 'gpu', 'npu_ascend', 'npu_cambricon']:
                self.algorithm_instances[processor_type] = {
                    'fall_detection_v2': AutonomousFallDetector({
                        'use_npu': processor_type.startswith('npu'),
                        'npu_device': processor_type.split('_')[-1] if processor_type.startswith('npu') else None
                    }),
                    'fire_smoke_detection_v2': AutonomousFireSmokeDetector({
                        'use_npu': processor_type.startswith('npu'),
                        'npu_device': processor_type.split('_')[-1] if processor_type.startswith('npu') else None
                    })
                }
            
            logger.info("算法实例池初始化完成")
            
        except Exception as e:
            logger.error(f"算法实例初始化异常: {e}")
            # 创建mock实例作为备用
            self.algorithm_instances = {
                'cpu': {'fall_detection_v2': None, 'fire_smoke_detection_v2': None},
                'gpu': {'fall_detection_v2': None, 'fire_smoke_detection_v2': None},
                'npu_ascend': {'fall_detection_v2': None, 'fire_smoke_detection_v2': None},
                'npu_cambricon': {'fall_detection_v2': None, 'fire_smoke_detection_v2': None}
            }
    
    def start(self):
        """启动调度器"""
        if self.is_running:
            logger.warning("调度器已在运行中")
            return
        
        self.is_running = True
        
        # 启动调度器线程
        self.scheduler_thread = threading.Thread(target=self._scheduler_loop, daemon=True)
        self.scheduler_thread.start()
        
        # 启动负载均衡器线程
        self.load_balancer_thread = threading.Thread(target=self._load_balancer_loop, daemon=True)
        self.load_balancer_thread.start()
        
        logger.info("多流批处理调度器启动完成")
    
    def stop(self):
        """停止调度器"""
        self.is_running = False
        
        if self.scheduler_thread:
            self.scheduler_thread.join(timeout=5.0)
        
        if self.load_balancer_thread:
            self.load_balancer_thread.join(timeout=5.0)
        
        self.processor_pool.shutdown(wait=True)
        
        logger.info("多流批处理调度器已停止")
    
    def add_stream(self, stream_config: StreamConfig) -> bool:
        """添加视频流"""
        try:
            if len(self.active_streams) >= self.max_streams:
                logger.error(f"已达到最大流数量限制: {self.max_streams}")
                return False
            
            if stream_config.stream_id in self.active_streams:
                logger.warning(f"流 {stream_config.stream_id} 已存在")
                return False
            
            self.active_streams[stream_config.stream_id] = stream_config
            self.stream_metrics[stream_config.stream_id] = {
                'frames_processed': 0,
                'processing_errors': 0,
                'average_latency': 0.0,
                'last_frame_time': 0.0,
                'fps': 0.0
            }
            
            logger.info(f"添加视频流: {stream_config.stream_id}, 优先级: {stream_config.priority.name}")
            return True
            
        except Exception as e:
            logger.error(f"添加视频流异常: {e}")
            return False
    
    def remove_stream(self, stream_id: str) -> bool:
        """移除视频流"""
        try:
            if stream_id in self.active_streams:
                del self.active_streams[stream_id]
                del self.stream_metrics[stream_id]
                logger.info(f"移除视频流: {stream_id}")
                return True
            else:
                logger.warning(f"流 {stream_id} 不存在")
                return False
        except Exception as e:
            logger.error(f"移除视频流异常: {e}")
            return False
    
    def submit_frame(self, stream_id: str, frame: np.ndarray, 
                    timestamp: float, frame_number: int) -> bool:
        """提交帧进行处理"""
        try:
            if stream_id not in self.active_streams:
                logger.warning(f"未知流ID: {stream_id}")
                return False
            
            stream_config = self.active_streams[stream_id]
            
            # 创建处理任务
            task = ProcessingTask(
                stream_id=stream_id,
                frame=frame,
                timestamp=timestamp,
                frame_number=frame_number,
                priority=stream_config.priority,
                algorithms=stream_config.algorithms
            )
            
            # 根据优先级添加到相应队列
            priority_queue = self.priority_queues[stream_config.priority]
            
            try:
                # 使用时间戳作为优先级排序（越早的帧优先级越高）
                priority_queue.put((timestamp, task), block=False)
                return True
            except queue.Full:
                self.stats['queue_overflow_count'] += 1
                logger.warning(f"队列已满，丢弃帧: 流={stream_id}, 帧号={frame_number}")
                return False
            
        except Exception as e:
            logger.error(f"提交帧异常: {e}")
            return False
    
    def _scheduler_loop(self):
        """调度器主循环"""
        logger.info("调度器主循环启动")
        
        while self.is_running:
            try:
                # 按优先级顺序处理队列
                task = None
                
                for priority in StreamPriority:
                    priority_queue = self.priority_queues[priority]
                    
                    try:
                        # 非阻塞获取任务
                        priority_timestamp, task = priority_queue.get(block=False)
                        break
                    except queue.Empty:
                        continue
                
                if task is None:
                    # 没有任务时短暂休眠
                    time.sleep(0.01)
                    continue
                
                # 选择最适合的处理器
                processor_id = self._select_best_processor(task)
                
                if processor_id is None:
                    # 没有可用处理器，重新入队或丢弃
                    if task.retry_count < 3:
                        task.retry_count += 1
                        self.priority_queues[task.priority].put((task.timestamp, task))
                    else:
                        logger.warning(f"任务重试次数超限，丢弃: 流={task.stream_id}")
                    continue
                
                # 异步提交处理任务
                future = self.processor_pool.submit(
                    self._process_task, processor_id, task
                )
                
                # 更新处理器状态
                processor = self.processors[processor_id]
                processor.current_tasks += 1
                processor.status = ProcessorStatus.PROCESSING
                processor.current_load = processor.current_tasks / processor.max_concurrent
                
            except Exception as e:
                logger.error(f"调度器循环异常: {e}")
                time.sleep(0.1)
        
        logger.info("调度器主循环结束")
    
    def _select_best_processor(self, task: ProcessingTask) -> Optional[str]:
        """选择最佳处理器"""
        available_processors = []
        
        for processor_id, processor in self.processors.items():
            if (processor.status != ProcessorStatus.ERROR and 
                processor.current_tasks < processor.max_concurrent):
                available_processors.append((processor_id, processor))
        
        if not available_processors:
            return None
        
        # 根据负载和处理器性能选择最佳处理器
        best_processor_id = None
        best_score = float('inf')
        
        for processor_id, processor in available_processors:
            # 计算评分 (负载 + 处理时间 + 硬件类型权重)
            load_score = processor.current_load
            time_score = processor.average_processing_time / 100.0  # 归一化
            
            # 硬件类型权重 (NPU > GPU > CPU)
            hardware_weight = {
                'npu_ascend': 0.1,
                'npu_cambricon': 0.1, 
                'gpu': 0.3,
                'cpu': 1.0
            }.get(processor.processor_type, 1.0)
            
            # 优先级权重
            priority_weight = {
                StreamPriority.CRITICAL: 0.1,
                StreamPriority.HIGH: 0.3,
                StreamPriority.NORMAL: 0.7,
                StreamPriority.LOW: 1.0
            }.get(task.priority, 1.0)
            
            score = (load_score + time_score) * hardware_weight * priority_weight
            
            if score < best_score:
                best_score = score
                best_processor_id = processor_id
        
        return best_processor_id
    
    def _process_task(self, processor_id: str, task: ProcessingTask) -> Optional[Dict[str, Any]]:
        """处理单个任务"""
        start_time = time.time()
        processor = self.processors[processor_id]
        
        try:
            # 获取算法实例
            processor_type = processor.processor_type
            if processor_type.startswith('npu'):
                processor_type_key = processor_type
            else:
                processor_type_key = processor_type
            
            results = []
            
            # 执行算法
            for algorithm_name in task.algorithms:
                algorithm_instance = self.algorithm_instances[processor_type_key].get(algorithm_name)
                
                if algorithm_instance is None:
                    logger.warning(f"算法实例不存在: {algorithm_name}")
                    continue
                
                try:
                    result = algorithm_instance.detect(
                        task.frame, task.timestamp, task.frame_number
                    )
                    
                    if result:
                        result['processor_id'] = processor_id
                        result['processing_latency'] = time.time() - start_time
                        results.append(result)
                        
                except Exception as e:
                    logger.error(f"算法执行异常: {algorithm_name}, {e}")
                    continue
            
            # 更新统计信息
            processing_time = time.time() - start_time
            self._update_task_stats(processor_id, task.stream_id, processing_time, len(results) > 0)
            
            return {
                'stream_id': task.stream_id,
                'frame_number': task.frame_number,
                'timestamp': task.timestamp,
                'processor_id': processor_id,
                'processing_time': processing_time,
                'results': results
            } if results else None
            
        except Exception as e:
            logger.error(f"任务处理异常: processor={processor_id}, stream={task.stream_id}, error={e}")
            self.stats['error_count'] += 1
            return None
            
        finally:
            # 更新处理器状态
            processor.current_tasks = max(0, processor.current_tasks - 1)
            processor.current_load = processor.current_tasks / processor.max_concurrent
            
            if processor.current_tasks == 0:
                processor.status = ProcessorStatus.IDLE
    
    def _update_task_stats(self, processor_id: str, stream_id: str, 
                          processing_time: float, success: bool):
        """更新任务统计信息"""
        # 更新处理器统计
        processor = self.processors[processor_id]
        processor.total_processed += 1
        
        # 更新平均处理时间
        if processor.total_processed == 1:
            processor.average_processing_time = processing_time
        else:
            alpha = 0.1  # 指数移动平均
            processor.average_processing_time = (
                alpha * processing_time + 
                (1 - alpha) * processor.average_processing_time
            )
        
        # 更新流统计
        if stream_id in self.stream_metrics:
            stream_stats = self.stream_metrics[stream_id]
            stream_stats['frames_processed'] += 1
            
            if not success:
                stream_stats['processing_errors'] += 1
            
            # 更新平均延迟
            if stream_stats['frames_processed'] == 1:
                stream_stats['average_latency'] = processing_time
            else:
                alpha = 0.1
                stream_stats['average_latency'] = (
                    alpha * processing_time + 
                    (1 - alpha) * stream_stats['average_latency']
                )
            
            # 更新FPS
            current_time = time.time()
            if stream_stats['last_frame_time'] > 0:
                frame_interval = current_time - stream_stats['last_frame_time']
                stream_stats['fps'] = 1.0 / frame_interval if frame_interval > 0 else 0
            stream_stats['last_frame_time'] = current_time
        
        # 更新全局统计
        self.stats['total_frames_processed'] += 1
        self.stats['total_processing_time'] += processing_time
        
        if self.stats['total_frames_processed'] > 0:
            self.stats['average_latency'] = (
                self.stats['total_processing_time'] / self.stats['total_frames_processed']
            )
            
            # 计算吞吐量
            total_runtime = time.time() - getattr(self, 'start_time', time.time())
            if total_runtime > 0:
                self.stats['throughput_fps'] = self.stats['total_frames_processed'] / total_runtime
    
    def _load_balancer_loop(self):
        """负载均衡器循环"""
        logger.info("负载均衡器循环启动")
        
        while self.is_running:
            try:
                # 检查处理器状态
                self._check_processor_health()
                
                # 动态调整队列优先级
                self._adjust_queue_priorities()
                
                # 记录性能指标
                self._log_performance_metrics()
                
                time.sleep(self.load_balance_interval)
                
            except Exception as e:
                logger.error(f"负载均衡器异常: {e}")
                time.sleep(self.load_balance_interval)
        
        logger.info("负载均衡器循环结束")
    
    def _check_processor_health(self):
        """检查处理器健康状态"""
        for processor_id, processor in self.processors.items():
            # 检查是否过载
            if processor.current_load > 0.9:
                if processor.status != ProcessorStatus.OVERLOADED:
                    processor.status = ProcessorStatus.OVERLOADED
                    logger.warning(f"处理器过载: {processor_id}, 负载: {processor.current_load:.2f}")
            
            # 检查是否恢复正常
            elif processor.current_load < 0.7 and processor.status == ProcessorStatus.OVERLOADED:
                processor.status = ProcessorStatus.PROCESSING if processor.current_tasks > 0 else ProcessorStatus.IDLE
                logger.info(f"处理器负载恢复: {processor_id}, 负载: {processor.current_load:.2f}")
    
    def _adjust_queue_priorities(self):
        """动态调整队列优先级"""
        # 检查各优先级队列的积压情况
        queue_sizes = {}
        for priority, priority_queue in self.priority_queues.items():
            queue_sizes[priority] = priority_queue.qsize()
        
        # 如果高优先级队列积压严重，考虑临时调整调度策略
        if queue_sizes.get(StreamPriority.CRITICAL, 0) > 50:
            logger.warning("关键优先级队列积压严重，建议增加处理资源")
        
        if queue_sizes.get(StreamPriority.HIGH, 0) > 100:
            logger.warning("高优先级队列积压严重")
    
    def _log_performance_metrics(self):
        """记录性能指标"""
        if logger.isEnabledFor(logging.INFO):
            # 处理器状态统计
            processor_stats = defaultdict(int)
            for processor in self.processors.values():
                processor_stats[processor.status.value] += 1
            
            # 队列状态统计
            queue_stats = {
                priority.name: self.priority_queues[priority].qsize() 
                for priority in StreamPriority
            }
            
            logger.info(f"调度器状态 - 处理器: {dict(processor_stats)}, "
                       f"队列: {queue_stats}, "
                       f"吞吐量: {self.stats['throughput_fps']:.1f}FPS, "
                       f"平均延迟: {self.stats['average_latency']*1000:.1f}ms")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取调度器统计信息"""
        # 处理器状态统计
        processor_stats = {
            'total_processors': len(self.processors),
            'by_type': defaultdict(int),
            'by_status': defaultdict(int),
            'average_load': 0.0
        }
        
        total_load = 0.0
        for processor in self.processors.values():
            processor_stats['by_type'][processor.processor_type] += 1
            processor_stats['by_status'][processor.status.value] += 1
            total_load += processor.current_load
        
        processor_stats['average_load'] = total_load / len(self.processors) if self.processors else 0
        
        # 流状态统计
        stream_stats = {
            'active_streams': len(self.active_streams),
            'by_priority': defaultdict(int),
            'total_fps': sum(metrics['fps'] for metrics in self.stream_metrics.values())
        }
        
        for stream_config in self.active_streams.values():
            stream_stats['by_priority'][stream_config.priority.name] += 1
        
        # 队列状态统计
        queue_stats = {
            priority.name: self.priority_queues[priority].qsize() 
            for priority in StreamPriority
        }
        
        return {
            'scheduler_type': 'multi_stream_batch_scheduler',
            'version': '2.0.0',
            'is_running': self.is_running,
            'max_streams': self.max_streams,
            'processor_stats': dict(processor_stats),
            'stream_stats': dict(stream_stats), 
            'queue_stats': queue_stats,
            'performance_stats': self.stats.copy(),
            'algorithm_features': [
                'intelligent_load_balancing',
                'priority_based_scheduling',
                'dynamic_resource_allocation',
                'npu_resource_pooling',
                'fault_recovery_mechanism'
            ],
            'copyright': '自主产权算法 - 康养AI团队'
        }
    
    def get_stream_metrics(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """获取特定流的性能指标"""
        if stream_id not in self.stream_metrics:
            return None
        
        return self.stream_metrics[stream_id].copy()
    
    def get_processor_metrics(self, processor_id: str) -> Optional[Dict[str, Any]]:
        """获取特定处理器的性能指标"""
        if processor_id not in self.processors:
            return None
        
        processor = self.processors[processor_id]
        return {
            'processor_id': processor.processor_id,
            'processor_type': processor.processor_type,
            'status': processor.status.value,
            'current_load': processor.current_load,
            'max_concurrent': processor.max_concurrent,
            'current_tasks': processor.current_tasks,
            'total_processed': processor.total_processed,
            'average_processing_time': processor.average_processing_time
        }
    
    def adjust_stream_priority(self, stream_id: str, new_priority: StreamPriority) -> bool:
        """动态调整流优先级"""
        try:
            if stream_id in self.active_streams:
                old_priority = self.active_streams[stream_id].priority
                self.active_streams[stream_id].priority = new_priority
                logger.info(f"流 {stream_id} 优先级调整: {old_priority.name} -> {new_priority.name}")
                return True
            else:
                logger.warning(f"流 {stream_id} 不存在")
                return False
        except Exception as e:
            logger.error(f"调整流优先级异常: {e}")
            return False