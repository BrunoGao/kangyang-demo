#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
RTSP流处理器 - 边缘控制器版本
专门处理RTSP视频流的连接、重连和错误恢复
"""

import cv2
import logging
import asyncio
import threading
import time
from typing import Dict, Any, Optional, Callable
from datetime import datetime
import numpy as np

logger = logging.getLogger(__name__)

class RTSPStream:
    """单个RTSP流处理器"""
    
    def __init__(self, stream_id: str, rtsp_url: str, config: Dict[str, Any] = None):
        self.stream_id = stream_id
        self.rtsp_url = rtsp_url
        self.config = config or {}
        
        # 连接参数
        self.timeout = self.config.get("rtsp_timeout", 10)
        self.reconnect_interval = self.config.get("reconnect_interval", 5)
        self.max_reconnect_attempts = self.config.get("max_reconnect_attempts", 3)
        
        # 状态
        self.is_connected = False
        self.is_running = False
        self.last_frame_time = None
        self.connection_attempts = 0
        self.total_frames = 0
        self.dropped_frames = 0
        
        # OpenCV VideoCapture
        self.cap: Optional[cv2.VideoCapture] = None
        
        # 回调函数
        self.frame_callback: Optional[Callable] = None
        self.error_callback: Optional[Callable] = None
        
    def set_frame_callback(self, callback: Callable):
        """设置帧处理回调函数"""
        self.frame_callback = callback
    
    def set_error_callback(self, callback: Callable):
        """设置错误处理回调函数"""
        self.error_callback = callback
    
    def connect(self) -> bool:
        """连接RTSP流"""
        try:
            if self.cap:
                self.cap.release()
            
            # 创建VideoCapture
            self.cap = cv2.VideoCapture(self.rtsp_url)
            
            # 设置参数
            self.cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)  # 减少缓冲延迟
            self.cap.set(cv2.CAP_PROP_TIMEOUT, self.timeout * 1000)
            
            # 测试连接
            if self.cap.isOpened():
                ret, frame = self.cap.read()
                if ret and frame is not None:
                    self.is_connected = True
                    self.connection_attempts = 0
                    logger.info(f"RTSP流连接成功: {self.stream_id}")
                    return True
            
            self.is_connected = False
            logger.warning(f"RTSP流连接失败: {self.stream_id}")
            return False
            
        except Exception as e:
            self.is_connected = False
            logger.error(f"RTSP流连接异常: {self.stream_id} - {e}")
            return False
    
    def disconnect(self):
        """断开连接"""
        try:
            self.is_running = False
            self.is_connected = False
            
            if self.cap:
                self.cap.release()
                self.cap = None
            
            logger.info(f"RTSP流已断开: {self.stream_id}")
            
        except Exception as e:
            logger.error(f"断开RTSP流异常: {self.stream_id} - {e}")
    
    def read_frame(self) -> Optional[np.ndarray]:
        """读取一帧"""
        try:
            if not self.is_connected or not self.cap:
                return None
            
            ret, frame = self.cap.read()
            if ret and frame is not None:
                self.total_frames += 1
                self.last_frame_time = datetime.now()
                return frame
            else:
                self.dropped_frames += 1
                return None
                
        except Exception as e:
            logger.error(f"读取帧异常: {self.stream_id} - {e}")
            self.dropped_frames += 1
            return None
    
    def start_streaming(self):
        """开始流处理"""
        self.is_running = True
        
        while self.is_running:
            try:
                # 检查连接状态
                if not self.is_connected:
                    if not self._try_reconnect():
                        time.sleep(self.reconnect_interval)
                        continue
                
                # 读取帧
                frame = self.read_frame()
                if frame is not None:
                    # 调用帧处理回调
                    if self.frame_callback:
                        try:
                            self.frame_callback(self.stream_id, frame)
                        except Exception as e:
                            logger.error(f"帧处理回调异常: {self.stream_id} - {e}")
                else:
                    # 读取失败，可能需要重连
                    if self.is_connected:
                        logger.warning(f"帧读取失败，尝试重连: {self.stream_id}")
                        self.is_connected = False
                
                # 简单的帧率控制
                time.sleep(0.01)
                
            except Exception as e:
                logger.error(f"流处理异常: {self.stream_id} - {e}")
                if self.error_callback:
                    self.error_callback(self.stream_id, str(e))
                time.sleep(1)
    
    def _try_reconnect(self) -> bool:
        """尝试重连"""
        if self.connection_attempts >= self.max_reconnect_attempts:
            logger.error(f"达到最大重连次数: {self.stream_id}")
            return False
        
        self.connection_attempts += 1
        logger.info(f"尝试重连 RTSP流 ({self.connection_attempts}/{self.max_reconnect_attempts}): {self.stream_id}")
        
        return self.connect()
    
    def get_stats(self) -> Dict[str, Any]:
        """获取流统计信息"""
        return {
            "stream_id": self.stream_id,
            "is_connected": self.is_connected,
            "is_running": self.is_running,
            "total_frames": self.total_frames,
            "dropped_frames": self.dropped_frames,
            "connection_attempts": self.connection_attempts,
            "last_frame_time": self.last_frame_time.isoformat() if self.last_frame_time else None,
            "drop_rate": self.dropped_frames / max(self.total_frames + self.dropped_frames, 1)
        }

class RTSPHandler:
    """RTSP流管理器"""
    
    def __init__(self, config: Dict[str, Any] = None):
        self.config = config or {}
        self.streams: Dict[str, RTSPStream] = {}
        self.stream_threads: Dict[str, threading.Thread] = {}
        self.is_initialized = False
        
    async def initialize(self):
        """初始化RTSP处理器"""
        try:
            self.is_initialized = True
            logger.info("RTSP处理器初始化完成")
        except Exception as e:
            logger.error(f"RTSP处理器初始化失败: {e}")
            raise
    
    async def shutdown(self):
        """关闭RTSP处理器"""
        try:
            logger.info("正在关闭RTSP处理器...")
            
            # 停止所有流
            for stream_id in list(self.streams.keys()):
                await self.stop_stream(stream_id)
            
            self.is_initialized = False
            logger.info("RTSP处理器已关闭")
            
        except Exception as e:
            logger.error(f"关闭RTSP处理器失败: {e}")
    
    async def add_stream(self, stream_id: str, rtsp_url: str, 
                        frame_callback: Callable = None, 
                        error_callback: Callable = None) -> bool:
        """添加RTSP流"""
        try:
            if stream_id in self.streams:
                logger.warning(f"RTSP流已存在: {stream_id}")
                return False
            
            # 创建流对象
            stream = RTSPStream(stream_id, rtsp_url, self.config)
            
            # 设置回调
            if frame_callback:
                stream.set_frame_callback(frame_callback)
            if error_callback:
                stream.set_error_callback(error_callback)
            
            # 测试连接
            if stream.connect():
                self.streams[stream_id] = stream
                logger.info(f"RTSP流添加成功: {stream_id}")
                return True
            else:
                logger.error(f"RTSP流连接测试失败: {stream_id}")
                return False
                
        except Exception as e:
            logger.error(f"添加RTSP流失败: {stream_id} - {e}")
            return False
    
    async def remove_stream(self, stream_id: str) -> bool:
        """移除RTSP流"""
        try:
            if stream_id not in self.streams:
                return False
            
            # 停止流
            await self.stop_stream(stream_id)
            
            # 移除流对象
            del self.streams[stream_id]
            
            logger.info(f"RTSP流移除成功: {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"移除RTSP流失败: {stream_id} - {e}")
            return False
    
    async def start_stream(self, stream_id: str) -> bool:
        """开始流处理"""
        try:
            if stream_id not in self.streams:
                logger.error(f"RTSP流不存在: {stream_id}")
                return False
            
            if stream_id in self.stream_threads:
                logger.warning(f"RTSP流已在运行: {stream_id}")
                return True
            
            stream = self.streams[stream_id]
            
            # 创建处理线程
            thread = threading.Thread(
                target=stream.start_streaming,
                daemon=True
            )
            thread.start()
            
            self.stream_threads[stream_id] = thread
            
            logger.info(f"RTSP流开始处理: {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"开始RTSP流失败: {stream_id} - {e}")
            return False
    
    async def stop_stream(self, stream_id: str) -> bool:
        """停止流处理"""
        try:
            if stream_id in self.streams:
                self.streams[stream_id].disconnect()
            
            if stream_id in self.stream_threads:
                thread = self.stream_threads[stream_id]
                if thread.is_alive():
                    thread.join(timeout=5.0)
                del self.stream_threads[stream_id]
            
            logger.info(f"RTSP流停止成功: {stream_id}")
            return True
            
        except Exception as e:
            logger.error(f"停止RTSP流失败: {stream_id} - {e}")
            return False
    
    async def get_stream_stats(self, stream_id: str) -> Optional[Dict[str, Any]]:
        """获取流统计信息"""
        if stream_id in self.streams:
            return self.streams[stream_id].get_stats()
        return None
    
    async def get_all_stats(self) -> Dict[str, Any]:
        """获取所有流的统计信息"""
        stats = {
            "total_streams": len(self.streams),
            "active_streams": len(self.stream_threads),
            "streams": {}
        }
        
        for stream_id, stream in self.streams.items():
            stats["streams"][stream_id] = stream.get_stats()
        
        return stats