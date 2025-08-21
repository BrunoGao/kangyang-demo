#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
告警管理API路由
支持多级告警分类和处理流程
"""

from fastapi import APIRouter, HTTPException, Query
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta

from ..models.alert import (
    Alert, AlertRule, AlertLevel, AlertStatus, AlertType,
    AlertListResponse, AlertDetailResponse, BatchAlertOperation,
    AlertStatistics, AlertAction, AlertNotification, AlertEscalation
)
from ..core.alert_manager import alert_manager

router = APIRouter(prefix="/api/alert", tags=["alert"])

@router.get("/list", response_model=AlertListResponse)
async def get_alert_list(
    status: Optional[AlertStatus] = Query(None, description="按状态筛选"),
    alert_type: Optional[AlertType] = Query(None, description="按类型筛选"),
    alert_level: Optional[AlertLevel] = Query(None, description="按级别筛选"),
    camera_id: Optional[str] = Query(None, description="按摄像头筛选"),
    limit: int = Query(50, description="返回数量"),
    offset: int = Query(0, description="偏移量")
):
    """获取告警列表"""
    try:
        alerts = await alert_manager.get_alerts(
            status=status,
            alert_type=alert_type,
            alert_level=alert_level,
            camera_id=camera_id,
            limit=limit,
            offset=offset
        )
        
        statistics = await alert_manager.get_statistics()
        
        return AlertListResponse(
            total=len(alerts),
            alerts=alerts,
            statistics=statistics
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警列表失败: {str(e)}")

@router.get("/{alert_id}", response_model=AlertDetailResponse)
async def get_alert_detail(alert_id: str):
    """获取告警详情"""
    try:
        alert = await alert_manager.get_alert_detail(alert_id)
        if not alert:
            raise HTTPException(status_code=404, detail="告警不存在")
        
        actions = await alert_manager.get_alert_actions(alert_id)
        notifications = await alert_manager.get_alert_notifications(alert_id)
        escalations = await alert_manager.get_alert_escalations(alert_id)
        
        return AlertDetailResponse(
            alert=alert,
            actions=actions,
            notifications=notifications,
            escalations=escalations
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取告警详情失败: {str(e)}")

@router.post("/create")
async def create_alert(
    alert_type: AlertType,
    title: str,
    description: str,
    camera_id: Optional[str] = None,
    camera_name: Optional[str] = None,
    location: Optional[str] = None,
    confidence: Optional[float] = None,
    algorithm_name: Optional[str] = None,
    detection_data: Optional[Dict[str, Any]] = None
):
    """创建告警"""
    try:
        alert_id = await alert_manager.create_alert(
            alert_type=alert_type,
            title=title,
            description=description,
            camera_id=camera_id,
            camera_name=camera_name,
            location=location,
            confidence=confidence,
            algorithm_name=algorithm_name,
            detection_data=detection_data
        )
        
        return {
            "success": True,
            "alert_id": alert_id,
            "message": "告警创建成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建告警失败: {str(e)}")

@router.post("/{alert_id}/acknowledge")
async def acknowledge_alert(
    alert_id: str,
    operator: str,
    notes: Optional[str] = None
):
    """确认告警"""
    try:
        success = await alert_manager.acknowledge_alert(alert_id, operator, notes)
        if success:
            return {"success": True, "message": "告警确认成功"}
        else:
            raise HTTPException(status_code=400, detail="告警确认失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"确认告警失败: {str(e)}")

@router.post("/{alert_id}/resolve")
async def resolve_alert(
    alert_id: str,
    operator: str,
    resolution_notes: str
):
    """解决告警"""
    try:
        success = await alert_manager.resolve_alert(alert_id, operator, resolution_notes)
        if success:
            return {"success": True, "message": "告警解决成功"}
        else:
            raise HTTPException(status_code=400, detail="告警解决失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"解决告警失败: {str(e)}")

@router.post("/{alert_id}/false_alarm")
async def mark_false_alarm(
    alert_id: str,
    operator: str,
    notes: Optional[str] = None
):
    """标记为误报"""
    try:
        success = await alert_manager.mark_false_alarm(alert_id, operator, notes)
        if success:
            return {"success": True, "message": "标记误报成功"}
        else:
            raise HTTPException(status_code=400, detail="标记误报失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"标记误报失败: {str(e)}")

@router.post("/{alert_id}/escalate")
async def escalate_alert(
    alert_id: str,
    new_level: AlertLevel,
    reason: str,
    operator: str = "manual"
):
    """升级告警"""
    try:
        success = await alert_manager.escalate_alert(alert_id, new_level, reason, auto=False)
        if success:
            return {"success": True, "message": "告警升级成功"}
        else:
            raise HTTPException(status_code=400, detail="告警升级失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"升级告警失败: {str(e)}")

@router.post("/batch/operation")
async def batch_alert_operation(operation: BatchAlertOperation):
    """批量告警操作"""
    try:
        results = await alert_manager.batch_operation(
            alert_ids=operation.alert_ids,
            operation=operation.operation,
            operator=operation.operator,
            notes=operation.notes
        )
        
        return {
            "success": True,
            "operation": operation.operation,
            "results": results,
            "total_processed": len(operation.alert_ids),
            "successful": sum(1 for v in results.values() if v)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")

@router.get("/statistics/overview", response_model=AlertStatistics)
async def get_alert_statistics():
    """获取告警统计信息"""
    try:
        statistics = await alert_manager.get_statistics()
        return statistics
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/statistics/trend")
async def get_alert_trend(
    days: int = Query(7, description="天数"),
    alert_type: Optional[AlertType] = Query(None, description="告警类型")
):
    """获取告警趋势数据"""
    try:
        # 这里可以实现更复杂的趋势分析
        # 暂时返回模拟数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=days)
        
        trend_data = []
        for i in range(days):
            date = start_date + timedelta(days=i)
            # 模拟数据
            trend_data.append({
                "date": date.strftime("%Y-%m-%d"),
                "total_alerts": max(0, 10 + i * 2 + (i % 3)),
                "fall_alerts": max(0, 3 + i % 4),
                "fire_alerts": max(0, 1 + i % 2),
                "smoke_alerts": max(0, 2 + i % 3),
                "resolved_rate": min(100, 60 + i * 3)
            })
        
        return {
            "success": True,
            "period": f"{start_date.strftime('%Y-%m-%d')} 至 {end_date.strftime('%Y-%m-%d')}",
            "trend_data": trend_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取趋势数据失败: {str(e)}")

@router.get("/levels/list")
async def get_alert_levels():
    """获取告警级别列表"""
    return {
        "alert_levels": [
            {
                "level": AlertLevel.CRITICAL,
                "name": "紧急",
                "color": "#FF4444",
                "description": "需要立即处理的紧急情况"
            },
            {
                "level": AlertLevel.HIGH,
                "name": "高级",
                "color": "#FF8800",
                "description": "需要尽快处理的重要事件"
            },
            {
                "level": AlertLevel.MEDIUM,
                "name": "中级",
                "color": "#FFAA00",
                "description": "需要关注的一般事件"
            },
            {
                "level": AlertLevel.LOW,
                "name": "低级",
                "color": "#88CC00",
                "description": "轻微的提醒事件"
            }
        ]
    }

@router.get("/types/list")
async def get_alert_types():
    """获取告警类型列表"""
    return {
        "alert_types": [
            {
                "type": AlertType.FALL_DETECTION,
                "name": "跌倒检测",
                "icon": "👤",
                "description": "检测到人员跌倒事件"
            },
            {
                "type": AlertType.FIRE_DETECTION,
                "name": "火焰检测",
                "icon": "🔥",
                "description": "检测到火焰燃烧现象"
            },
            {
                "type": AlertType.SMOKE_DETECTION,
                "name": "烟雾检测",
                "icon": "💨",
                "description": "检测到烟雾扩散"
            },
            {
                "type": AlertType.SYSTEM_ERROR,
                "name": "系统错误",
                "icon": "⚠️",
                "description": "系统运行异常"
            },
            {
                "type": AlertType.CAMERA_OFFLINE,
                "name": "摄像头离线",
                "icon": "📹",
                "description": "摄像头连接异常"
            },
            {
                "type": AlertType.ALGORITHM_ERROR,
                "name": "算法错误",
                "icon": "🤖",
                "description": "AI算法处理异常"
            }
        ]
    }

@router.post("/demo/create_test_alerts")
async def create_test_alerts():
    """创建测试告警数据"""
    try:
        test_alerts = [
            {
                "alert_type": AlertType.FALL_DETECTION,
                "title": "检测到跌倒事件",
                "description": "房间201检测到老人跌倒",
                "camera_id": "camera_01",
                "camera_name": "摄像头01号",
                "location": "楼层1-房间1",
                "confidence": 0.92,
                "algorithm_name": "FallDetector"
            },
            {
                "alert_type": AlertType.FIRE_DETECTION,
                "title": "检测到火焰",
                "description": "厨房区域检测到火焰",
                "camera_id": "camera_15",
                "camera_name": "摄像头15号",
                "location": "楼层3-厨房",
                "confidence": 0.88,
                "algorithm_name": "FireDetector"
            },
            {
                "alert_type": AlertType.SMOKE_DETECTION,
                "title": "检测到烟雾",
                "description": "走廊检测到烟雾扩散",
                "camera_id": "camera_08",
                "camera_name": "摄像头08号",
                "location": "楼层2-走廊",
                "confidence": 0.76,
                "algorithm_name": "SmokeDetector"
            }
        ]
        
        created_alerts = []
        for alert_data in test_alerts:
            alert_id = await alert_manager.create_alert(**alert_data)
            created_alerts.append(alert_id)
        
        return {
            "success": True,
            "message": f"创建了 {len(created_alerts)} 个测试告警",
            "alert_ids": created_alerts
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"创建测试告警失败: {str(e)}")