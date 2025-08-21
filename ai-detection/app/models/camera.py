#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头管理数据模型
支持22路摄像头接入管理
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class CameraStatus(str, Enum):
    """摄像头状态枚举"""
    ONLINE = "online"
    OFFLINE = "offline"
    ERROR = "error"
    MAINTENANCE = "maintenance"

class CameraType(str, Enum):
    """摄像头类型枚举"""
    INDOOR = "indoor"      # 室内摄像头
    OUTDOOR = "outdoor"    # 室外摄像头
    CORRIDOR = "corridor"  # 走廊摄像头
    ENTRANCE = "entrance"  # 出入口摄像头

class AlgorithmType(str, Enum):
    """算法类型枚举"""
    FALL_DETECTION = "fall_detection"      # 跌倒检测
    FIRE_DETECTION = "fire_detection"      # 火焰检测
    SMOKE_DETECTION = "smoke_detection"    # 烟雾检测
    CROWD_DETECTION = "crowd_detection"    # 拥挤检测
    WANDERING_DETECTION = "wandering_detection"  # 徘徊检测

class Camera(BaseModel):
    """摄像头基础信息模型"""
    id: str = Field(..., description="摄像头唯一ID")
    name: str = Field(..., description="摄像头名称")
    ip_address: str = Field(..., description="IP地址")
    rtsp_url: str = Field(..., description="RTSP视频流地址")
    location: str = Field(..., description="安装位置")
    camera_type: CameraType = Field(..., description="摄像头类型")
    brand: Optional[str] = Field(None, description="摄像头品牌")
    model: Optional[str] = Field(None, description="摄像头型号")
    resolution: str = Field(default="1920x1080", description="分辨率")
    fps: int = Field(default=25, description="帧率")
    status: CameraStatus = Field(default=CameraStatus.OFFLINE, description="当前状态")
    enabled_algorithms: List[AlgorithmType] = Field(default=[], description="启用的算法")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class CameraConfig(BaseModel):
    """摄像头配置模型"""
    camera_id: str = Field(..., description="摄像头ID")
    algorithm_configs: Dict[AlgorithmType, Dict[str, Any]] = Field(..., description="算法配置")
    detection_zones: Optional[List[Dict[str, Any]]] = Field(None, description="检测区域")
    sensitivity: float = Field(default=0.8, description="检测灵敏度")
    alert_threshold: float = Field(default=0.85, description="告警阈值")
    
class CameraStream(BaseModel):
    """摄像头视频流信息"""
    camera_id: str = Field(..., description="摄像头ID")
    stream_url: str = Field(..., description="视频流地址")
    stream_status: str = Field(..., description="流状态")
    bitrate: Optional[int] = Field(None, description="码率")
    frame_count: int = Field(default=0, description="处理帧数")
    last_frame_time: Optional[datetime] = Field(None, description="最后一帧时间")
    
class CameraStats(BaseModel):
    """摄像头统计信息"""
    camera_id: str = Field(..., description="摄像头ID")
    total_detections: int = Field(default=0, description="总检测数")
    fall_detections: int = Field(default=0, description="跌倒检测数")
    fire_detections: int = Field(default=0, description="火焰检测数")
    smoke_detections: int = Field(default=0, description="烟雾检测数")
    uptime_hours: float = Field(default=0.0, description="在线时长(小时)")
    avg_processing_time: float = Field(default=0.0, description="平均处理时间(毫秒)")
    last_detection_time: Optional[datetime] = Field(None, description="最后检测时间")

class CameraGroup(BaseModel):
    """摄像头分组模型"""
    id: str = Field(..., description="分组ID")
    name: str = Field(..., description="分组名称")
    description: Optional[str] = Field(None, description="分组描述")
    camera_ids: List[str] = Field(default=[], description="摄像头ID列表")
    enabled_algorithms: List[AlgorithmType] = Field(default=[], description="分组算法配置")
    alert_contacts: List[str] = Field(default=[], description="告警联系人")

class BatchCameraOperation(BaseModel):
    """批量摄像头操作模型"""
    camera_ids: List[str] = Field(..., description="摄像头ID列表")
    operation: str = Field(..., description="操作类型")
    parameters: Optional[Dict[str, Any]] = Field(None, description="操作参数")

class CameraAlarmRule(BaseModel):
    """摄像头告警规则"""
    id: str = Field(..., description="规则ID")
    camera_id: str = Field(..., description="摄像头ID")
    algorithm_type: AlgorithmType = Field(..., description="算法类型")
    trigger_condition: Dict[str, Any] = Field(..., description="触发条件")
    alert_level: str = Field(..., description="告警级别")
    notification_methods: List[str] = Field(..., description="通知方式")
    is_active: bool = Field(default=True, description="是否激活")

# 响应模型
class CameraListResponse(BaseModel):
    """摄像头列表响应"""
    total: int = Field(..., description="总数量")
    cameras: List[Camera] = Field(..., description="摄像头列表")
    online_count: int = Field(..., description="在线数量")
    offline_count: int = Field(..., description="离线数量")

class CameraDetailResponse(BaseModel):
    """摄像头详情响应"""
    camera: Camera = Field(..., description="摄像头信息")
    config: Optional[CameraConfig] = Field(None, description="配置信息")
    stats: Optional[CameraStats] = Field(None, description="统计信息")
    stream: Optional[CameraStream] = Field(None, description="流信息")

class SystemOverview(BaseModel):
    """系统总览模型"""
    total_cameras: int = Field(..., description="摄像头总数")
    online_cameras: int = Field(..., description="在线摄像头数")
    active_algorithms: int = Field(..., description="活跃算法数")
    total_detections_today: int = Field(..., description="今日检测总数")
    system_load: float = Field(..., description="系统负载")
    edge_controllers: List[Dict[str, Any]] = Field(..., description="边缘控制器状态")
    recent_alerts: List[Dict[str, Any]] = Field(..., description="最近告警")