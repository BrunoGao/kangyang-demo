#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信API路由模块
"""

from fastapi import APIRouter, HTTPException
from typing import Dict, Any
from datetime import datetime
import time

from ..core.wechat_notifier import get_wechat_notifier, init_wechat_notifier, AlertEvent

router = APIRouter(prefix="/api/wechat", tags=["wechat"])

@router.post("/init")
async def init_wechat(config: Dict[str, str]):
    """初始化微信通知器"""
    try:
        app_id = config.get('app_id')
        app_secret = config.get('app_secret')
        
        if not app_id or not app_secret:
            raise HTTPException(status_code=400, detail="缺少app_id或app_secret")
        
        notifier = init_wechat_notifier(app_id, app_secret)
        
        return {
            'success': True,
            'message': '微信通知器初始化成功',
            'app_id': app_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'初始化失败: {str(e)}')

@router.post("/subscribe")
async def add_subscriber(data: Dict[str, str]):
    """添加微信订阅用户"""
    try:
        openid = data.get('openid')
        if not openid:
            raise HTTPException(status_code=400, detail="缺少openid")
        
        notifier = get_wechat_notifier()
        if not notifier:
            raise HTTPException(status_code=400, detail="微信通知器未初始化")
        
        notifier.add_subscriber(openid)
        
        return {
            'success': True,
            'message': f'用户 {openid} 订阅成功'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'订阅失败: {str(e)}')

@router.delete("/subscribe")
async def remove_subscriber(data: Dict[str, str]):
    """移除微信订阅用户"""
    try:
        openid = data.get('openid')
        if not openid:
            raise HTTPException(status_code=400, detail="缺少openid")
        
        notifier = get_wechat_notifier()
        if not notifier:
            raise HTTPException(status_code=400, detail="微信通知器未初始化")
        
        notifier.remove_subscriber(openid)
        
        return {
            'success': True,
            'message': f'用户 {openid} 取消订阅成功'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'取消订阅失败: {str(e)}')

@router.post("/test")
async def test_wechat_notification(data: Dict[str, Any]):
    """测试微信通知"""
    try:
        notifier = get_wechat_notifier()
        if not notifier:
            raise HTTPException(status_code=400, detail="微信通知器未初始化")
        
        # 创建测试事件
        test_event = AlertEvent(
            event_type=data.get('event_type', 'fall'),
            event_subtype=data.get('event_subtype', 'test_fall'),
            confidence=data.get('confidence', 0.95),
            timestamp=time.time(),
            location=data.get('location', '测试位置'),
            severity=data.get('severity', 'HIGH')
        )
        
        # 发送测试通知
        result = await notifier.send_alert(test_event)
        
        return {
            'success': result,
            'message': '测试通知发送成功' if result else '测试通知发送失败'
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'测试失败: {str(e)}')

@router.get("/status")
async def get_wechat_status():
    """获取微信通知器状态"""
    try:
        notifier = get_wechat_notifier()
        if not notifier:
            return {
                'initialized': False,
                'subscribers_count': 0,
                'message': '微信通知器未初始化'
            }
        
        return {
            'initialized': True,
            'subscribers_count': len(notifier.subscribers),
            'app_id': notifier.config.app_id,
            'token_valid': bool(notifier.config.access_token),
            'last_check': datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'获取状态失败: {str(e)}')