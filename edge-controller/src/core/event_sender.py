#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
事件发送器 - 负责将检测事件发送到管理平台
"""

import asyncio
import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import aiohttp
from dataclasses import dataclass, asdict

logger = logging.getLogger(__name__)

@dataclass
class DetectionEvent:
    """检测事件数据结构"""
    id: str
    event_type: str  # fall, fire, smoke
    event_subtype: str
    camera_id: str
    camera_name: str
    location: str
    timestamp: str
    confidence: float
    severity: str  # LOW, MEDIUM, HIGH, CRITICAL
    bbox: Optional[List[int]] = None
    algorithm: str = ""
    additional_data: Optional[Dict[str, Any]] = None

@dataclass
class HeartbeatData:
    """心跳数据结构"""
    controller_id: str
    controller_name: str
    timestamp: str
    status: str
    camera_count: int
    active_cameras: int
    system_stats: Dict[str, Any]

class EventSender:
    """事件发送器"""
    
    def __init__(self, management_config: Dict[str, Any], local_cache):
        self.config = management_config
        self.local_cache = local_cache
        self.api_url = management_config["api_url"]
        self.heartbeat_interval = management_config.get("heartbeat_interval", 10)
        self.retry_attempts = management_config.get("retry_attempts", 3)
        
        self.session: Optional[aiohttp.ClientSession] = None
        self.heartbeat_task: Optional[asyncio.Task] = None
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.send_task: Optional[asyncio.Task] = None
        
        self._is_running = False
        self._controller_stats = {}
        
    async def initialize(self):
        """初始化事件发送器"""
        try:
            # 创建HTTP会话
            timeout = aiohttp.ClientTimeout(total=30)
            self.session = aiohttp.ClientSession(timeout=timeout)
            
            # 启动心跳任务
            self.heartbeat_task = asyncio.create_task(self._heartbeat_loop())
            
            # 启动事件发送任务
            self.send_task = asyncio.create_task(self._event_send_loop())
            
            self._is_running = True
            logger.info("事件发送器初始化完成")
            
        except Exception as e:
            logger.error(f"事件发送器初始化失败: {e}")
            raise
    
    async def shutdown(self):
        """关闭事件发送器"""
        try:
            self._is_running = False
            
            # 取消任务
            if self.heartbeat_task:
                self.heartbeat_task.cancel()
            if self.send_task:
                self.send_task.cancel()
            
            # 等待任务完成
            await asyncio.gather(
                self.heartbeat_task, self.send_task,
                return_exceptions=True
            )
            
            # 关闭HTTP会话
            if self.session:
                await self.session.close()
            
            logger.info("事件发送器已关闭")
            
        except Exception as e:
            logger.error(f"事件发送器关闭失败: {e}")
    
    async def send_detection_event(self, event: DetectionEvent):
        """发送检测事件"""
        try:
            # 添加到队列
            await self.event_queue.put(event)
            logger.debug(f"检测事件已加入队列: {event.id}")
            
        except Exception as e:
            logger.error(f"发送检测事件失败: {e}")
            # 保存到本地缓存
            await self.local_cache.save_event(asdict(event))
    
    async def update_controller_stats(self, stats: Dict[str, Any]):
        """更新控制器统计信息"""
        self._controller_stats = stats
    
    async def _heartbeat_loop(self):
        """心跳循环"""
        while self._is_running:
            try:
                await self._send_heartbeat()
                await asyncio.sleep(self.heartbeat_interval)
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"心跳发送失败: {e}")
                await asyncio.sleep(5)
    
    async def _send_heartbeat(self):
        """发送心跳"""
        try:
            heartbeat = HeartbeatData(
                controller_id="edge_controller_1",
                controller_name="边缘控制器#1", 
                timestamp=datetime.now().isoformat(),
                status="running",
                camera_count=self._controller_stats.get("total_cameras", 0),
                active_cameras=self._controller_stats.get("active_cameras", 0),
                system_stats=self._controller_stats
            )
            
            url = f"{self.api_url}/edge/heartbeat"
            data = asdict(heartbeat)
            
            async with self.session.post(url, json=data) as response:
                if response.status == 200:
                    logger.debug("心跳发送成功")
                else:
                    logger.warning(f"心跳发送失败: {response.status}")
                    
        except Exception as e:
            logger.error(f"心跳发送异常: {e}")
    
    async def _event_send_loop(self):
        """事件发送循环"""
        while self._is_running:
            try:
                # 批量处理事件
                events = []
                try:
                    # 收集批量事件
                    for _ in range(10):  # 最多10个事件一批
                        event = await asyncio.wait_for(
                            self.event_queue.get(), timeout=1.0
                        )
                        events.append(event)
                except asyncio.TimeoutError:
                    pass
                
                if events:
                    await self._send_events_batch(events)
                    
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"事件发送循环异常: {e}")
                await asyncio.sleep(1)
    
    async def _send_events_batch(self, events: List[DetectionEvent]):
        """批量发送事件"""
        try:
            url = f"{self.api_url}/edge/events"
            data = {
                "controller_id": "edge_controller_1",
                "timestamp": datetime.now().isoformat(),
                "events": [asdict(event) for event in events]
            }
            
            success = False
            for attempt in range(self.retry_attempts):
                try:
                    async with self.session.post(url, json=data) as response:
                        if response.status == 200:
                            logger.info(f"成功发送 {len(events)} 个事件")
                            success = True
                            break
                        else:
                            logger.warning(f"事件发送失败: {response.status}")
                            
                except Exception as e:
                    logger.error(f"事件发送尝试 {attempt + 1} 失败: {e}")
                    if attempt < self.retry_attempts - 1:
                        await asyncio.sleep(2 ** attempt)  # 指数退避
            
            if not success:
                # 保存到本地缓存
                for event in events:
                    await self.local_cache.save_event(asdict(event))
                logger.warning(f"{len(events)} 个事件已保存到本地缓存")
                
        except Exception as e:
            logger.error(f"批量发送事件异常: {e}")
            # 保存到本地缓存
            for event in events:
                await self.local_cache.save_event(asdict(event))
    
    async def get_connection_status(self) -> Dict[str, Any]:
        """获取连接状态"""
        try:
            url = f"{self.api_url}/health"
            async with self.session.get(url) as response:
                if response.status == 200:
                    return {
                        "status": "connected",
                        "management_platform": "online",
                        "last_check": datetime.now().isoformat()
                    }
                else:
                    return {
                        "status": "disconnected", 
                        "management_platform": "offline",
                        "last_check": datetime.now().isoformat(),
                        "error": f"HTTP {response.status}"
                    }
        except Exception as e:
            return {
                "status": "disconnected",
                "management_platform": "offline", 
                "last_check": datetime.now().isoformat(),
                "error": str(e)
            }