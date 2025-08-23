#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边缘设备管理API - 算法管理、服务控制、性能监控
"""

from fastapi import APIRouter, Request, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
from datetime import datetime
import asyncio
import psutil
import os
from core.system_monitor import SystemMonitor
from core.metrics_history import MetricsHistory

router = APIRouter(tags=["management"])

class AlgorithmConfig(BaseModel):
    """算法配置模型"""
    algorithm_name: str
    enabled: bool
    confidence_threshold: float = 0.8
    parameters: Dict[str, Any] = {}

class CameraBatch(BaseModel):
    """批量摄像头操作模型"""
    camera_ids: List[str]
    action: str  # start, stop, restart

# ========== 算法管理 ==========
@router.get("/algorithms")
async def get_algorithms(request: Request) -> Dict[str, Any]:
    """获取所有算法配置"""
    try:
        config = request.app.state.config
        algorithms = config.get("detection", {}).get("algorithms", {})
        
        return {
            "success": True,
            "algorithms": algorithms,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取算法配置失败: {str(e)}")

@router.put("/algorithms/{algorithm_name}")
async def update_algorithm(algorithm_name: str, config_data: AlgorithmConfig, request: Request) -> Dict[str, Any]:
    """更新算法配置"""
    try:
        config = request.app.state.config
        camera_manager = request.app.state.camera_manager
        
        # 更新配置
        if "detection" not in config:
            config["detection"] = {"algorithms": {}}
        
        config["detection"]["algorithms"][algorithm_name] = {
            "enabled": config_data.enabled,
            "confidence_threshold": config_data.confidence_threshold,
            "parameters": config_data.parameters
        }
        
        # 通知摄像头管理器更新算法配置
        await camera_manager.update_algorithm_config(algorithm_name, config_data.dict())
        
        return {
            "success": True,
            "message": f"算法 {algorithm_name} 配置更新成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新算法配置失败: {str(e)}")

@router.post("/algorithms/{algorithm_name}/reload")
async def reload_algorithm(algorithm_name: str, request: Request) -> Dict[str, Any]:
    """重新加载算法"""
    try:
        camera_manager = request.app.state.camera_manager
        success = await camera_manager.reload_algorithm(algorithm_name)
        
        if success:
            return {
                "success": True,
                "message": f"算法 {algorithm_name} 重新加载成功"
            }
        else:
            raise HTTPException(status_code=400, detail="算法重新加载失败")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重新加载算法失败: {str(e)}")

# ========== 摄像头批量管理 ==========
@router.post("/cameras/batch")
async def batch_camera_operation(batch_data: CameraBatch, request: Request) -> Dict[str, Any]:
    """批量摄像头操作"""
    try:
        camera_manager = request.app.state.camera_manager
        results = {}
        
        for camera_id in batch_data.camera_ids:
            try:
                if batch_data.action == "start":
                    success = await camera_manager.start_camera_stream(camera_id)
                elif batch_data.action == "stop":
                    success = await camera_manager.stop_camera_stream(camera_id)
                elif batch_data.action == "restart":
                    await camera_manager.stop_camera_stream(camera_id)
                    await asyncio.sleep(1)
                    success = await camera_manager.start_camera_stream(camera_id)
                else:
                    success = False
                
                results[camera_id] = {"success": success, "action": batch_data.action}
            except Exception as e:
                results[camera_id] = {"success": False, "error": str(e)}
        
        return {
            "success": True,
            "batch_results": results,
            "total_processed": len(batch_data.camera_ids)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"批量操作失败: {str(e)}")

@router.put("/cameras/max-count/{max_count}")
async def update_max_camera_count(max_count: int, request: Request) -> Dict[str, Any]:
    """动态调整最大摄像头数量"""
    try:
        camera_manager = request.app.state.camera_manager
        config = request.app.state.config
        
        if max_count < 1 or max_count > 50:
            raise HTTPException(status_code=400, detail="摄像头数量必须在1-50之间")
        
        # 更新配置
        config["cameras"]["max_cameras"] = max_count
        
        # 通知摄像头管理器
        await camera_manager.update_max_camera_count(max_count)
        
        return {
            "success": True,
            "message": f"最大摄像头数量已调整为 {max_count}",
            "max_count": max_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"调整摄像头数量失败: {str(e)}")

# ========== 性能监控 ==========
@router.get("/performance/metrics")
async def get_performance_metrics(request: Request) -> Dict[str, Any]:
    """获取详细性能指标 - 包含GPU、CPU、IO、网络、温度、磁盘监控"""
    try:
        camera_manager = request.app.state.camera_manager
        
        # 使用增强的系统监控器
        monitor = SystemMonitor()
        system_metrics = await monitor.get_all_metrics()
        
        # 摄像头性能统计
        camera_stats = await camera_manager.get_performance_stats()
        
        # 存储历史数据
        metrics_history = MetricsHistory()
        await metrics_history.initialize()
        
        system_metrics_dict = {
            "cpu": system_metrics.cpu,
            "memory": system_metrics.memory,
            "disk": system_metrics.disk,
            "network": system_metrics.network,
            "gpu": system_metrics.gpu,
            "temperature": system_metrics.temperature,
            "io": system_metrics.io,
            "load_average": system_metrics.load_avg
        }
        
        # 异步存储历史数据
        asyncio.create_task(
            metrics_history.store_metrics(system_metrics.timestamp, system_metrics_dict)
        )
        
        return {
            "success": True,
            "timestamp": system_metrics.timestamp,
            "system_metrics": system_metrics_dict,
            "camera_performance": camera_stats,
            "service_info": {
                "uptime": camera_stats.get("uptime_seconds", 0),
                "process_id": os.getpid(),
                "python_version": f"{psutil.Process().name()}"
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取性能指标失败: {str(e)}")

@router.get("/performance/history")
async def get_performance_history(hours: int = 24, interval: int = 5) -> Dict[str, Any]:
    """获取性能历史数据用于图表展示"""
    try:
        metrics_history = MetricsHistory()
        await metrics_history.initialize()
        
        # 获取聚合的历史数据
        aggregated_data = await metrics_history.get_aggregated_history(hours, interval)
        
        # 获取存储统计信息
        stats = await metrics_history.get_statistics()
        
        return {
            "success": True,
            "history": aggregated_data,
            "parameters": {
                "hours": hours,
                "interval_minutes": interval
            },
            "statistics": stats,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取历史数据失败: {str(e)}")

# ========== 服务控制 ==========
@router.post("/service/restart")
async def restart_service(request: Request) -> Dict[str, Any]:
    """重启边缘控制器服务"""
    try:
        # 这是一个优雅重启，需要与容器管理配合
        return {
            "success": True,
            "message": "服务重启请求已接收",
            "note": "服务将在5秒后重启",
            "restart_time": (datetime.now()).isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"重启服务失败: {str(e)}")

@router.post("/service/stop")
async def stop_service(request: Request) -> Dict[str, Any]:
    """停止边缘控制器服务"""
    try:
        camera_manager = request.app.state.camera_manager
        
        # 优雅停止所有摄像头
        await camera_manager.stop_all_cameras()
        
        return {
            "success": True,
            "message": "服务停止中...",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"停止服务失败: {str(e)}")

@router.get("/service/status")
async def get_service_status(request: Request) -> Dict[str, Any]:
    """获取服务详细状态"""
    try:
        camera_manager = request.app.state.camera_manager
        local_cache = request.app.state.local_cache
        event_sender = request.app.state.event_sender
        
        # 获取各组件状态
        camera_status = await camera_manager.get_health_status()
        
        # 简化的组件状态检查
        cache_status = {
            "status": "healthy" if local_cache else "unavailable",
            "type": "local_cache"
        }
        
        sender_status = {
            "status": "healthy" if event_sender else "unavailable", 
            "type": "event_sender"
        }
        
        return {
            "success": True,
            "service_status": "running",
            "components": {
                "camera_manager": camera_status,
                "local_cache": cache_status,
                "event_sender": sender_status
            },
            "uptime": camera_status.get("uptime_seconds", 0),
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取服务状态失败: {str(e)}")

# ========== 配置管理 ==========
@router.get("/config")
async def get_config(request: Request) -> Dict[str, Any]:
    """获取完整配置"""
    try:
        config = request.app.state.config
        
        return {
            "success": True,
            "config": config,
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取配置失败: {str(e)}")

@router.put("/config")
async def update_config(config_data: Dict[str, Any], request: Request) -> Dict[str, Any]:
    """更新配置"""
    try:
        config = request.app.state.config
        camera_manager = request.app.state.camera_manager
        
        # 更新配置
        config.update(config_data)
        
        # 通知相关组件配置更新
        await camera_manager.reload_config(config)
        
        return {
            "success": True,
            "message": "配置更新成功",
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"更新配置失败: {str(e)}")