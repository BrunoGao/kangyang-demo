#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
配置API路由 - 边缘控制器版本
处理配置管理相关的HTTP请求
"""

import logging
from typing import Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import JSONResponse
from datetime import datetime
import yaml
import json

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/config", tags=["配置管理"])

@router.get("/")
async def get_config(request: Request):
    """获取当前配置信息"""
    try:
        config = getattr(request.app.state, 'config', {})
        
        # 过滤敏感信息
        safe_config = {
            "edge_controller": config.get("edge_controller", {}),
            "server": {
                "host": config.get("server", {}).get("host"),
                "port": config.get("server", {}).get("port"),
                "workers": config.get("server", {}).get("workers")
            },
            "cameras": config.get("cameras", {}),
            "detection": config.get("detection", {}),
            "management_platform": {
                "api_url": config.get("management_platform", {}).get("api_url"),
                "heartbeat_interval": config.get("management_platform", {}).get("heartbeat_interval")
            }
        }
        
        return {
            "success": True,
            "data": safe_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取配置失败")

@router.get("/detection")
async def get_detection_config(request: Request):
    """获取检测算法配置"""
    try:
        config = getattr(request.app.state, 'config', {})
        detection_config = config.get("detection", {})
        
        return {
            "success": True,
            "data": detection_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取检测配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取检测配置失败")

@router.put("/detection/{algorithm}")
async def update_algorithm_config(
    request: Request,
    algorithm: str,
    config_update: Dict[str, Any]
):
    """更新特定算法的配置"""
    try:
        config = getattr(request.app.state, 'config', {})
        algorithms = config.get('detection', {}).get('algorithms', {})
        
        if algorithm not in algorithms:
            raise HTTPException(
                status_code=404, 
                detail=f"算法不存在: {algorithm}"
            )
        
        # 验证配置字段
        allowed_fields = {
            'enabled', 'confidence_threshold', 'cooldown_period', 
            'min_fall_duration', 'sensitivity'
        }
        
        invalid_fields = set(config_update.keys()) - allowed_fields
        if invalid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"无效的配置字段: {list(invalid_fields)}"
            )
        
        # 更新配置
        algorithms[algorithm].update(config_update)
        
        # 通知摄像头管理器重新加载检测器
        camera_manager = getattr(request.app.state, 'camera_manager', None)
        if camera_manager and hasattr(camera_manager, 'reload_detector'):
            await camera_manager.reload_detector(algorithm)
        
        return {
            "success": True,
            "message": f"算法 {algorithm} 配置更新成功",
            "updated_config": algorithms[algorithm],
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新算法配置失败: {e}")
        raise HTTPException(status_code=500, detail="配置更新失败")

@router.get("/cameras")
async def get_camera_config(request: Request):
    """获取摄像头配置"""
    try:
        config = getattr(request.app.state, 'config', {})
        camera_config = config.get("cameras", {})
        
        # 添加当前活跃摄像头信息
        camera_manager = getattr(request.app.state, 'camera_manager', None)
        if camera_manager:
            camera_config["active_cameras"] = len(camera_manager.active_streams)
            camera_config["configured_cameras"] = list(camera_manager.active_streams.keys())
        
        return {
            "success": True,
            "data": camera_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取摄像头配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取摄像头配置失败")

@router.put("/cameras")
async def update_camera_config(
    request: Request,
    config_update: Dict[str, Any]
):
    """更新摄像头配置"""
    try:
        config = getattr(request.app.state, 'config', {})
        
        # 验证配置字段
        allowed_fields = {'max_cameras', 'frame_rate', 'resolution', 'quality'}
        invalid_fields = set(config_update.keys()) - allowed_fields
        
        if invalid_fields:
            raise HTTPException(
                status_code=400,
                detail=f"无效的配置字段: {list(invalid_fields)}"
            )
        
        # 更新配置
        camera_config = config.setdefault("cameras", {})
        camera_config.update(config_update)
        
        return {
            "success": True,
            "message": "摄像头配置更新成功",
            "updated_config": camera_config,
            "timestamp": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新摄像头配置失败: {e}")
        raise HTTPException(status_code=500, detail="摄像头配置更新失败")

@router.get("/system")
async def get_system_info(request: Request):
    """获取系统信息和状态"""
    try:
        config = getattr(request.app.state, 'config', {})
        
        # 获取系统组件状态
        camera_manager = getattr(request.app.state, 'camera_manager', None)
        event_sender = getattr(request.app.state, 'event_sender', None)
        local_cache = getattr(request.app.state, 'local_cache', None)
        
        system_info = {
            "controller_info": config.get("edge_controller", {}),
            "server_config": config.get("server", {}),
            "components_status": {
                "camera_manager": "running" if camera_manager else "not_initialized",
                "event_sender": "running" if event_sender else "not_initialized", 
                "local_cache": "running" if local_cache else "not_initialized"
            },
            "capabilities": [
                "video_stream_processing",
                "fall_detection",
                "fire_detection", 
                "smoke_detection",
                "real_time_alerts",
                "local_caching",
                "api_interface"
            ]
        }
        
        # 添加运行时统计
        if camera_manager:
            system_info["runtime_stats"] = {
                "active_cameras": len(camera_manager.active_streams),
                "uptime_seconds": camera_manager.get_uptime(),
                "processed_frames": getattr(camera_manager, 'processed_frames', 0)
            }
        
        return {
            "success": True,
            "data": system_info,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取系统信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取系统信息失败")

@router.post("/reload")
async def reload_config(request: Request):
    """重新加载配置（热重载）"""
    try:
        # 注意：这是一个简化版本，实际生产环境需要更复杂的热重载逻辑
        logger.info("配置热重载请求")
        
        # 这里可以重新加载配置文件并更新各个组件
        # 由于当前架构限制，返回提示信息
        
        return {
            "success": True,
            "message": "配置重载请求已接收，部分配置需要重启服务才能生效",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"重新加载配置失败: {e}")
        raise HTTPException(status_code=500, detail="配置重载失败")

@router.get("/defaults")
async def get_default_config():
    """获取默认配置模板"""
    try:
        default_config = {
            "edge_controller": {
                "id": "edge_controller_x",
                "name": "边缘控制器#X"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8084,
                "workers": 4,
                "log_level": "info"
            },
            "cameras": {
                "max_cameras": 11,
                "frame_rate": 8,
                "resolution": "1280x720",
                "quality": "medium"
            },
            "detection": {
                "algorithms": {
                    "fall_detection": {
                        "enabled": True,
                        "confidence_threshold": 0.8,
                        "min_fall_duration": 3.0,
                        "cooldown_period": 30
                    },
                    "fire_detection": {
                        "enabled": True,
                        "confidence_threshold": 0.85,
                        "cooldown_period": 10
                    },
                    "smoke_detection": {
                        "enabled": True,
                        "confidence_threshold": 0.80,
                        "cooldown_period": 15
                    }
                }
            },
            "management_platform": {
                "api_url": "http://localhost:8080/api",
                "heartbeat_interval": 10,
                "timeout": 30
            }
        }
        
        return {
            "success": True,
            "data": default_config,
            "message": "默认配置模板",
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取默认配置失败: {e}")
        raise HTTPException(status_code=500, detail="获取默认配置失败")