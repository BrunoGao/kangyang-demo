#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查API
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
from datetime import datetime

router = APIRouter(tags=["health"])

@router.get("/health")
async def health_check(request: Request) -> Dict[str, Any]:
    """健康检查接口"""
    try:
        camera_manager = getattr(request.app.state, 'camera_manager', None)
        local_cache = getattr(request.app.state, 'local_cache', None)
        event_sender = getattr(request.app.state, 'event_sender', None)
        
        # 检查组件状态
        components = {
            "camera_manager": "healthy" if camera_manager else "unavailable",
            "local_cache": "healthy" if local_cache else "unavailable", 
            "event_sender": "healthy" if event_sender else "unavailable"
        }
        
        # 获取系统统计
        stats = {}
        if camera_manager:
            stats = await camera_manager.get_system_stats()
        
        # 获取连接状态
        connection_status = {}
        if event_sender:
            connection_status = await event_sender.get_connection_status()
        
        return {
            "status": "healthy",
            "service": "康养AI检测系统 - 边缘控制器",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "system_stats": stats,
            "management_platform_connection": connection_status
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }