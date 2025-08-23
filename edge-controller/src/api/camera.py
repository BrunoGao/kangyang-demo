#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头管理API
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime

router = APIRouter(tags=["camera"])

class CameraRequest(BaseModel):
    """摄像头请求模型"""
    id: str
    name: str
    rtsp_url: str
    location: str
    zone_id: Optional[str] = ""
    enabled_algorithms: Optional[List[str]] = ["fall_detection"]

@router.get("/cameras")
async def get_cameras(request: Request) -> Dict[str, Any]:
    """获取摄像头列表"""
    try:
        camera_manager = request.app.state.camera_manager
        cameras = await camera_manager.get_camera_list()
        
        return {
            "success": True,
            "cameras": cameras,
            "total": len(cameras),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取摄像头列表失败: {str(e)}")

@router.post("/cameras")
async def add_camera(camera_data: CameraRequest, request: Request) -> Dict[str, Any]:
    """添加摄像头"""
    try:
        camera_manager = request.app.state.camera_manager
        
        # 导入CameraInfo
        from core.camera_manager import CameraInfo
        
        camera_info = CameraInfo(
            id=camera_data.id,
            name=camera_data.name,
            rtsp_url=camera_data.rtsp_url,
            location=camera_data.location,
            zone_id=camera_data.zone_id,
            enabled_algorithms=camera_data.enabled_algorithms
        )
        
        success = await camera_manager.add_camera(camera_info)
        
        if success:
            return {
                "success": True,
                "message": f"摄像头 {camera_data.name} 添加成功",
                "camera_id": camera_data.id
            }
        else:
            raise HTTPException(status_code=400, detail="摄像头添加失败")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加摄像头失败: {str(e)}")

@router.delete("/cameras/{camera_id}")
async def remove_camera(camera_id: str, request: Request) -> Dict[str, Any]:
    """移除摄像头"""
    try:
        camera_manager = request.app.state.camera_manager
        success = await camera_manager.remove_camera(camera_id)
        
        if success:
            return {
                "success": True,
                "message": f"摄像头 {camera_id} 移除成功"
            }
        else:
            raise HTTPException(status_code=404, detail="摄像头不存在")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除摄像头失败: {str(e)}")

@router.post("/cameras/{camera_id}/start")
async def start_camera_stream(camera_id: str, request: Request) -> Dict[str, Any]:
    """启动摄像头流"""
    try:
        camera_manager = request.app.state.camera_manager
        success = await camera_manager.start_camera_stream(camera_id)
        
        if success:
            return {
                "success": True,
                "message": f"摄像头 {camera_id} 流启动成功"
            }
        else:
            raise HTTPException(status_code=400, detail="启动摄像头流失败")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动摄像头流失败: {str(e)}")

@router.post("/cameras/{camera_id}/stop")
async def stop_camera_stream(camera_id: str, request: Request) -> Dict[str, Any]:
    """停止摄像头流"""
    try:
        camera_manager = request.app.state.camera_manager
        success = await camera_manager.stop_camera_stream(camera_id)
        
        if success:
            return {
                "success": True,
                "message": f"摄像头 {camera_id} 流停止成功"
            }
        else:
            raise HTTPException(status_code=400, detail="停止摄像头流失败")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止摄像头流失败: {str(e)}")

@router.get("/cameras/{camera_id}/stats")
async def get_camera_stats(camera_id: str, request: Request) -> Dict[str, Any]:
    """获取摄像头统计信息"""
    try:
        camera_manager = request.app.state.camera_manager
        stats = await camera_manager.get_camera_stats(camera_id)
        
        if stats:
            return {
                "success": True,
                "camera_id": camera_id,
                "stats": stats
            }
        else:
            raise HTTPException(status_code=404, detail="摄像头不存在")
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/system/stats")
async def get_system_stats(request: Request) -> Dict[str, Any]:
    """获取系统统计信息"""
    try:
        camera_manager = request.app.state.camera_manager
        stats = await camera_manager.get_system_stats()
        
        return {
            "success": True,
            "stats": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统统计失败: {str(e)}")