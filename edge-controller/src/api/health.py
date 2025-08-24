#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
健康检查API
"""

from fastapi import APIRouter, Request
from typing import Dict, Any
from datetime import datetime
from core.gpu_detector import get_gpu_detector

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
        
        # 获取GPU信息
        gpu_detector = get_gpu_detector()
        gpu_info = gpu_detector.get_gpu_info()
        gpu_settings = gpu_detector.get_recommended_settings()
        
        return {
            "status": "healthy",
            "service": "康养AI检测系统 - 边缘控制器",
            "version": "1.0.0",
            "timestamp": datetime.now().isoformat(),
            "components": components,
            "system_stats": stats,
            "management_platform_connection": connection_status,
            "gpu_info": {
                "type": gpu_info["gpu_type"],
                "name": gpu_info["gpu_name"],
                "memory": f"{gpu_info['gpu_memory']}MB" if gpu_info["gpu_memory"] else "Unknown",
                "backend": gpu_info["optimization_backend"],
                "supports": {
                    "metal": gpu_info["supports_metal"],
                    "ml_compute": gpu_info["supports_ml_compute"],
                    "cuda": gpu_info["supports_cuda"],
                    "opencl": gpu_info["supports_opencl"]
                },
                "optimized_settings": {
                    "input_size": gpu_settings["input_size"],
                    "batch_size": gpu_settings["batch_size"],
                    "use_fp16": gpu_settings["use_fp16"],
                    "backends": gpu_settings["detection_backends"]
                }
            }
        }
        
    except Exception as e:
        return {
            "status": "unhealthy",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

@router.get("/gpu-info")
async def get_gpu_info() -> Dict[str, Any]:
    """获取详细的GPU信息"""
    try:
        gpu_detector = get_gpu_detector()
        gpu_info = gpu_detector.get_gpu_info()
        gpu_settings = gpu_detector.get_recommended_settings()
        
        return {
            "success": True,
            "timestamp": datetime.now().isoformat(),
            "hardware": {
                "gpu_type": gpu_info["gpu_type"],
                "gpu_name": gpu_info["gpu_name"],
                "gpu_memory": gpu_info["gpu_memory"],
                "compute_capability": gpu_info["compute_capability"],
                "driver_version": gpu_info["driver_version"]
            },
            "capabilities": {
                "supports_metal": gpu_info["supports_metal"],
                "supports_ml_compute": gpu_info["supports_ml_compute"],
                "supports_cuda": gpu_info["supports_cuda"],
                "supports_opencl": gpu_info["supports_opencl"]
            },
            "optimization": {
                "backend": gpu_info["optimization_backend"],
                "recommended_settings": gpu_settings
            },
            "performance_profile": {
                "optimized_for": gpu_info["gpu_type"],
                "expected_speedup": _get_expected_speedup(gpu_info["gpu_type"]),
                "memory_efficiency": _get_memory_efficiency(gpu_info["gpu_type"])
            }
        }
    except Exception as e:
        return {
            "success": False,
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }

def _get_expected_speedup(gpu_type: str) -> str:
    """获取预期加速比"""
    speedup_map = {
        "apple_m_series": "3-5x vs CPU (Neural Engine优化)",
        "nvidia": "5-10x vs CPU (CUDA/TensorRT优化)",
        "amd": "2-3x vs CPU (OpenCL优化)",
        "intel": "1.5-2x vs CPU (OpenCL优化)",
        "cpu_only": "基准性能",
        "unknown": "未知"
    }
    return speedup_map.get(gpu_type, "未知")

def _get_memory_efficiency(gpu_type: str) -> str:
    """获取内存效率"""
    efficiency_map = {
        "apple_m_series": "高效 (统一内存架构)",
        "nvidia": "高效 (专用显存)",
        "amd": "中等 (专用显存)",
        "intel": "中等 (共享内存)",
        "cpu_only": "基础 (系统内存)",
        "unknown": "未知"
    }
    return efficiency_map.get(gpu_type, "未知")