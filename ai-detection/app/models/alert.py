#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警管理数据模型
支持多级告警分类和处理流程
"""

from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
from datetime import datetime
from enum import Enum

class AlertLevel(str, Enum):
    """告警级别"""
    LOW = "low"           # 低级告警
    MEDIUM = "medium"     # 中级告警
    HIGH = "high"         # 高级告警
    CRITICAL = "critical" # 紧急告警

class AlertStatus(str, Enum):
    """告警状态"""
    PENDING = "pending"       # 待处理
    ACKNOWLEDGED = "acknowledged"  # 已确认
    IN_PROGRESS = "in_progress"   # 处理中
    RESOLVED = "resolved"     # 已解决
    CLOSED = "closed"         # 已关闭
    FALSE_ALARM = "false_alarm"   # 误报

class AlertType(str, Enum):
    """告警类型"""
    FALL_DETECTION = "fall_detection"
    FIRE_DETECTION = "fire_detection"
    SMOKE_DETECTION = "smoke_detection"
    SYSTEM_ERROR = "system_error"
    CAMERA_OFFLINE = "camera_offline"
    ALGORITHM_ERROR = "algorithm_error"

class NotificationChannel(str, Enum):
    """通知渠道"""
    WECHAT = "wechat"
    SMS = "sms"
    EMAIL = "email"
    APP_PUSH = "app_push"
    DASHBOARD = "dashboard"

class Alert(BaseModel):
    """告警基础模型"""
    id: str = Field(..., description="告警唯一ID")
    title: str = Field(..., description="告警标题")
    description: str = Field(..., description="告警描述")
    alert_type: AlertType = Field(..., description="告警类型")
    alert_level: AlertLevel = Field(..., description="告警级别")
    status: AlertStatus = Field(default=AlertStatus.PENDING, description="告警状态")
    
    # 关联信息
    camera_id: Optional[str] = Field(None, description="关联摄像头ID")
    camera_name: Optional[str] = Field(None, description="摄像头名称")
    location: Optional[str] = Field(None, description="发生位置")
    
    # 检测信息
    confidence: Optional[float] = Field(None, description="检测置信度")
    algorithm_name: Optional[str] = Field(None, description="算法名称")
    frame_number: Optional[int] = Field(None, description="帧编号")
    detection_data: Optional[Dict[str, Any]] = Field(None, description="检测数据")
    
    # 时间信息
    triggered_at: datetime = Field(default_factory=datetime.now, description="触发时间")
    acknowledged_at: Optional[datetime] = Field(None, description="确认时间")
    resolved_at: Optional[datetime] = Field(None, description="解决时间")
    
    # 处理信息
    assigned_to: Optional[str] = Field(None, description="分配给")
    handler_notes: Optional[str] = Field(None, description="处理备注")
    resolution_notes: Optional[str] = Field(None, description="解决备注")
    
    # 通知信息
    notification_sent: bool = Field(default=False, description="是否已发送通知")
    notification_channels: List[NotificationChannel] = Field(default=[], description="通知渠道")
    notification_count: int = Field(default=0, description="通知次数")
    
    class Config:
        json_encoders = {
            datetime: lambda dt: dt.isoformat()
        }

class AlertRule(BaseModel):
    """告警规则模型"""
    id: str = Field(..., description="规则ID")
    name: str = Field(..., description="规则名称")
    description: Optional[str] = Field(None, description="规则描述")
    
    # 触发条件
    alert_type: AlertType = Field(..., description="告警类型")
    camera_ids: List[str] = Field(default=[], description="适用摄像头")
    confidence_threshold: float = Field(default=0.8, description="置信度阈值")
    frequency_threshold: int = Field(default=1, description="频次阈值")
    time_window_minutes: int = Field(default=5, description="时间窗口(分钟)")
    
    # 告警设置
    alert_level: AlertLevel = Field(..., description="告警级别")
    auto_escalate: bool = Field(default=False, description="自动升级")
    escalate_after_minutes: int = Field(default=30, description="升级等待时间")
    
    # 通知设置
    notification_channels: List[NotificationChannel] = Field(..., description="通知渠道")
    notification_template: Optional[str] = Field(None, description="通知模板")
    
    # 处理设置
    auto_assign: bool = Field(default=False, description="自动分配")
    default_assignee: Optional[str] = Field(None, description="默认处理人")
    
    # 状态
    is_active: bool = Field(default=True, description="是否激活")
    created_at: datetime = Field(default_factory=datetime.now, description="创建时间")
    updated_at: datetime = Field(default_factory=datetime.now, description="更新时间")

class AlertAction(BaseModel):
    """告警操作记录"""
    id: str = Field(..., description="操作ID")
    alert_id: str = Field(..., description="告警ID")
    action_type: str = Field(..., description="操作类型")
    operator: str = Field(..., description="操作人")
    notes: Optional[str] = Field(None, description="操作备注")
    timestamp: datetime = Field(default_factory=datetime.now, description="操作时间")
    
class AlertStatistics(BaseModel):
    """告警统计模型"""
    total_alerts: int = Field(default=0, description="总告警数")
    pending_alerts: int = Field(default=0, description="待处理告警")
    resolved_alerts: int = Field(default=0, description="已解决告警")
    false_alarms: int = Field(default=0, description="误报数")
    
    # 按级别统计
    critical_alerts: int = Field(default=0, description="紧急告警")
    high_alerts: int = Field(default=0, description="高级告警")
    medium_alerts: int = Field(default=0, description="中级告警")
    low_alerts: int = Field(default=0, description="低级告警")
    
    # 按类型统计
    fall_alerts: int = Field(default=0, description="跌倒告警")
    fire_alerts: int = Field(default=0, description="火焰告警")
    smoke_alerts: int = Field(default=0, description="烟雾告警")
    system_alerts: int = Field(default=0, description="系统告警")
    
    # 时间统计
    avg_response_time_minutes: float = Field(default=0.0, description="平均响应时间")
    avg_resolution_time_minutes: float = Field(default=0.0, description="平均解决时间")
    
    # 趋势数据
    alerts_trend: List[Dict[str, Any]] = Field(default=[], description="告警趋势")

class AlertNotification(BaseModel):
    """告警通知模型"""
    id: str = Field(..., description="通知ID")
    alert_id: str = Field(..., description="告警ID")
    channel: NotificationChannel = Field(..., description="通知渠道")
    recipient: str = Field(..., description="接收者")
    content: str = Field(..., description="通知内容")
    status: str = Field(..., description="发送状态")
    sent_at: datetime = Field(default_factory=datetime.now, description="发送时间")
    delivery_status: Optional[str] = Field(None, description="投递状态")
    error_message: Optional[str] = Field(None, description="错误信息")

class AlertEscalation(BaseModel):
    """告警升级模型"""
    id: str = Field(..., description="升级ID")
    alert_id: str = Field(..., description="告警ID")
    from_level: AlertLevel = Field(..., description="原级别")
    to_level: AlertLevel = Field(..., description="目标级别")
    reason: str = Field(..., description="升级原因")
    auto_escalated: bool = Field(default=False, description="是否自动升级")
    escalated_at: datetime = Field(default_factory=datetime.now, description="升级时间")

# 响应模型
class AlertListResponse(BaseModel):
    """告警列表响应"""
    total: int = Field(..., description="总数")
    alerts: List[Alert] = Field(..., description="告警列表")
    statistics: AlertStatistics = Field(..., description="统计信息")

class AlertDetailResponse(BaseModel):
    """告警详情响应"""
    alert: Alert = Field(..., description="告警信息")
    actions: List[AlertAction] = Field(default=[], description="操作记录")
    notifications: List[AlertNotification] = Field(default=[], description="通知记录")
    escalations: List[AlertEscalation] = Field(default=[], description="升级记录")

class BatchAlertOperation(BaseModel):
    """批量告警操作"""
    alert_ids: List[str] = Field(..., description="告警ID列表")
    operation: str = Field(..., description="操作类型")
    operator: str = Field(..., description="操作人")
    notes: Optional[str] = Field(None, description="操作备注")