#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频处理模块
支持真实跌倒和烟雾视频的检测与告警
"""

import os
import time
import json
import base64
from datetime import datetime
from typing import List, Dict, Optional, Callable
import threading
import queue
import logging

# 模拟OpenCV功能 (在没有OpenCV环境中)
class MockCV2:
    """模拟OpenCV功能"""
    
    def VideoCapture(self, source):
        return MockVideoCapture(source)
    
    def waitKey(self, delay):
        time.sleep(delay / 1000.0)
        return -1
    
    def destroyAllWindows(self):
        pass

class MockVideoCapture:
    """模拟视频捕获"""
    
    def __init__(self, source):
        self.source = source
        self.frame_count = 300  # 模拟300帧视频
        self.current_frame = 0
        self.fps = 30
        
    def isOpened(self):
        return True
    
    def read(self):
        if self.current_frame >= self.frame_count:
            return False, None
        
        # 模拟帧数据
        self.current_frame += 1
        mock_frame = f"frame_{self.current_frame}_from_{self.source}"
        return True, mock_frame
    
    def get(self, prop):
        if prop == 7:  # CV_CAP_PROP_FRAME_COUNT
            return self.frame_count
        elif prop == 5:  # CV_CAP_PROP_FPS
            return self.fps
        return 0
    
    def release(self):
        pass

# 使用模拟的OpenCV
cv2 = MockCV2()

logger = logging.getLogger(__name__)

class VideoProcessor:
    """视频处理器 - 支持真实视频文件的跌倒和火焰检测"""
    
    def __init__(self, unified_detector=None):
        """
        初始化视频处理器
        
        Args:
            unified_detector: 统一检测器实例
        """
        # 如果没有提供检测器，使用模拟检测器
        if unified_detector is None:
            from unified_detector import UnifiedDetector
            try:
                self.detector = UnifiedDetector()
            except:
                self.detector = MockUnifiedDetector()
        else:
            self.detector = unified_detector
        
        # 视频处理参数
        self.frame_skip = 2  # 每2帧处理一次
        self.max_fps = 15    # 最大处理帧率
        
        # 结果存储
        self.detection_results = []
        self.alert_history = []
        self.processing_stats = {
            'total_frames': 0,
            'processed_frames': 0,
            'total_detections': 0,
            'alerts_generated': 0,
            'processing_time': 0.0
        }
        
        # 实时处理控制
        self.is_processing = False
        self.stop_processing = False
        self.result_queue = queue.Queue()
        
    def process_video_file(self, video_path: str, camera_id: str = "video_test", 
                          enable_fall: bool = True, enable_fire: bool = True,
                          save_results: bool = True) -> Dict:
        """
        处理视频文件
        
        Args:
            video_path: 视频文件路径
            camera_id: 摄像头ID
            enable_fall: 是否启用跌倒检测
            enable_fire: 是否启用火焰检测
            save_results: 是否保存检测结果
            
        Returns:
            处理结果统计
        """
        if not os.path.exists(video_path):
            logger.error(f"视频文件不存在: {video_path}")
            return {'error': f'视频文件不存在: {video_path}'}
        
        logger.info(f"开始处理视频: {video_path}")
        start_time = time.time()
        
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return {'error': f'无法打开视频文件: {video_path}'}
        
        # 获取视频信息
        total_frames = int(cap.get(7))  # CV_CAP_PROP_FRAME_COUNT
        fps = cap.get(5)  # CV_CAP_PROP_FPS
        
        logger.info(f"视频信息: 总帧数={total_frames}, FPS={fps}")
        
        frame_count = 0
        processed_count = 0
        current_alerts = []
        
        try:
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                frame_count += 1
                self.processing_stats['total_frames'] = frame_count
                
                # 跳帧处理
                if frame_count % self.frame_skip != 0:
                    continue
                
                processed_count += 1
                self.processing_stats['processed_frames'] = processed_count
                
                # 执行检测
                detection_result = self.detector.process_frame(
                    frame, camera_id, enable_fall, enable_fire
                )
                
                # 添加帧信息
                detection_result['frame_number'] = frame_count
                detection_result['video_timestamp'] = frame_count / fps
                
                # 记录检测结果
                self.detection_results.append(detection_result)
                self.processing_stats['total_detections'] += len(detection_result.get('detections', []))
                
                # 处理告警
                alerts = detection_result.get('alerts', [])
                if alerts:
                    current_alerts.extend(alerts)
                    self.alert_history.extend(alerts)
                    self.processing_stats['alerts_generated'] += len(alerts)
                    
                    # 输出实时告警信息
                    for alert in alerts:
                        logger.warning(f"🚨 {alert['severity']} 告警: {alert['message']} (帧:{frame_count})")
                
                # 控制处理速度
                if processed_count % 10 == 0:
                    logger.info(f"处理进度: {frame_count}/{total_frames} ({frame_count/total_frames*100:.1f}%)")
                
                # 限制处理速度
                time.sleep(1.0 / self.max_fps)
        
        except KeyboardInterrupt:
            logger.info("用户中断处理")
        except Exception as e:
            logger.error(f"处理过程中出错: {e}")
        finally:
            cap.release()
        
        # 计算处理统计
        end_time = time.time()
        processing_time = end_time - start_time
        self.processing_stats['processing_time'] = processing_time
        
        # 生成结果报告
        result_summary = {
            'video_path': video_path,
            'camera_id': camera_id,
            'processing_time': processing_time,
            'video_info': {
                'total_frames': total_frames,
                'fps': fps,
                'duration': total_frames / fps if fps > 0 else 0
            },
            'processing_stats': self.processing_stats.copy(),
            'detection_summary': self._generate_detection_summary(),
            'alerts': current_alerts,
            'timestamp': datetime.now().isoformat()
        }
        
        # 保存结果
        if save_results:
            self._save_results(video_path, result_summary)
        
        logger.info(f"视频处理完成: {processing_time:.2f}秒")
        return result_summary
    
    def process_video_realtime(self, video_path: str, camera_id: str = "live_test",
                              callback: Optional[Callable] = None) -> bool:
        """
        实时视频处理 (模拟摄像头)
        
        Args:
            video_path: 视频文件路径
            camera_id: 摄像头ID
            callback: 结果回调函数
            
        Returns:
            是否成功启动
        """
        if self.is_processing:
            logger.warning("已有视频在处理中")
            return False
        
        def process_thread():
            self.is_processing = True
            self.stop_processing = False
            
            cap = cv2.VideoCapture(video_path)
            if not cap.isOpened():
                logger.error(f"无法打开视频: {video_path}")
                self.is_processing = False
                return
            
            frame_count = 0
            
            try:
                while not self.stop_processing:
                    ret, frame = cap.read()
                    if not ret:
                        # 视频结束，循环播放
                        cap.set(1, 0)  # 重置到第一帧
                        continue
                    
                    frame_count += 1
                    
                    if frame_count % self.frame_skip == 0:
                        # 执行检测
                        result = self.detector.process_frame(frame, camera_id)
                        result['frame_number'] = frame_count
                        
                        # 放入结果队列
                        try:
                            self.result_queue.put_nowait(result)
                        except queue.Full:
                            # 队列满了，丢弃最旧的结果
                            try:
                                self.result_queue.get_nowait()
                                self.result_queue.put_nowait(result)
                            except queue.Empty:
                                pass
                        
                        # 调用回调函数
                        if callback:
                            callback(result)
                    
                    # 控制帧率
                    time.sleep(1.0 / self.max_fps)
            
            except Exception as e:
                logger.error(f"实时处理出错: {e}")
            finally:
                cap.release()
                self.is_processing = False
        
        # 启动处理线程
        thread = threading.Thread(target=process_thread)
        thread.daemon = True
        thread.start()
        
        return True
    
    def stop_realtime_processing(self):
        """停止实时处理"""
        self.stop_processing = True
        self.is_processing = False
    
    def get_latest_result(self) -> Optional[Dict]:
        """获取最新的检测结果"""
        try:
            return self.result_queue.get_nowait()
        except queue.Empty:
            return None
    
    def _generate_detection_summary(self) -> Dict:
        """生成检测汇总"""
        if not self.detection_results:
            return {}
        
        summary = {
            'total_detections': 0,
            'fall_detections': 0,
            'fire_detections': 0,
            'smoke_detections': 0,
            'avg_confidence': 0.0,
            'detection_timeline': []
        }
        
        total_confidence = 0
        confidence_count = 0
        
        for result in self.detection_results:
            detections = result.get('detections', [])
            summary['total_detections'] += len(detections)
            
            for detection in detections:
                detection_type = detection.get('type', '')
                confidence = detection.get('confidence', 0)
                
                if detection_type == 'fall':
                    summary['fall_detections'] += 1
                elif detection_type == 'fire':
                    summary['fire_detections'] += 1
                elif detection_type == 'smoke':
                    summary['smoke_detections'] += 1
                
                total_confidence += confidence
                confidence_count += 1
                
                # 记录时间线
                summary['detection_timeline'].append({
                    'frame': result.get('frame_number', 0),
                    'timestamp': result.get('video_timestamp', 0),
                    'type': detection_type,
                    'confidence': confidence
                })
        
        if confidence_count > 0:
            summary['avg_confidence'] = total_confidence / confidence_count
        
        return summary
    
    def _save_results(self, video_path: str, results: Dict):
        """保存检测结果"""
        video_name = os.path.basename(video_path).split('.')[0]
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        
        # 保存详细结果
        results_file = f"video_test_results_{video_name}_{timestamp}.json"
        with open(results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        # 保存简化报告
        report_file = f"video_test_report_{video_name}_{timestamp}.txt"
        with open(report_file, 'w', encoding='utf-8') as f:
            f.write(f"视频检测报告\n")
            f.write(f"=" * 50 + "\n")
            f.write(f"视频文件: {video_path}\n")
            f.write(f"处理时间: {results['processing_time']:.2f}秒\n")
            f.write(f"总帧数: {results['video_info']['total_frames']}\n")
            f.write(f"处理帧数: {results['processing_stats']['processed_frames']}\n")
            f.write(f"检测总数: {results['processing_stats']['total_detections']}\n")
            f.write(f"告警总数: {results['processing_stats']['alerts_generated']}\n\n")
            
            summary = results.get('detection_summary', {})
            f.write(f"检测汇总:\n")
            f.write(f"- 跌倒检测: {summary.get('fall_detections', 0)}\n")
            f.write(f"- 火焰检测: {summary.get('fire_detections', 0)}\n")
            f.write(f"- 烟雾检测: {summary.get('smoke_detections', 0)}\n")
            f.write(f"- 平均置信度: {summary.get('avg_confidence', 0):.3f}\n\n")
            
            if results.get('alerts'):
                f.write(f"告警列表:\n")
                for i, alert in enumerate(results['alerts'], 1):
                    f.write(f"{i}. {alert['severity']}: {alert['message']}\n")
        
        logger.info(f"结果已保存: {results_file}, {report_file}")

class MockUnifiedDetector:
    """模拟统一检测器 (当真实检测器不可用时)"""
    
    def process_frame(self, frame, camera_id, enable_fall=True, enable_fire=True):
        import random
        
        detections = []
        alerts = []
        
        # 模拟检测逻辑
        if enable_fall and random.random() < 0.1:  # 10%概率检测到跌倒
            detection = {
                'type': 'fall',
                'confidence': round(random.uniform(0.7, 0.95), 2),
                'person_id': f'person_{random.randint(1, 3)}',
                'timestamp': datetime.now().isoformat()
            }
            detections.append(detection)
            
            if detection['confidence'] > 0.8:
                alerts.append({
                    'id': f"fall_{int(time.time() * 1000)}",
                    'type': 'fall',
                    'severity': 'HIGH',
                    'message': f"检测到跌倒，置信度: {detection['confidence']:.2f}",
                    'timestamp': detection['timestamp']
                })
        
        if enable_fire and random.random() < 0.05:  # 5%概率检测到火焰
            detection = {
                'type': 'fire',
                'confidence': round(random.uniform(0.6, 0.9), 2),
                'bbox': [100, 100, 200, 200],
                'timestamp': datetime.now().isoformat()
            }
            detections.append(detection)
            
            if detection['confidence'] > 0.7:
                alerts.append({
                    'id': f"fire_{int(time.time() * 1000)}",
                    'type': 'fire',
                    'severity': 'CRITICAL',
                    'message': f"检测到火焰，置信度: {detection['confidence']:.2f}",
                    'timestamp': detection['timestamp']
                })
        
        return {
            'camera_id': camera_id,
            'timestamp': datetime.now().isoformat(),
            'detections': detections,
            'alerts': alerts,
            'processing_time': round(random.uniform(0.1, 0.3), 3)
        }

def create_test_video_info():
    """创建测试视频信息"""
    return {
        'fall_videos': [
            {
                'name': 'elderly_fall_001.mp4',
                'description': '老人在卧室跌倒',
                'expected_detections': ['fall'],
                'duration': '30秒',
                'resolution': '1280x720'
            },
            {
                'name': 'elderly_fall_002.mp4', 
                'description': '老人在客厅跌倒',
                'expected_detections': ['fall'],
                'duration': '45秒',
                'resolution': '1920x1080'
            }
        ],
        'fire_videos': [
            {
                'name': 'house_fire_001.mp4',
                'description': '室内火灾场景',
                'expected_detections': ['fire', 'smoke'],
                'duration': '60秒',
                'resolution': '1280x720'
            },
            {
                'name': 'smoke_detection_001.mp4',
                'description': '烟雾检测场景',
                'expected_detections': ['smoke'],
                'duration': '40秒',
                'resolution': '1920x1080'
            }
        ]
    }

if __name__ == "__main__":
    # 测试视频处理器
    processor = VideoProcessor()
    
    # 显示测试视频信息
    test_videos = create_test_video_info()
    print("📹 支持的测试视频类型:")
    print("\n跌倒检测视频:")
    for video in test_videos['fall_videos']:
        print(f"  - {video['name']}: {video['description']}")
    
    print("\n火焰/烟雾检测视频:")
    for video in test_videos['fire_videos']:
        print(f"  - {video['name']}: {video['description']}")
    
    print("\n使用方法:")
    print("processor.process_video_file('path/to/video.mp4', 'camera_01')")
    print("processor.process_video_realtime('path/to/video.mp4', 'live_01')")