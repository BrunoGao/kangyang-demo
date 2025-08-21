#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检测API路由模块
"""

from fastapi import APIRouter, UploadFile, File, HTTPException
from typing import Dict, Any, List
import tempfile
import os
import time
from datetime import datetime

from ..core.video_processor import video_processor
from ..core.wechat_notifier import get_wechat_notifier, AlertEvent

router = APIRouter(prefix="/api/detection", tags=["detection"])

@router.post("/video/upload")
async def upload_video(video: UploadFile = File(...)):
    """上传视频文件"""
    try:
        if not video.filename:
            raise HTTPException(status_code=400, detail="没有选择文件")
        
        # 检查文件格式
        allowed_extensions = {'.mp4', '.avi', '.mov', '.mkv', '.wmv'}
        file_ext = os.path.splitext(video.filename)[1].lower()
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="不支持的文件格式")
        
        # 保存上传的视频
        temp_dir = tempfile.gettempdir()
        filepath = os.path.join(temp_dir, f"uploaded_{int(time.time())}_{video.filename}")
        
        with open(filepath, 'wb') as f:
            content = await video.read()
            f.write(content)
        
        # 获取视频信息
        video_info = await video_processor._get_video_info(filepath)
        video_info['id'] = f"video_{int(time.time())}"
        video_info['filepath'] = filepath
        video_info['upload_time'] = datetime.now().isoformat()
        video_info['status'] = 'uploaded'
        
        return {
            'success': True,
            'message': f'视频 {video.filename} 上传成功',
            'video_info': video_info
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'上传失败: {str(e)}')

@router.post("/video/process")
async def process_video(config: Dict[Any, Any]):
    """处理视频并进行AI检测"""
    try:
        video_file_path = config.get('video_file_path', '')
        
        if not video_file_path or not os.path.exists(video_file_path):
            raise HTTPException(status_code=400, detail="视频文件不存在")
        
        # 处理视频
        result = await video_processor.process_video_file(video_file_path, config)
        
        if not result['success']:
            raise HTTPException(status_code=500, detail=result.get('error', '处理失败'))
        
        # 检查是否需要发送微信告警
        detection_results = result['detection_results']
        detections = detection_results.get('detections', [])
        
        wechat_notifier = get_wechat_notifier()
        if wechat_notifier and detections:
            for detection in detections:
                # 创建告警事件
                alert_event = AlertEvent(
                    event_type=detection['type'],
                    event_subtype=detection.get('subtype', ''),
                    confidence=detection['confidence'],
                    timestamp=detection['timestamp'],
                    location=config.get('location', '未知位置'),
                    severity=detection.get('severity', 'HIGH'),
                    video_file=video_file_path,
                    frame_number=detection.get('frame_number', 0)
                )
                
                # 发送微信告警
                await wechat_notifier.send_alert(alert_event)
        
        return {'results': result}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'处理失败: {str(e)}')

@router.get("/stats")
async def get_detection_stats():
    """获取检测统计信息"""
    try:
        # 这里可以添加统计信息获取逻辑
        stats = {
            'total_videos_processed': 0,
            'total_detections': 0,
            'detection_types': {
                'fall': 0,
                'fire': 0,
                'smoke': 0
            },
            'last_update': datetime.now().isoformat()
        }
        
        return {
            'success': True,
            'stats': stats
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f'获取统计失败: {str(e)}')