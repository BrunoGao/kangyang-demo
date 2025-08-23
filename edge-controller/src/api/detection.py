#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测API路由 - 边缘控制器版本
处理AI检测相关的HTTP请求
"""

import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Request, HTTPException, UploadFile, File, Form
from fastapi.responses import JSONResponse
from datetime import datetime
import json
import base64
import cv2
import numpy as np

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/detection", tags=["AI检测"])

@router.get("/algorithms")
async def get_algorithms(request: Request):
    """获取支持的AI检测算法列表"""
    try:
        config = getattr(request.app.state, 'config', {})
        algorithms = config.get('detection', {}).get('algorithms', {})
        
        result = []
        for algo_name, algo_config in algorithms.items():
            result.append({
                "name": algo_name,
                "display_name": {
                    "fall_detection": "跌倒检测",
                    "fire_detection": "火焰检测", 
                    "smoke_detection": "烟雾检测"
                }.get(algo_name, algo_name),
                "enabled": algo_config.get("enabled", False),
                "confidence_threshold": algo_config.get("confidence_threshold", 0.8),
                "description": {
                    "fall_detection": "基于姿态分析的跌倒检测算法",
                    "fire_detection": "基于颜色和运动特征的火焰检测",
                    "smoke_detection": "基于颜色和纹理特征的烟雾检测"
                }.get(algo_name, "AI检测算法")
            })
        
        return {
            "success": True,
            "data": result,
            "total": len(result),
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取算法列表失败: {e}")
        raise HTTPException(status_code=500, detail="获取算法列表失败")

@router.post("/test/image")
async def test_detection_with_image(
    request: Request,
    file: UploadFile = File(...),
    algorithm: str = Form(...)
):
    """使用上传的图片测试检测算法"""
    try:
        # 验证算法支持
        config = getattr(request.app.state, 'config', {})
        algorithms = config.get('detection', {}).get('algorithms', {})
        
        if algorithm not in algorithms:
            raise HTTPException(status_code=400, detail=f"不支持的算法: {algorithm}")
        
        if not algorithms[algorithm].get("enabled", False):
            raise HTTPException(status_code=400, detail=f"算法未启用: {algorithm}")
        
        # 读取上传的图片
        contents = await file.read()
        nparr = np.frombuffer(contents, np.uint8)
        frame = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if frame is None:
            raise HTTPException(status_code=400, detail="无效的图片格式")
        
        # 获取摄像头管理器
        camera_manager = getattr(request.app.state, 'camera_manager', None)
        if not camera_manager:
            raise HTTPException(status_code=500, detail="摄像头管理器未初始化")
        
        # 执行检测
        detectors = camera_manager.detectors
        results = []
        
        if algorithm == "fall_detection" and "fall_detector" in detectors:
            result = detectors["fall_detector"].detect(frame, datetime.now().timestamp(), 1)
            if result:
                results.append(result)
        
        elif algorithm == "fire_detection" and "fire_detector" in detectors:
            fire_results = detectors["fire_detector"].detect_fire_smoke(frame)
            results.extend(fire_results)
        
        elif algorithm == "smoke_detection" and "smoke_detector" in detectors:
            smoke_results = detectors["smoke_detector"].detect_fire_smoke(frame)
            results.extend(smoke_results)
        
        # 处理检测结果
        response_data = {
            "algorithm": algorithm,
            "image_info": {
                "filename": file.filename,
                "size": f"{frame.shape[1]}x{frame.shape[0]}",
                "channels": frame.shape[2] if len(frame.shape) > 2 else 1
            },
            "detection_results": results,
            "detected": len(results) > 0,
            "timestamp": datetime.now().isoformat()
        }
        
        # 如果有检测结果，添加详细信息
        if results:
            response_data["summary"] = {
                "total_detections": len(results),
                "max_confidence": max(r.get("confidence", 0) for r in results),
                "detected_types": list(set(r.get("type", "unknown") for r in results))
            }
        
        return {
            "success": True,
            "data": response_data,
            "message": f"检测完成，发现 {len(results)} 个检测结果" if results else "检测完成，未发现异常"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"图片检测失败: {e}")
        raise HTTPException(status_code=500, detail=f"检测处理失败: {str(e)}")

@router.get("/stats")
async def get_detection_stats(request: Request):
    """获取检测统计信息"""
    try:
        camera_manager = getattr(request.app.state, 'camera_manager', None)
        if not camera_manager:
            raise HTTPException(status_code=500, detail="摄像头管理器未初始化")
        
        stats = {}
        detectors = camera_manager.detectors
        
        # 获取各检测器的统计信息
        for detector_name, detector in detectors.items():
            if hasattr(detector, 'get_stats'):
                stats[detector_name] = detector.get_stats()
        
        # 添加系统统计
        stats["system"] = {
            "active_cameras": len(camera_manager.active_streams),
            "total_detectors": len(detectors),
            "uptime_seconds": camera_manager.get_uptime(),
            "last_update": datetime.now().isoformat()
        }
        
        return {
            "success": True,
            "data": stats,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取统计信息失败: {e}")
        raise HTTPException(status_code=500, detail="获取统计信息失败")

@router.post("/config/update")
async def update_detection_config(
    request: Request,
    algorithm: str,
    config_data: Dict[str, Any]
):
    """更新检测算法配置"""
    try:
        # 验证算法存在
        app_config = getattr(request.app.state, 'config', {})
        algorithms = app_config.get('detection', {}).get('algorithms', {})
        
        if algorithm not in algorithms:
            raise HTTPException(status_code=400, detail=f"不支持的算法: {algorithm}")
        
        # 更新配置
        algorithms[algorithm].update(config_data)
        
        # 重新初始化对应的检测器（如果需要）
        camera_manager = getattr(request.app.state, 'camera_manager', None)
        if camera_manager:
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
        logger.error(f"更新配置失败: {e}")
        raise HTTPException(status_code=500, detail="配置更新失败")

@router.post("/test/video")
async def test_detection_with_video(
    request: Request,
    file: UploadFile = File(...),
    algorithms: str = Form(default="fall_detection,fire_detection,smoke_detection")
):
    """使用上传的视频测试检测算法"""
    try:
        import tempfile
        import os
        
        # 验证文件格式
        if not file.filename.lower().endswith(('.mp4', '.avi', '.mov', '.mkv', '.webm')):
            raise HTTPException(status_code=400, detail="不支持的视频格式")
        
        # 解析要使用的算法
        algorithm_list = [alg.strip() for alg in algorithms.split(',')]
        
        # 验证算法支持
        config = getattr(request.app.state, 'config', {})
        available_algorithms = config.get('detection', {}).get('algorithms', {})
        
        enabled_algorithms = []
        for algorithm in algorithm_list:
            if algorithm in available_algorithms and available_algorithms[algorithm].get("enabled", False):
                enabled_algorithms.append(algorithm)
        
        if not enabled_algorithms:
            raise HTTPException(status_code=400, detail="没有可用的检测算法")
        
        # 保存上传的视频文件到临时目录
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            contents = await file.read()
            temp_file.write(contents)
            temp_video_path = temp_file.name
        
        try:
            # 使用OpenCV打开视频
            cap = cv2.VideoCapture(temp_video_path)
            if not cap.isOpened():
                raise HTTPException(status_code=400, detail="无法打开视频文件")
            
            # 获取视频信息
            fps = cap.get(cv2.CAP_PROP_FPS)
            frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
            duration = frame_count / fps if fps > 0 else 0
            
            # 获取检测器
            camera_manager = getattr(request.app.state, 'camera_manager', None)
            if not camera_manager:
                raise HTTPException(status_code=500, detail="摄像头管理器未初始化")
            
            detectors = camera_manager.detectors
            all_results = []
            frame_results = {}
            
            # 处理视频帧
            frame_idx = 0
            processed_frames = 0
            # 每秒处理2帧以提高速度
            frame_skip = max(1, int(fps / 2)) if fps > 0 else 1
            
            while True:
                ret, frame = cap.read()
                if not ret:
                    break
                
                # 跳帧处理
                if frame_idx % frame_skip != 0:
                    frame_idx += 1
                    continue
                
                timestamp = frame_idx / fps if fps > 0 else frame_idx
                current_frame_results = []
                
                # 执行各种检测算法
                for algorithm in enabled_algorithms:
                    try:
                        if algorithm == "fall_detection" and "fall_detector" in detectors:
                            result = detectors["fall_detector"].detect(frame, timestamp, frame_idx)
                            if result:
                                result["algorithm"] = "fall_detection"
                                result["frame_index"] = frame_idx
                                result["timestamp"] = timestamp
                                current_frame_results.append(result)
                        
                        elif algorithm == "fire_detection" and "fire_detector" in detectors:
                            fire_results = detectors["fire_detector"].detect_fire_smoke(frame)
                            for result in fire_results:
                                if result.get("type") == "fire":
                                    result["algorithm"] = "fire_detection"
                                    result["frame_index"] = frame_idx
                                    result["timestamp"] = timestamp
                                    current_frame_results.append(result)
                        
                        elif algorithm == "smoke_detection" and "smoke_detector" in detectors:
                            smoke_results = detectors["smoke_detector"].detect_fire_smoke(frame)
                            for result in smoke_results:
                                if result.get("type") == "smoke":
                                    result["algorithm"] = "smoke_detection"
                                    result["frame_index"] = frame_idx
                                    result["timestamp"] = timestamp
                                    current_frame_results.append(result)
                    
                    except Exception as e:
                        logger.warning(f"检测算法 {algorithm} 在帧 {frame_idx} 处理失败: {e}")
                
                if current_frame_results:
                    frame_results[frame_idx] = current_frame_results
                    all_results.extend(current_frame_results)
                
                processed_frames += 1
                frame_idx += 1
                
                # 限制处理的最大帧数，避免处理过长的视频
                if processed_frames >= 300:  # 最多处理300帧
                    logger.info(f"达到最大处理帧数限制，停止处理")
                    break
            
            cap.release()
            
            # 生成分析报告
            analysis_report = {
                "video_info": {
                    "filename": file.filename,
                    "duration": duration,
                    "fps": fps,
                    "total_frames": frame_count,
                    "processed_frames": processed_frames,
                    "frame_skip": frame_skip
                },
                "algorithms_used": enabled_algorithms,
                "detection_summary": {
                    "total_detections": len(all_results),
                    "frames_with_detections": len(frame_results),
                    "detection_rate": len(frame_results) / processed_frames if processed_frames > 0 else 0
                },
                "detailed_results": all_results,
                "frame_results": frame_results,
                "processing_time": datetime.now().isoformat()
            }
            
            # 按算法分类统计
            algorithm_stats = {}
            for algorithm in enabled_algorithms:
                algo_results = [r for r in all_results if r.get("algorithm") == algorithm]
                algorithm_stats[algorithm] = {
                    "total_detections": len(algo_results),
                    "avg_confidence": sum(r.get("confidence", 0) for r in algo_results) / len(algo_results) if algo_results else 0,
                    "max_confidence": max(r.get("confidence", 0) for r in algo_results) if algo_results else 0,
                    "detection_frames": list(set(r.get("frame_index", 0) for r in algo_results))
                }
            
            analysis_report["algorithm_statistics"] = algorithm_stats
            
            return {
                "success": True,
                "data": analysis_report,
                "message": f"视频分析完成，处理了 {processed_frames} 帧，发现 {len(all_results)} 个检测结果"
            }
        
        finally:
            # 清理临时文件
            try:
                os.unlink(temp_video_path)
            except:
                pass
                
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"视频分析失败: {e}")
        raise HTTPException(status_code=500, detail=f"视频分析失败: {str(e)}")

@router.get("/history")
async def get_detection_history(
    request: Request,
    limit: int = 100,
    algorithm: Optional[str] = None
):
    """获取检测历史记录"""
    try:
        local_cache = getattr(request.app.state, 'local_cache', None)
        if not local_cache:
            raise HTTPException(status_code=500, detail="本地缓存未初始化")
        
        # 从缓存中获取历史记录
        history = await local_cache.get_detection_history(limit, algorithm)
        
        return {
            "success": True,
            "data": history,
            "total": len(history),
            "filter": {"algorithm": algorithm} if algorithm else None,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"获取历史记录失败: {e}")
        raise HTTPException(status_code=500, detail="获取历史记录失败")