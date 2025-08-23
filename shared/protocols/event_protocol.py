#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边缘控制器与管理平台通信协议定义
定义数据格式、API接口和消息结构
"""

from dataclasses import dataclass, asdict
from typing import Dict, Any, List, Optional, Union
from datetime import datetime
from enum import Enum

class EventType(Enum):
    """事件类型枚举"""
    FALL_DETECTION = "fall"
    FIRE_DETECTION = "fire"
    SMOKE_DETECTION = "smoke"
    SYSTEM_ALERT = "system"

class SeverityLevel(Enum):
    """严重等级枚举"""
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"
    CRITICAL = "CRITICAL"

class ControllerStatus(Enum):
    """控制器状态枚举"""
    RUNNING = "running"
    STOPPED = "stopped"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class CameraStatus(Enum):
    """摄像头状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"

@dataclass
class DetectionEvent:
    """检测事件数据结构"""
    id: str
    event_type: str  # EventType value
    event_subtype: str
    camera_id: str
    camera_name: str
    location: str
    timestamp: str  # ISO format
    confidence: float
    severity: str  # SeverityLevel value
    bbox: Optional[List[int]] = None
    algorithm: str = ""
    additional_data: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DetectionEvent':
        """从字典创建对象"""
        return cls(**data)

@dataclass
class SystemStats:
    """系统统计信息"""
    controller_id: str
    controller_name: str
    total_cameras: int
    active_cameras: int
    online_cameras: int
    total_detections: int
    total_frames_processed: int
    uptime_seconds: float
    average_fps: float
    cpu_usage: Optional[float] = None
    memory_usage: Optional[float] = None
    gpu_usage: Optional[float] = None
    disk_usage: Optional[float] = None
    temperature: Optional[float] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class HeartbeatData:
    """心跳数据结构"""
    controller_id: str
    controller_name: str
    timestamp: str  # ISO format
    status: str  # ControllerStatus value
    camera_count: int
    active_cameras: int
    system_stats: SystemStats
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class CameraInfo:
    """摄像头信息"""
    id: str
    name: str
    rtsp_url: str
    location: str
    zone_id: str = ""
    status: str = CameraStatus.OFFLINE.value
    enabled_algorithms: List[str] = None
    fps: float = 0.0
    last_frame_time: Optional[str] = None
    total_detections: int = 0
    
    def __post_init__(self):
        if self.enabled_algorithms is None:
            self.enabled_algorithms = ["fall_detection"]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class EventBatch:
    """事件批量上报"""
    controller_id: str
    timestamp: str  # ISO format
    events: List[DetectionEvent]
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "controller_id": self.controller_id,
            "timestamp": self.timestamp,
            "events": [event.to_dict() for event in self.events]
        }

@dataclass
class ConfigUpdate:
    """配置更新"""
    target: str  # "controller" | "camera" | "algorithm"
    target_id: str
    config: Dict[str, Any]
    timestamp: str
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class CommandRequest:
    """命令请求"""
    command: str  # "start_camera" | "stop_camera" | "restart" | "update_config"
    target: str   # controller_id or camera_id
    parameters: Dict[str, Any] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
        if self.parameters is None:
            self.parameters = {}
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

@dataclass
class CommandResponse:
    """命令响应"""
    command: str
    target: str
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

# API 端点定义
class APIEndpoints:
    """API端点常量"""
    
    # 管理平台接收的端点
    EDGE_HEARTBEAT = "/api/edge/heartbeat"
    EDGE_EVENTS = "/api/edge/events"
    EDGE_CONTROLLERS = "/api/edge/controllers"
    EDGE_STATISTICS = "/api/edge/statistics"
    
    # 边缘控制器接收的端点
    EDGE_CONFIG = "/api/config"
    EDGE_CAMERAS = "/api/cameras"
    EDGE_DETECTION = "/api/detection"
    EDGE_HEALTH = "/api/health"
    
    # 摄像头操作
    CAMERA_ADD = "/api/cameras"
    CAMERA_REMOVE = "/api/cameras/{camera_id}"
    CAMERA_START = "/api/cameras/{camera_id}/start"
    CAMERA_STOP = "/api/cameras/{camera_id}/stop"
    CAMERA_STATS = "/api/cameras/{camera_id}/stats"

# HTTP状态码定义
class StatusCodes:
    """HTTP状态码常量"""
    SUCCESS = 200
    CREATED = 201
    BAD_REQUEST = 400
    UNAUTHORIZED = 401
    NOT_FOUND = 404
    INTERNAL_ERROR = 500
    SERVICE_UNAVAILABLE = 503

# 消息类型定义
class MessageTypes:
    """消息类型常量"""
    HEARTBEAT = "heartbeat"
    EVENT_BATCH = "event_batch"
    CONFIG_UPDATE = "config_update"
    COMMAND_REQUEST = "command_request"
    COMMAND_RESPONSE = "command_response"
    ALERT = "alert"

# 协议版本
PROTOCOL_VERSION = "1.0.0"

def create_standard_response(success: bool, message: str, data: Any = None) -> Dict[str, Any]:
    """创建标准响应格式"""
    response = {
        "success": success,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "protocol_version": PROTOCOL_VERSION
    }
    if data is not None:
        response["data"] = data
    return response

def create_error_response(error_code: str, error_message: str, details: Any = None) -> Dict[str, Any]:
    """创建错误响应格式"""
    response = {
        "success": False,
        "error": {
            "code": error_code,
            "message": error_message
        },
        "timestamp": datetime.now().isoformat(),
        "protocol_version": PROTOCOL_VERSION
    }
    if details is not None:
        response["error"]["details"] = details
    return response

def validate_event_data(event_data: Dict[str, Any]) -> bool:
    """验证事件数据格式"""
    required_fields = [
        "id", "event_type", "camera_id", "camera_name", 
        "location", "timestamp", "confidence"
    ]
    
    for field in required_fields:
        if field not in event_data:
            return False
    
    # 验证数据类型
    if not isinstance(event_data["confidence"], (int, float)):
        return False
    
    if event_data["confidence"] < 0 or event_data["confidence"] > 1:
        return False
    
    # 验证事件类型
    valid_event_types = [e.value for e in EventType]
    if event_data["event_type"] not in valid_event_types:
        return False
    
    return True

def validate_heartbeat_data(heartbeat_data: Dict[str, Any]) -> bool:
    """验证心跳数据格式"""
    required_fields = [
        "controller_id", "controller_name", "timestamp", 
        "status", "camera_count", "system_stats"
    ]
    
    for field in required_fields:
        if field not in heartbeat_data:
            return False
    
    # 验证状态
    valid_statuses = [s.value for s in ControllerStatus]
    if heartbeat_data["status"] not in valid_statuses:
        return False
    
    return True