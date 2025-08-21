#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警管理核心模块
支持多级告警分类、处理流程和通知推送
"""

import asyncio
import uuid
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from collections import defaultdict

from ..models.alert import (
    Alert, AlertRule, AlertLevel, AlertStatus, AlertType, 
    NotificationChannel, AlertAction, AlertStatistics,
    AlertNotification, AlertEscalation
)
from .wechat_notifier import get_wechat_notifier, AlertEvent

logger = logging.getLogger(__name__)

class AlertManager:
    """告警管理器"""
    
    def __init__(self):
        """初始化告警管理器"""
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: Dict[str, AlertRule] = {}
        self.alert_actions: Dict[str, List[AlertAction]] = defaultdict(list)
        self.alert_notifications: Dict[str, List[AlertNotification]] = defaultdict(list)
        self.alert_escalations: Dict[str, List[AlertEscalation]] = defaultdict(list)
        
        # 统计信息
        self.statistics = AlertStatistics()
        
        # 默认告警规则
        self._init_default_rules()
        
        logger.info("告警管理器初始化完成")
    
    def _init_default_rules(self):
        """初始化默认告警规则"""
        default_rules = [
            AlertRule(
                id="fall_detection_rule",
                name="跌倒检测告警规则",
                description="检测到跌倒事件时触发告警",
                alert_type=AlertType.FALL_DETECTION,
                confidence_threshold=0.85,
                alert_level=AlertLevel.HIGH,
                notification_channels=[NotificationChannel.WECHAT, NotificationChannel.DASHBOARD],
                auto_escalate=True,
                escalate_after_minutes=10
            ),
            AlertRule(
                id="fire_detection_rule",
                name="火焰检测告警规则",
                description="检测到火焰时立即触发紧急告警",
                alert_type=AlertType.FIRE_DETECTION,
                confidence_threshold=0.80,
                alert_level=AlertLevel.CRITICAL,
                notification_channels=[NotificationChannel.WECHAT, NotificationChannel.SMS, NotificationChannel.DASHBOARD],
                auto_escalate=False
            ),
            AlertRule(
                id="smoke_detection_rule",
                name="烟雾检测告警规则",
                description="检测到烟雾时触发高级告警",
                alert_type=AlertType.SMOKE_DETECTION,
                confidence_threshold=0.75,
                alert_level=AlertLevel.HIGH,
                notification_channels=[NotificationChannel.WECHAT, NotificationChannel.DASHBOARD],
                auto_escalate=True,
                escalate_after_minutes=15
            ),
            AlertRule(
                id="camera_offline_rule",
                name="摄像头离线告警规则",
                description="摄像头离线时触发系统告警",
                alert_type=AlertType.CAMERA_OFFLINE,
                confidence_threshold=1.0,
                alert_level=AlertLevel.MEDIUM,
                notification_channels=[NotificationChannel.DASHBOARD],
                auto_escalate=False
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.id] = rule
        
        logger.info(f"已加载 {len(default_rules)} 个默认告警规则")
    
    async def create_alert(self, 
                          alert_type: AlertType,
                          title: str,
                          description: str,
                          camera_id: Optional[str] = None,
                          camera_name: Optional[str] = None,
                          location: Optional[str] = None,
                          confidence: Optional[float] = None,
                          algorithm_name: Optional[str] = None,
                          detection_data: Optional[Dict[str, Any]] = None) -> str:
        """
        创建新告警
        
        Returns:
            告警ID
        """
        try:
            # 查找匹配的告警规则
            matching_rule = self._find_matching_rule(alert_type, camera_id, confidence)
            
            if not matching_rule:
                logger.warning(f"未找到匹配的告警规则: {alert_type}")
                alert_level = AlertLevel.MEDIUM
            else:
                alert_level = matching_rule.alert_level
            
            # 创建告警
            alert_id = str(uuid.uuid4())
            alert = Alert(
                id=alert_id,
                title=title,
                description=description,
                alert_type=alert_type,
                alert_level=alert_level,
                camera_id=camera_id,
                camera_name=camera_name,
                location=location,
                confidence=confidence,
                algorithm_name=algorithm_name,
                detection_data=detection_data
            )
            
            self.alerts[alert_id] = alert
            
            # 更新统计
            self._update_statistics_for_new_alert(alert)
            
            # 记录创建操作
            await self._add_alert_action(
                alert_id, "created", "system", f"告警创建: {title}"
            )
            
            # 发送通知
            if matching_rule:
                await self._send_notifications(alert, matching_rule.notification_channels)
                
                # 设置自动升级
                if matching_rule.auto_escalate:
                    asyncio.create_task(
                        self._schedule_escalation(alert_id, matching_rule.escalate_after_minutes)
                    )
            
            logger.info(f"告警创建成功: {alert_id} - {title}")
            return alert_id
            
        except Exception as e:
            logger.error(f"创建告警失败: {str(e)}")
            raise
    
    def _find_matching_rule(self, alert_type: AlertType, camera_id: Optional[str], confidence: Optional[float]) -> Optional[AlertRule]:
        """查找匹配的告警规则"""
        for rule in self.alert_rules.values():
            if not rule.is_active:
                continue
                
            if rule.alert_type != alert_type:
                continue
                
            if camera_id and rule.camera_ids and camera_id not in rule.camera_ids:
                continue
                
            if confidence is not None and confidence < rule.confidence_threshold:
                continue
                
            return rule
        
        return None
    
    async def acknowledge_alert(self, alert_id: str, operator: str, notes: Optional[str] = None) -> bool:
        """确认告警"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            if alert.status != AlertStatus.PENDING:
                logger.warning(f"告警状态不是待处理: {alert_id} - {alert.status}")
                return False
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_at = datetime.now()
            if notes:
                alert.handler_notes = notes
            
            await self._add_alert_action(alert_id, "acknowledged", operator, notes)
            
            logger.info(f"告警已确认: {alert_id} by {operator}")
            return True
            
        except Exception as e:
            logger.error(f"确认告警失败: {str(e)}")
            return False
    
    async def resolve_alert(self, alert_id: str, operator: str, resolution_notes: str) -> bool:
        """解决告警"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            if alert.status in [AlertStatus.RESOLVED, AlertStatus.CLOSED]:
                logger.warning(f"告警已解决或关闭: {alert_id}")
                return False
            
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            alert.resolution_notes = resolution_notes
            
            await self._add_alert_action(alert_id, "resolved", operator, resolution_notes)
            
            # 更新统计
            self.statistics.resolved_alerts += 1
            
            logger.info(f"告警已解决: {alert_id} by {operator}")
            return True
            
        except Exception as e:
            logger.error(f"解决告警失败: {str(e)}")
            return False
    
    async def mark_false_alarm(self, alert_id: str, operator: str, notes: Optional[str] = None) -> bool:
        """标记为误报"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            alert.status = AlertStatus.FALSE_ALARM
            
            await self._add_alert_action(alert_id, "mark_false_alarm", operator, notes)
            
            # 更新统计
            self.statistics.false_alarms += 1
            
            logger.info(f"告警标记为误报: {alert_id} by {operator}")
            return True
            
        except Exception as e:
            logger.error(f"标记误报失败: {str(e)}")
            return False
    
    async def escalate_alert(self, alert_id: str, new_level: AlertLevel, reason: str, auto: bool = False) -> bool:
        """升级告警"""
        try:
            if alert_id not in self.alerts:
                return False
            
            alert = self.alerts[alert_id]
            old_level = alert.alert_level
            
            if old_level == new_level:
                return True
            
            alert.alert_level = new_level
            
            # 记录升级
            escalation = AlertEscalation(
                id=str(uuid.uuid4()),
                alert_id=alert_id,
                from_level=old_level,
                to_level=new_level,
                reason=reason,
                auto_escalated=auto
            )
            
            self.alert_escalations[alert_id].append(escalation)
            
            await self._add_alert_action(
                alert_id, "escalated", "system" if auto else "manual",
                f"告警升级: {old_level} -> {new_level}, 原因: {reason}"
            )
            
            # 发送升级通知
            await self._send_escalation_notification(alert, escalation)
            
            logger.info(f"告警已升级: {alert_id} - {old_level} -> {new_level}")
            return True
            
        except Exception as e:
            logger.error(f"升级告警失败: {str(e)}")
            return False
    
    async def _send_notifications(self, alert: Alert, channels: List[NotificationChannel]):
        """发送告警通知"""
        try:
            for channel in channels:
                if channel == NotificationChannel.WECHAT:
                    await self._send_wechat_notification(alert)
                elif channel == NotificationChannel.DASHBOARD:
                    await self._send_dashboard_notification(alert)
                # 其他通知渠道可以在这里扩展
            
            alert.notification_sent = True
            alert.notification_channels = channels
            alert.notification_count += 1
            
        except Exception as e:
            logger.error(f"发送通知失败: {str(e)}")
    
    async def _send_wechat_notification(self, alert: Alert):
        """发送微信通知"""
        try:
            wechat_notifier = get_wechat_notifier()
            if not wechat_notifier:
                logger.warning("微信通知器未初始化")
                return
            
            # 转换为微信告警事件
            alert_event = AlertEvent(
                event_type=alert.alert_type.value.replace('_detection', ''),
                event_subtype=alert.description,
                confidence=alert.confidence or 0.0,
                timestamp=alert.triggered_at.timestamp(),
                location=alert.location or "未知位置",
                severity=alert.alert_level.value.upper(),
                video_file=alert.camera_id or "",
                frame_number=alert.detection_data.get('frame_number', 0) if alert.detection_data else 0
            )
            
            success = await wechat_notifier.send_alert(alert_event)
            
            # 记录通知
            notification = AlertNotification(
                id=str(uuid.uuid4()),
                alert_id=alert.id,
                channel=NotificationChannel.WECHAT,
                recipient="微信订阅用户",
                content=f"{alert.title} - {alert.description}",
                status="sent" if success else "failed"
            )
            
            self.alert_notifications[alert.id].append(notification)
            
        except Exception as e:
            logger.error(f"发送微信通知失败: {str(e)}")
    
    async def _send_dashboard_notification(self, alert: Alert):
        """发送监控大屏通知"""
        try:
            # 这里可以实现WebSocket推送到监控大屏
            # 暂时记录通知日志
            notification = AlertNotification(
                id=str(uuid.uuid4()),
                alert_id=alert.id,
                channel=NotificationChannel.DASHBOARD,
                recipient="监控大屏",
                content=f"{alert.title} - {alert.description}",
                status="sent"
            )
            
            self.alert_notifications[alert.id].append(notification)
            
        except Exception as e:
            logger.error(f"发送监控大屏通知失败: {str(e)}")
    
    async def _send_escalation_notification(self, alert: Alert, escalation: AlertEscalation):
        """发送升级通知"""
        try:
            # 升级后重新发送通知
            channels = [NotificationChannel.WECHAT, NotificationChannel.DASHBOARD]
            await self._send_notifications(alert, channels)
            
        except Exception as e:
            logger.error(f"发送升级通知失败: {str(e)}")
    
    async def _schedule_escalation(self, alert_id: str, delay_minutes: int):
        """计划自动升级"""
        try:
            await asyncio.sleep(delay_minutes * 60)
            
            alert = self.alerts.get(alert_id)
            if not alert:
                return
            
            # 检查是否需要升级
            if alert.status == AlertStatus.PENDING:
                new_level = self._get_escalated_level(alert.alert_level)
                if new_level != alert.alert_level:
                    await self.escalate_alert(
                        alert_id, new_level, 
                        f"超时自动升级 ({delay_minutes}分钟未处理)", 
                        auto=True
                    )
            
        except Exception as e:
            logger.error(f"自动升级失败: {str(e)}")
    
    def _get_escalated_level(self, current_level: AlertLevel) -> AlertLevel:
        """获取升级后的告警级别"""
        escalation_map = {
            AlertLevel.LOW: AlertLevel.MEDIUM,
            AlertLevel.MEDIUM: AlertLevel.HIGH,
            AlertLevel.HIGH: AlertLevel.CRITICAL,
            AlertLevel.CRITICAL: AlertLevel.CRITICAL  # 最高级别
        }
        return escalation_map.get(current_level, current_level)
    
    async def _add_alert_action(self, alert_id: str, action_type: str, operator: str, notes: Optional[str]):
        """添加告警操作记录"""
        action = AlertAction(
            id=str(uuid.uuid4()),
            alert_id=alert_id,
            action_type=action_type,
            operator=operator,
            notes=notes
        )
        
        self.alert_actions[alert_id].append(action)
    
    def _update_statistics_for_new_alert(self, alert: Alert):
        """更新新告警的统计信息"""
        self.statistics.total_alerts += 1
        self.statistics.pending_alerts += 1
        
        # 按级别统计
        if alert.alert_level == AlertLevel.CRITICAL:
            self.statistics.critical_alerts += 1
        elif alert.alert_level == AlertLevel.HIGH:
            self.statistics.high_alerts += 1
        elif alert.alert_level == AlertLevel.MEDIUM:
            self.statistics.medium_alerts += 1
        elif alert.alert_level == AlertLevel.LOW:
            self.statistics.low_alerts += 1
        
        # 按类型统计
        if alert.alert_type == AlertType.FALL_DETECTION:
            self.statistics.fall_alerts += 1
        elif alert.alert_type == AlertType.FIRE_DETECTION:
            self.statistics.fire_alerts += 1
        elif alert.alert_type == AlertType.SMOKE_DETECTION:
            self.statistics.smoke_alerts += 1
        else:
            self.statistics.system_alerts += 1
    
    async def get_alerts(self, 
                        status: Optional[AlertStatus] = None,
                        alert_type: Optional[AlertType] = None,
                        alert_level: Optional[AlertLevel] = None,
                        camera_id: Optional[str] = None,
                        limit: int = 50,
                        offset: int = 0) -> List[Alert]:
        """获取告警列表"""
        alerts = list(self.alerts.values())
        
        # 应用筛选条件
        if status:
            alerts = [a for a in alerts if a.status == status]
        if alert_type:
            alerts = [a for a in alerts if a.alert_type == alert_type]
        if alert_level:
            alerts = [a for a in alerts if a.alert_level == alert_level]
        if camera_id:
            alerts = [a for a in alerts if a.camera_id == camera_id]
        
        # 按触发时间倒序排列
        alerts.sort(key=lambda x: x.triggered_at, reverse=True)
        
        # 分页
        return alerts[offset:offset + limit]
    
    async def get_alert_detail(self, alert_id: str) -> Optional[Alert]:
        """获取告警详情"""
        return self.alerts.get(alert_id)
    
    async def get_alert_actions(self, alert_id: str) -> List[AlertAction]:
        """获取告警操作记录"""
        return self.alert_actions.get(alert_id, [])
    
    async def get_alert_notifications(self, alert_id: str) -> List[AlertNotification]:
        """获取告警通知记录"""
        return self.alert_notifications.get(alert_id, [])
    
    async def get_alert_escalations(self, alert_id: str) -> List[AlertEscalation]:
        """获取告警升级记录"""
        return self.alert_escalations.get(alert_id, [])
    
    async def get_statistics(self) -> AlertStatistics:
        """获取告警统计信息"""
        return self.statistics
    
    async def batch_operation(self, alert_ids: List[str], operation: str, operator: str, notes: Optional[str] = None) -> Dict[str, bool]:
        """批量操作告警"""
        results = {}
        
        for alert_id in alert_ids:
            try:
                if operation == "acknowledge":
                    results[alert_id] = await self.acknowledge_alert(alert_id, operator, notes)
                elif operation == "resolve":
                    results[alert_id] = await self.resolve_alert(alert_id, operator, notes or "批量解决")
                elif operation == "mark_false_alarm":
                    results[alert_id] = await self.mark_false_alarm(alert_id, operator, notes)
                else:
                    results[alert_id] = False
            except Exception as e:
                logger.error(f"批量操作失败 {alert_id}: {str(e)}")
                results[alert_id] = False
        
        return results

# 全局告警管理器实例
alert_manager = AlertManager()