#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
摄像头管理API路由
支持22路摄像头的管理和监控
"""

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from typing import List, Optional, Dict, Any
from datetime import datetime

from ..models.camera import (
    Camera, CameraConfig, CameraListResponse, CameraDetailResponse,
    CameraStatus, CameraType, AlgorithmType, BatchCameraOperation,
    SystemOverview, CameraStats
)
from ..core.camera_manager import camera_manager

router = APIRouter(prefix="/api/camera", tags=["camera"])

@router.get("/overview", response_model=SystemOverview)
async def get_system_overview():
    """获取系统总览信息"""
    try:
        overview = await camera_manager.get_system_overview()
        return overview
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取系统总览失败: {str(e)}")

@router.get("/list", response_model=CameraListResponse)
async def get_camera_list(
    status: Optional[CameraStatus] = Query(None, description="按状态筛选"),
    camera_type: Optional[CameraType] = Query(None, description="按类型筛选"),
    location: Optional[str] = Query(None, description="按位置筛选")
):
    """获取摄像头列表"""
    try:
        cameras = await camera_manager.get_camera_list()
        
        # 应用筛选条件
        if status:
            cameras = [c for c in cameras if c.status == status]
        if camera_type:
            cameras = [c for c in cameras if c.camera_type == camera_type]
        if location:
            cameras = [c for c in cameras if location.lower() in c.location.lower()]
        
        # 统计在线/离线数量
        online_count = sum(1 for c in cameras if c.status == CameraStatus.ONLINE)
        offline_count = len(cameras) - online_count
        
        return CameraListResponse(
            total=len(cameras),
            cameras=cameras,
            online_count=online_count,
            offline_count=offline_count
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取摄像头列表失败: {str(e)}")

@router.post("/add")
async def add_camera(camera: Camera):
    """添加摄像头"""
    try:
        success = await camera_manager.add_camera(camera)
        if success:
            return {"success": True, "message": f"摄像头 {camera.name} 添加成功"}
        else:
            raise HTTPException(status_code=400, detail="添加摄像头失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"添加摄像头失败: {str(e)}")

@router.delete("/{camera_id}")
async def remove_camera(camera_id: str):
    """移除摄像头"""
    try:
        success = await camera_manager.remove_camera(camera_id)
        if success:
            return {"success": True, "message": f"摄像头 {camera_id} 移除成功"}
        else:
            raise HTTPException(status_code=404, detail="摄像头不存在")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"移除摄像头失败: {str(e)}")

@router.get("/{camera_id}", response_model=CameraDetailResponse)
async def get_camera_detail(camera_id: str):
    """获取摄像头详情"""
    try:
        camera = await camera_manager.get_camera_detail(camera_id)
        if not camera:
            raise HTTPException(status_code=404, detail="摄像头不存在")
        
        # 获取统计信息
        stats = await camera_manager.get_camera_stats(camera_id)
        
        # 获取配置信息
        config = camera_manager.camera_configs.get(camera_id)
        
        # 获取流信息
        stream = None
        if camera_id in camera_manager.stream_processors:
            processor = camera_manager.stream_processors[camera_id]
            stream = {
                "camera_id": camera_id,
                "stream_url": processor.rtsp_url,
                "stream_status": "active" if processor.is_running else "inactive",
                "frame_count": processor.frame_count,
                "last_frame_time": processor.last_frame_time.isoformat() if processor.last_frame_time else None
            }
        
        return CameraDetailResponse(
            camera=camera,
            config=config,
            stats=stats,
            stream=stream
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取摄像头详情失败: {str(e)}")

@router.put("/{camera_id}/config")
async def configure_camera(camera_id: str, config: CameraConfig):
    """配置摄像头算法参数"""
    try:
        success = await camera_manager.configure_camera(camera_id, config)
        if success:
            return {"success": True, "message": f"摄像头 {camera_id} 配置成功"}
        else:
            raise HTTPException(status_code=404, detail="摄像头不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"配置摄像头失败: {str(e)}")

@router.post("/{camera_id}/start")
async def start_camera_stream(camera_id: str, background_tasks: BackgroundTasks):
    """启动摄像头视频流"""
    try:
        success = await camera_manager.start_camera_stream(camera_id)
        if success:
            return {"success": True, "message": f"摄像头 {camera_id} 启动成功"}
        else:
            raise HTTPException(status_code=400, detail="启动摄像头失败")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"启动摄像头失败: {str(e)}")

@router.post("/{camera_id}/stop")
async def stop_camera_stream(camera_id: str):
    """停止摄像头视频流"""
    try:
        success = await camera_manager.stop_camera_stream(camera_id)
        if success:
            return {"success": True, "message": f"摄像头 {camera_id} 停止成功"}
        else:
            raise HTTPException(status_code=404, detail="摄像头不存在")
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止摄像头失败: {str(e)}")

@router.post("/batch/operation")
async def batch_camera_operation(operation: BatchCameraOperation):
    """批量摄像头操作"""
    try:
        results = {}
        
        if operation.operation == "start":
            results = await camera_manager.batch_start_cameras(operation.camera_ids)
        elif operation.operation == "stop":
            results = await camera_manager.batch_stop_cameras(operation.camera_ids)
        elif operation.operation == "restart":
            # 先停止再启动
            stop_results = await camera_manager.batch_stop_cameras(operation.camera_ids)
            start_results = await camera_manager.batch_start_cameras(operation.camera_ids)
            results = {
                "stop_results": stop_results,
                "start_results": start_results
            }
        else:
            raise HTTPException(status_code=400, detail="不支持的操作类型")
        
        return {
            "success": True,
            "operation": operation.operation,
            "results": results
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")

@router.get("/{camera_id}/stats", response_model=CameraStats)
async def get_camera_stats(camera_id: str):
    """获取摄像头统计信息"""
    try:
        stats = await camera_manager.get_camera_stats(camera_id)
        if not stats:
            raise HTTPException(status_code=404, detail="摄像头统计信息不存在")
        return stats
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取统计信息失败: {str(e)}")

@router.get("/algorithms/types")
async def get_algorithm_types():
    """获取支持的算法类型"""
    return {
        "algorithm_types": [
            {
                "type": AlgorithmType.FALL_DETECTION,
                "name": "跌倒检测",
                "description": "检测人员跌倒事件"
            },
            {
                "type": AlgorithmType.FIRE_DETECTION,
                "name": "火焰检测", 
                "description": "检测火焰和燃烧现象"
            },
            {
                "type": AlgorithmType.SMOKE_DETECTION,
                "name": "烟雾检测",
                "description": "检测烟雾扩散"
            },
            {
                "type": AlgorithmType.CROWD_DETECTION,
                "name": "拥挤检测",
                "description": "检测人群聚集和拥挤"
            },
            {
                "type": AlgorithmType.WANDERING_DETECTION,
                "name": "徘徊检测",
                "description": "检测异常徘徊行为"
            }
        ]
    }

@router.get("/camera_types/list")
async def get_camera_types():
    """获取摄像头类型列表"""
    return {
        "camera_types": [
            {
                "type": CameraType.INDOOR,
                "name": "室内摄像头",
                "description": "安装在室内环境"
            },
            {
                "type": CameraType.OUTDOOR,
                "name": "室外摄像头",
                "description": "安装在室外环境"
            },
            {
                "type": CameraType.CORRIDOR,
                "name": "走廊摄像头",
                "description": "安装在走廊通道"
            },
            {
                "type": CameraType.ENTRANCE,
                "name": "出入口摄像头",
                "description": "安装在出入口位置"
            }
        ]
    }

@router.post("/demo/init")
async def init_demo_cameras():
    """初始化演示摄像头数据"""
    try:
        demo_cameras = [
            Camera(
                id=f"camera_{i:02d}",
                name=f"摄像头{i:02d}号",
                ip_address=f"192.168.1.{100+i}",
                rtsp_url=f"rtsp://192.168.1.{100+i}:554/stream1",
                location=f"楼层{(i-1)//6+1}-房间{(i-1)%6+1}",
                camera_type=CameraType.INDOOR,
                brand="海康威视",
                model="DS-2CD2185FWD-I",
                enabled_algorithms=[AlgorithmType.FALL_DETECTION, AlgorithmType.FIRE_DETECTION]
            )
            for i in range(1, 23)  # 创建22个演示摄像头
        ]
        
        success_count = 0
        for camera in demo_cameras:
            success = await camera_manager.add_camera(camera)
            if success:
                success_count += 1
        
        return {
            "success": True,
            "message": f"演示数据初始化完成，成功添加 {success_count} 个摄像头"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化演示数据失败: {str(e)}")

@router.get("/stream/{camera_id}/status")
async def get_stream_status(camera_id: str):
    """获取摄像头流状态"""
    try:
        if camera_id not in camera_manager.stream_processors:
            return {
                "camera_id": camera_id,
                "is_running": False,
                "message": "摄像头流未启动"
            }
        
        processor = camera_manager.stream_processors[camera_id]
        return {
            "camera_id": camera_id,
            "is_running": processor.is_running,
            "frame_count": processor.frame_count,
            "detection_count": processor.detection_count,
            "last_frame_time": processor.last_frame_time.isoformat() if processor.last_frame_time else None,
            "rtsp_url": processor.rtsp_url
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取流状态失败: {str(e)}")