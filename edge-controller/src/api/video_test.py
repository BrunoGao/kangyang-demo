#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
视频测试API - 用于测试跌倒检测等AI算法
支持上传和处理视频文件
"""

import os
import logging
import asyncio
import uuid
from datetime import datetime
from typing import Dict, Any, List
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, BackgroundTasks
from pydantic import BaseModel

from ai.video_processor import VideoProcessor

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/video", tags=["video-test"])

# 全局变量存储处理状态
processing_tasks = {}
video_results = {}

class VideoProcessRequest(BaseModel):
    """视频处理请求"""
    video_path: str
    algorithms: List[str] = ["fall_detection"]
    config: Dict[str, Any] = {}

class ProcessingStatus(BaseModel):
    """处理状态"""
    task_id: str
    status: str  # pending, processing, completed, failed
    progress: float = 0.0
    message: str = ""

@router.post("/process-local")
async def process_local_video(request: VideoProcessRequest, background_tasks: BackgroundTasks):
    """处理本地视频文件"""
    try:
        # 验证文件存在
        if not os.path.exists(request.video_path):
            raise HTTPException(status_code=404, detail=f"视频文件不存在: {request.video_path}")
        
        # 生成任务ID
        task_id = str(uuid.uuid4())
        
        # 初始化任务状态
        processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="pending",
            message="任务已创建，等待处理"
        )
        
        # 添加后台任务
        background_tasks.add_task(
            _process_video_background,
            task_id,
            request.video_path,
            request.algorithms,
            request.config
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "message": "视频处理任务已启动",
            "status_url": f"/api/video/status/{task_id}",
            "result_url": f"/api/video/result/{task_id}"
        }
        
    except Exception as e:
        logger.error(f"启动视频处理失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/validate")
async def validate_video(video_path: str):
    """验证视频文件"""
    try:
        processor = VideoProcessor()
        result = processor.validate_video_file(video_path)
        
        if result["valid"]:
            return {
                "success": True,
                "video_info": result,
                "message": "视频文件有效"
            }
        else:
            return {
                "success": False,
                "error": result["error"],
                "message": "视频文件无效"
            }
            
    except Exception as e:
        logger.error(f"验证视频文件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/status/{task_id}")
async def get_processing_status(task_id: str):
    """获取处理状态"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    status = processing_tasks[task_id]
    return {
        "success": True,
        "task_id": task_id,
        "status": status.status,
        "progress": status.progress,
        "message": status.message
    }

@router.get("/result/{task_id}")
async def get_processing_result(task_id: str):
    """获取处理结果"""
    if task_id not in processing_tasks:
        raise HTTPException(status_code=404, detail="任务不存在")
    
    status = processing_tasks[task_id]
    
    if status.status != "completed":
        return {
            "success": False,
            "message": f"任务状态: {status.status}",
            "progress": status.progress
        }
    
    if task_id not in video_results:
        raise HTTPException(status_code=404, detail="结果不存在")
    
    result = video_results[task_id]
    return {
        "success": True,
        "task_id": task_id,
        "result": result
    }

@router.get("/test-falldown")
async def test_falldown_video(background_tasks: BackgroundTasks):
    """测试跌倒检测视频"""
    try:
        # 查找跌倒视频文件
        video_paths = [
            "/Users/brunogao/work/codes/kangyang/kangyang-demo/mp4/falldown.mp4",
            "./mp4/falldown.mp4",
            "../mp4/falldown.mp4"
        ]
        
        video_path = None
        for path in video_paths:
            if os.path.exists(path):
                video_path = path
                break
        
        if not video_path:
            raise HTTPException(status_code=404, detail="找不到跌倒测试视频文件")
        
        # 创建处理请求
        request = VideoProcessRequest(
            video_path=video_path,
            algorithms=["fall_detection"],
            config={
                "fall_detection": {
                    "confidence_threshold": 0.7,
                    "min_fall_duration": 2.0,
                    "cooldown_period": 10
                },
                "resize_width": 640,
                "resize_height": 480,
                "skip_frames": 2  # 每3帧处理1帧，提高速度
            }
        )
        
        # 生成任务ID
        task_id = "falldown_test_" + str(uuid.uuid4())[:8]
        
        # 初始化任务状态
        processing_tasks[task_id] = ProcessingStatus(
            task_id=task_id,
            status="pending",
            message="跌倒检测测试任务已创建"
        )
        
        # 添加后台任务
        background_tasks.add_task(
            _process_video_background,
            task_id,
            request.video_path,
            request.algorithms,
            request.config
        )
        
        return {
            "success": True,
            "task_id": task_id,
            "video_path": video_path,
            "message": "跌倒检测测试已启动",
            "status_url": f"/api/video/status/{task_id}",
            "result_url": f"/api/video/result/{task_id}",
            "config": request.config
        }
        
    except Exception as e:
        logger.error(f"启动跌倒检测测试失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/tasks")
async def list_tasks():
    """列出所有任务"""
    tasks = []
    for task_id, status in processing_tasks.items():
        tasks.append({
            "task_id": task_id,
            "status": status.status,
            "progress": status.progress,
            "message": status.message
        })
    
    return {
        "success": True,
        "tasks": tasks,
        "total": len(tasks)
    }

@router.delete("/task/{task_id}")
async def delete_task(task_id: str):
    """删除任务记录"""
    if task_id in processing_tasks:
        del processing_tasks[task_id]
    
    if task_id in video_results:
        del video_results[task_id]
    
    return {
        "success": True,
        "message": f"任务 {task_id} 已删除"
    }

async def _process_video_background(task_id: str, video_path: str, 
                                  algorithms: List[str], config: Dict[str, Any]):
    """后台视频处理任务"""
    try:
        # 更新状态为处理中
        processing_tasks[task_id].status = "processing"
        processing_tasks[task_id].message = "正在处理视频..."
        processing_tasks[task_id].progress = 0.0
        
        logger.info(f"开始处理视频任务 {task_id}: {video_path}")
        
        # 创建视频处理器
        processor = VideoProcessor(config)
        
        # 进度回调函数
        async def progress_callback(progress: float, frame_number: int, detections: List[Dict]):
            processing_tasks[task_id].progress = progress
            processing_tasks[task_id].message = f"处理中... 帧号: {frame_number}, 进度: {progress:.1%}"
            if detections:
                logger.info(f"任务 {task_id} 检测到 {len(detections)} 个事件在帧 {frame_number}")
        
        # 处理视频
        result = await processor.process_video(
            video_path=video_path,
            algorithms=algorithms,
            progress_callback=progress_callback
        )
        
        if result["success"]:
            # 处理成功
            processing_tasks[task_id].status = "completed"
            processing_tasks[task_id].progress = 1.0
            processing_tasks[task_id].message = f"处理完成，检测到 {result['detection_summary']['total_detections']} 个事件"
            
            # 保存结果
            video_results[task_id] = result
            
            logger.info(f"视频任务 {task_id} 处理完成: {result['detection_summary']}")
            
        else:
            # 处理失败
            processing_tasks[task_id].status = "failed"
            processing_tasks[task_id].message = f"处理失败: {result.get('error', '未知错误')}"
            
            logger.error(f"视频任务 {task_id} 处理失败: {result.get('error')}")
        
    except Exception as e:
        logger.error(f"后台处理任务 {task_id} 异常: {e}")
        processing_tasks[task_id].status = "failed"
        processing_tasks[task_id].message = f"处理异常: {str(e)}"