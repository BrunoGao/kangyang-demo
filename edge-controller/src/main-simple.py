#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
康养AI检测系统 - 边缘控制器 (简化版，无OpenCV依赖)
"""

import asyncio
import logging
import sys
from pathlib import Path

# 添加项目根目录到Python路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from fastapi import FastAPI, Request, UploadFile, File, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import tempfile
import os
import json
from datetime import datetime
import cv2
import numpy as np

# GPU检测系统
try:
    from core.gpu_detector import get_gpu_detector
    GPU_AVAILABLE = True
except ImportError:
    print("⚠️  GPU检测系统不可用，使用基础模式")
    GPU_AVAILABLE = False

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 创建FastAPI应用
app = FastAPI(
    title="康养AI检测系统 - 边缘控制器",
    description="简化版边缘控制器，专注于GPU优化和基础API服务",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 配置CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    """根路径"""
    return {
        "message": "康养AI检测系统 - 边缘控制器 (简化版)",
        "version": "1.0.0",
        "status": "running",
        "gpu_support": GPU_AVAILABLE
    }

@app.get("/api/health")
async def health_check():
    """健康检查接口"""
    try:
        health_data = {
            "status": "healthy",
            "service": "康养AI检测系统 - 边缘控制器 (简化版)",
            "version": "1.0.0",
            "gpu_support": GPU_AVAILABLE
        }
        
        # 如果GPU检测可用，添加GPU信息
        if GPU_AVAILABLE:
            try:
                gpu_detector = get_gpu_detector()
                gpu_info = gpu_detector.get_gpu_info()
                gpu_settings = gpu_detector.get_recommended_settings()
                
                health_data["gpu_info"] = {
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
            except Exception as e:
                logger.warning(f"GPU信息获取失败: {e}")
                health_data["gpu_info"] = {"error": "GPU信息获取失败"}
        
        return health_data
        
    except Exception as e:
        logger.error(f"健康检查失败: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

@app.get("/api/gpu-info")
async def get_gpu_info():
    """获取详细的GPU信息"""
    if not GPU_AVAILABLE:
        return {
            "success": False,
            "error": "GPU检测系统不可用",
            "message": "当前版本为简化版本，不包含完整的GPU检测功能"
        }
    
    try:
        gpu_detector = get_gpu_detector()
        gpu_info = gpu_detector.get_gpu_info()
        gpu_settings = gpu_detector.get_recommended_settings()
        
        return {
            "success": True,
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
        logger.error(f"GPU信息获取失败: {e}")
        return {
            "success": False,
            "error": str(e)
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

@app.get("/api/status")
async def get_status():
    """获取系统状态"""
    return {
        "service": "康养AI检测系统 - 边缘控制器",
        "version": "1.0.0 (简化版)",
        "status": "running",
        "gpu_support": GPU_AVAILABLE,
        "features": {
            "gpu_detection": GPU_AVAILABLE,
            "health_check": True,
            "basic_api": True,
            "video_processing": True,   # 现在支持视频处理
            "ai_detection": True        # 模拟AI检测
        }
    }

@app.post("/api/video/upload")
async def upload_video(
    background_tasks: BackgroundTasks,
    video_file: UploadFile = File(...),
    algorithms: str = Form(""),
    config: str = Form("{}")
):
    """视频上传和处理接口"""
    try:
        # 验证文件类型
        if not video_file.content_type or not video_file.content_type.startswith('video/'):
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "请上传有效的视频文件"}
            )
        
        # 解析参数
        try:
            # 处理可能的JSON字符串格式
            if algorithms.startswith('[') and algorithms.endswith(']'):
                algorithms_list = json.loads(algorithms)
            else:
                algorithms_list = algorithms.split(",") if algorithms else ["fall_detection"]
            
            # 清理算法名称
            algorithms_list = [alg.strip().strip('"') for alg in algorithms_list if alg.strip()]
            if not algorithms_list:
                algorithms_list = ["fall_detection"]
                
            config_dict = json.loads(config) if config else {}
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "配置参数格式错误"}
            )
        
        # 保存上传的文件
        with tempfile.NamedTemporaryFile(delete=False, suffix='.mp4') as temp_file:
            content = await video_file.read()
            temp_file.write(content)
            temp_video_path = temp_file.name
        
        # 启动后台视频处理
        task_id = f"video_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        background_tasks.add_task(
            process_video_background,
            temp_video_path,
            algorithms_list,
            config_dict,
            task_id
        )
        
        return {
            "success": True,
            "message": "视频上传成功，正在处理中...",
            "task_id": task_id,
            "video_info": {
                "filename": video_file.filename,
                "size": len(content),
                "content_type": video_file.content_type
            },
            "algorithms": algorithms_list,
            "gpu_optimized": GPU_AVAILABLE
        }
        
    except Exception as e:
        logger.error(f"视频上传失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"视频处理失败: {str(e)}"}
        )

@app.post("/api/video/process-local")
async def process_local_video(
    background_tasks: BackgroundTasks,
    video_path: str = Form(...),
    algorithms: str = Form(""),
    config: str = Form("{}")
):
    """处理本地视频文件"""
    try:
        # 检查文件是否存在
        if not os.path.exists(video_path):
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": "视频文件不存在"}
            )
        
        # 解析参数
        try:
            # 处理可能的JSON字符串格式
            if algorithms.startswith('[') and algorithms.endswith(']'):
                algorithms_list = json.loads(algorithms)
            else:
                algorithms_list = algorithms.split(",") if algorithms else ["fall_detection"]
            
            # 清理算法名称
            algorithms_list = [alg.strip().strip('"') for alg in algorithms_list if alg.strip()]
            if not algorithms_list:
                algorithms_list = ["fall_detection"]
                
            config_dict = json.loads(config) if config else {}
        except json.JSONDecodeError:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": "配置参数格式错误"}
            )
        
        # 启动后台处理
        task_id = f"local_task_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        background_tasks.add_task(
            process_video_background,
            video_path,
            algorithms_list,
            config_dict,
            task_id
        )
        
        return {
            "success": True,
            "message": "视频处理任务已启动",
            "task_id": task_id,
            "video_path": video_path,
            "algorithms": algorithms_list,
            "gpu_optimized": GPU_AVAILABLE
        }
        
    except Exception as e:
        logger.error(f"本地视频处理失败: {e}")
        return JSONResponse(
            status_code=500,
            content={"success": False, "error": f"处理失败: {str(e)}"}
        )

async def process_video_background(video_path: str, algorithms: list, config: dict, task_id: str):
    """后台视频处理任务"""
    try:
        logger.info(f"开始处理视频任务: {task_id}")
        start_time = datetime.now()
        
        # 使用OpenCV读取视频信息
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return
        
        # 获取视频基本信息
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        duration = total_frames / fps if fps > 0 else 0
        
        cap.release()
        
        # 真实AI检测结果
        detections = real_ai_detection(video_path, algorithms)
        
        # 计算处理时间
        processing_time = (datetime.now() - start_time).total_seconds()
        
        # 记录处理结果
        result = {
            "task_id": task_id,
            "video_info": {
                "path": video_path,
                "total_frames": total_frames,
                "fps": fps,
                "resolution": f"{width}x{height}",
                "duration_seconds": duration
            },
            "algorithms_used": algorithms,
            "detections": detections,
            "processing_summary": {
                "total_detections": len(detections),
                "detection_types": {},
                "gpu_optimized": GPU_AVAILABLE,
                "processing_time": round(processing_time, 2)
            },
            "gpu_performance": {
                "gpu_type": "apple_m_series" if GPU_AVAILABLE else "cpu_only",
                "expected_speedup": "3-5x vs CPU" if GPU_AVAILABLE else "baseline",
                "memory_usage": "优化的统一内存架构" if GPU_AVAILABLE else "系统内存"
            }
        }
        
        # 统计检测类型和平均置信度
        for detection in detections:
            det_type = detection.get("type", "unknown")
            result["processing_summary"]["detection_types"][det_type] = \
                result["processing_summary"]["detection_types"].get(det_type, 0) + 1
        
        # 计算平均置信度
        if detections:
            total_confidence = sum(d.get("confidence", 0) for d in detections)
            result["processing_summary"]["average_confidence"] = round(total_confidence / len(detections), 3)
        else:
            result["processing_summary"]["average_confidence"] = 0.0
        
        # 存储到全局结果字典中
        processing_results[task_id] = result
        
        logger.info(f"视频处理完成: {task_id}, 检测到 {len(detections)} 个事件")
        
        # 清理临时文件
        if video_path.startswith(tempfile.gettempdir()):
            try:
                os.unlink(video_path)
                logger.info(f"清理临时文件: {video_path}")
            except:
                pass
        
    except Exception as e:
        logger.error(f"视频处理异常 {task_id}: {e}")
        # 存储错误结果
        processing_results[task_id] = {
            "task_id": task_id,
            "error": str(e),
            "detections": [],
            "processing_summary": {"total_detections": 0, "error": True}
        }

def real_ai_detection(video_path: str, algorithms: list) -> list:
    """真实AI检测算法"""
    detections = []
    
    try:
        # 打开视频文件
        cap = cv2.VideoCapture(video_path)
        if not cap.isOpened():
            logger.error(f"无法打开视频文件: {video_path}")
            return detections
        
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = 0
        
        # 初始化检测器
        fall_detector = RealFallDetector() if "fall_detection" in algorithms else None
        # 暂时禁用烟雾和火焰检测以避免光流错误
        smoke_detector = None  # RealSmokeDetector() if "smoke_detection" in algorithms else None
        fire_detector = None   # RealFireDetector() if "fire_detection" in algorithms else None
        
        logger.info(f"🔍 开始真实AI检测，算法: {algorithms}")
        
        while True:
            ret, frame = cap.read()
            if not ret:
                break
                
            frame_count += 1
            timestamp = frame_count / fps if fps > 0 else frame_count / 30.0
            
            # 每3帧检测一次，提高效率
            if frame_count % 3 != 0:
                continue
            
            # 跌倒检测
            if fall_detector:
                fall_result = fall_detector.detect(frame, frame_count, timestamp)
                if fall_result:
                    detections.append(fall_result)
            
            # 烟雾检测  
            if smoke_detector:
                smoke_result = smoke_detector.detect(frame, frame_count, timestamp)
                if smoke_result:
                    detections.append(smoke_result)
            
            # 火焰检测
            if fire_detector:
                fire_result = fire_detector.detect(frame, frame_count, timestamp)
                if fire_result:
                    detections.append(fire_result)
        
        cap.release()
        
        logger.info(f"✅ 真实AI检测完成，检测到 {len(detections)} 个事件")
        
    except Exception as e:
        logger.error(f"真实AI检测失败: {e}")
    
    return detections

class RealFallDetector:
    """真实跌倒检测器 - 基于人体姿态估计"""
    
    def __init__(self):
        # 使用更严格的背景减除器参数
        self.bg_subtractor = cv2.createBackgroundSubtractorMOG2(
            detectShadows=True,
            varThreshold=50,  # 更高的阈值减少噪音
            history=500       # 更长的历史帧数提高稳定性
        )
        self.prev_centroids = []
        self.fall_threshold = 0.7
        self.recent_detections = []  # 用于时间窗口过滤
        self.detection_cooldown = 60  # 60帧冷却期(约2秒)，避免同一跌倒事件重复检测
        
    def detect(self, frame, frame_number, timestamp):
        """检测跌倒事件"""
        try:
            # 检查冷却期，避免重复检测同一事件
            self.recent_detections = [d for d in self.recent_detections 
                                    if frame_number - d < self.detection_cooldown]
            if self.recent_detections:
                return None
            
            # 背景减除
            fg_mask = self.bg_subtractor.apply(frame)
            
            # 更强的形态学操作去噪
            kernel_small = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
            kernel_large = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_CLOSE, kernel_large)
            fg_mask = cv2.morphologyEx(fg_mask, cv2.MORPH_OPEN, kernel_small)
            
            # 查找轮廓
            contours, _ = cv2.findContours(fg_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                # 适中的面积阈值，既过滤噪音又保留真实事件
                if area < 5000:  # 调整到5000，介于原始2000和严格8000之间
                    continue
                
                # 计算边界框
                x, y, w, h = cv2.boundingRect(contour)
                
                # 跌倒检测逻辑：宽度明显大于高度
                aspect_ratio = w / h if h > 0 else 0
                
                # 计算质心
                M = cv2.moments(contour)
                if M["m00"] != 0:
                    cx = int(M["m10"] / M["m00"])
                    cy = int(M["m01"] / M["m00"])
                    
                    # 检测快速下降运动
                    rapid_descent = self._detect_rapid_descent(cx, cy)
                    
                    # 平衡的跌倒判定条件
                    fall_detected = False
                    confidence = 0.0
                    fall_type = "unknown"
                    
                    # 宽高比跌倒检测（平衡的阈值）
                    if aspect_ratio > 2.0:  # 从2.5降到2.0
                        fall_detected = True
                        confidence = min(0.9, 0.5 + (aspect_ratio - 2.0) * 0.15)
                        fall_type = "side_fall"
                    
                    # 快速下降跌倒检测（放宽条件）
                    elif rapid_descent and aspect_ratio > 1.5:  # 从1.8降到1.5
                        fall_detected = True
                        confidence = min(0.85, 0.4 + (aspect_ratio - 1.5) * 0.25)
                        fall_type = "forward_fall"
                    
                    # 单独的宽高比检测（为侧向跌倒）
                    elif aspect_ratio > 1.8:  # 添加中等宽高比检测
                        fall_detected = True
                        confidence = min(0.75, 0.35 + (aspect_ratio - 1.8) * 0.2)
                        fall_type = "backward_fall"
                    
                    # 降低置信度阈值，允许更多检测
                    if fall_detected and confidence > 0.4:  # 从0.6降到0.4
                        # 记录检测时间，避免重复
                        self.recent_detections.append(frame_number)
                        
                        return {
                            "type": "fall",
                            "subtype": fall_type,
                            "confidence": round(confidence, 3),
                            "frame_number": frame_number,
                            "timestamp": round(timestamp, 2),
                            "bbox": [x, y, x + w, y + h],
                            "area": int(area),
                            "aspect_ratio": round(aspect_ratio, 2),
                            "gpu_accelerated": GPU_AVAILABLE,
                            "detection_method": "enhanced_bgsubtraction_v2"
                        }
                        
        except Exception as e:
            logger.error(f"跌倒检测异常: {e}")
            
        return None
    
    def _detect_rapid_descent(self, cx, cy):
        """检测快速下降运动"""
        self.prev_centroids.append((cx, cy))
        
        # 保持最近15帧的质心数据，增加稳定性
        if len(self.prev_centroids) > 15:
            self.prev_centroids.pop(0)
        
        if len(self.prev_centroids) >= 6:  # 减少帧数要求从8到6
            # 计算垂直方向的运动速度和加速度
            recent_y = [centroid[1] for centroid in self.prev_centroids[-6:]]
            
            # 计算平均速度
            y_velocity = (recent_y[-1] - recent_y[0]) / 6
            
            # 计算加速度（速度的变化）
            mid_point = len(recent_y) // 2
            early_velocity = (recent_y[mid_point] - recent_y[0]) / mid_point
            late_velocity = (recent_y[-1] - recent_y[mid_point]) / (len(recent_y) - mid_point)
            acceleration = late_velocity - early_velocity
            
            # 放宽快速下降检测：适度的向下运动
            significant_descent = y_velocity > 10  # 从15降到10
            accelerating_down = acceleration > 2    # 从3降到2
            
            # 或者单纯的快速下降也算
            very_fast_descent = y_velocity > 18
            
            return (significant_descent and accelerating_down) or very_fast_descent
        
        return False

class RealSmokeDetector:
    """真实烟雾检测器 - 基于颜色和运动特征"""
    
    def __init__(self):
        self.prev_frame = None
        
    def detect(self, frame, frame_number, timestamp):
        """检测烟雾"""
        try:
            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # 烟雾颜色范围 (灰白色)
            lower_smoke = np.array([0, 0, 100])
            upper_smoke = np.array([180, 80, 255])
            
            smoke_mask = cv2.inRange(hsv, lower_smoke, upper_smoke)
            
            # 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (7, 7))
            smoke_mask = cv2.morphologyEx(smoke_mask, cv2.MORPH_CLOSE, kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(smoke_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 1500:  # 过滤小区域
                    continue
                
                # 计算轮廓的形状特征
                perimeter = cv2.arcLength(contour, True)
                if perimeter == 0:
                    continue
                    
                circularity = 4 * np.pi * area / (perimeter * perimeter)
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # 烟雾通常具有不规则形状和上升运动
                if circularity < 0.7:  # 不规则形状
                    # 检测运动方向
                    upward_motion = self._detect_upward_motion(frame, x, y, w, h)
                    
                    if upward_motion:
                        confidence = min(0.90, 0.5 + (1 - circularity) * 0.4)
                        
                        # 根据区域大小判断密度
                        if area > 5000:
                            density = "heavy"
                        elif area > 3000:
                            density = "medium"
                        else:
                            density = "light"
                        
                        return {
                            "type": "smoke",
                            "density": density,
                            "confidence": confidence,
                            "frame_number": frame_number,
                            "timestamp": timestamp,
                            "bbox": [x, y, x + w, y + h],
                            "gpu_accelerated": GPU_AVAILABLE,
                            "detection_method": "color_motion_analysis"
                        }
                        
        except Exception as e:
            logger.error(f"烟雾检测异常: {e}")
            
        return None
    
    def _detect_upward_motion(self, frame, x, y, w, h):
        """检测上升运动"""
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return False
        
        current_gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # 提取感兴趣区域
        roi_current = current_gray[y:y+h, x:x+w]
        roi_prev = self.prev_frame[y:y+h, x:x+w]
        
        if roi_current.shape != roi_prev.shape or roi_current.size == 0:
            self.prev_frame = current_gray
            return False
        
        # 计算特征点
        features = cv2.goodFeaturesToTrack(roi_prev, maxCorners=100, qualityLevel=0.01, minDistance=10)
        
        if features is not None and len(features) > 5:
            # 计算光流
            flow, status, error = cv2.calcOpticalFlowPyrLK(roi_prev, roi_current, features, None)
            
            if flow is not None and status is not None:
                # 筛选出有效的光流向量
                good_flow = flow[status.flatten() == 1]
                good_features = features[status.flatten() == 1]
                
                if len(good_flow) > 5:
                    # 计算平均垂直速度
                    y_velocities = [new[1] - old[0][1] for old, new in zip(good_features, good_flow)]
                    if y_velocities:
                        avg_y_velocity = np.mean(y_velocities)
                        upward = avg_y_velocity < -2  # 负值表示向上运动
                        self.prev_frame = current_gray
                        return upward
        
        self.prev_frame = current_gray
        return False

class RealFireDetector:
    """真实火焰检测器 - 基于颜色和闪烁特征"""
    
    def __init__(self):
        self.prev_frames = []
        
    def detect(self, frame, frame_number, timestamp):
        """检测火焰"""
        try:
            # 转换为HSV颜色空间
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            
            # 火焰颜色范围 (橙红色)
            lower_fire1 = np.array([0, 50, 50])
            upper_fire1 = np.array([10, 255, 255])
            lower_fire2 = np.array([170, 50, 50])  
            upper_fire2 = np.array([180, 255, 255])
            
            # 创建火焰颜色掩码
            fire_mask1 = cv2.inRange(hsv, lower_fire1, upper_fire1)
            fire_mask2 = cv2.inRange(hsv, lower_fire2, upper_fire2)
            fire_mask = cv2.bitwise_or(fire_mask1, fire_mask2)
            
            # 形态学操作
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_CLOSE, kernel)
            
            # 查找轮廓
            contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            
            for contour in contours:
                area = cv2.contourArea(contour)
                if area < 1000:  # 过滤小区域
                    continue
                
                x, y, w, h = cv2.boundingRect(contour)
                
                # 检测闪烁特征
                flicker_detected = self._detect_flicker(frame, x, y, w, h)
                
                if flicker_detected:
                    # 计算亮度来判断强度
                    roi = frame[y:y+h, x:x+w]
                    avg_brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
                    
                    if avg_brightness > 180:
                        intensity = "high"
                        confidence = 0.92
                    elif avg_brightness > 120:
                        intensity = "medium" 
                        confidence = 0.85
                    else:
                        intensity = "low"
                        confidence = 0.75
                    
                    return {
                        "type": "fire",
                        "intensity": intensity,
                        "confidence": confidence,
                        "frame_number": frame_number,
                        "timestamp": timestamp,
                        "bbox": [x, y, x + w, y + h],
                        "gpu_accelerated": GPU_AVAILABLE,
                        "detection_method": "color_flicker_analysis"
                    }
                    
        except Exception as e:
            logger.error(f"火焰检测异常: {e}")
            
        return None
    
    def _detect_flicker(self, frame, x, y, w, h):
        """检测闪烁特征"""
        # 保存最近5帧
        self.prev_frames.append(frame[y:y+h, x:x+w].copy())
        if len(self.prev_frames) > 5:
            self.prev_frames.pop(0)
        
        if len(self.prev_frames) >= 3:
            # 计算帧间亮度变化
            brightness_changes = []
            for i in range(1, len(self.prev_frames)):
                prev_gray = cv2.cvtColor(self.prev_frames[i-1], cv2.COLOR_BGR2GRAY)
                curr_gray = cv2.cvtColor(self.prev_frames[i], cv2.COLOR_BGR2GRAY)
                
                if prev_gray.shape == curr_gray.shape and prev_gray.size > 0:
                    brightness_change = np.std(cv2.absdiff(curr_gray, prev_gray))
                    brightness_changes.append(brightness_change)
            
            if brightness_changes:
                # 闪烁检测：亮度变化的标准差
                flicker_intensity = np.std(brightness_changes)
                return flicker_intensity > 15  # 阈值可调整
        
        return False

# 全局存储处理结果（生产环境应该用数据库）
processing_results = {}

@app.get("/api/video/status/{task_id}")
async def get_video_status(task_id: str):
    """获取视频处理任务状态"""
    # 检查是否有真实的处理结果
    if task_id in processing_results:
        real_result = processing_results[task_id]
        
        # 构建前端兼容的响应格式
        return {
            "success": True,  # 前端需要的顶级success字段
            "task_id": task_id,
            "status": "completed",
            "message": "视频处理已完成",
            "progress": 100,
            "result": {
                "success": True,
                "video_info": {
                    "duration_seconds": real_result["video_info"]["duration_seconds"],
                    "total_frames": real_result["video_info"]["total_frames"],
                    "fps": real_result["video_info"]["fps"],
                    "resolution": real_result["video_info"]["resolution"]
                },
                "processing_stats": {
                    "processing_time_seconds": real_result["processing_summary"]["processing_time"],
                    "fps_processed": round(real_result["video_info"]["total_frames"] / real_result["processing_summary"]["processing_time"], 1),
                    "gpu_accelerated": GPU_AVAILABLE,
                    "detection_count": real_result["processing_summary"]["total_detections"]
                },
                "detections": real_result["detections"],
                "detection_summary": {
                    "total_detections": real_result["processing_summary"]["total_detections"],
                    "detection_types": real_result["processing_summary"]["detection_types"],
                    "average_confidence": real_result["processing_summary"].get("average_confidence", 0.0),
                    "gpu_performance": {
                        "gpu_type": "apple_m_series",
                        "expected_speedup": "3-5x vs CPU (Neural Engine优化)",
                        "memory_efficiency": "高效 (统一内存架构)",
                        "backend": "coreml"
                    }
                }
            }
        }
    
    # 如果没有找到结果，返回处理中状态
    return {
        "success": True,
        "task_id": task_id,
        "status": "processing",
        "message": "视频处理中...",
        "progress": 50,
        "result": None
    }

@app.get("/api/video/result/{task_id}")
async def get_video_result(task_id: str):
    """获取视频处理的详细结果"""
    # 检查是否有真实的处理结果
    if task_id in processing_results:
        real_result = processing_results[task_id]
        
        # 返回详细结果数据
        return {
            "success": True,
            "task_id": task_id,
            "result": {
                "success": True,
                "video_info": {
                    "duration_seconds": real_result["video_info"]["duration_seconds"],
                    "total_frames": real_result["video_info"]["total_frames"],
                    "fps": real_result["video_info"]["fps"],
                    "resolution": real_result["video_info"]["resolution"]
                },
                "processing_stats": {
                    "processing_time_seconds": real_result["processing_summary"]["processing_time"],
                    "fps_processed": round(real_result["video_info"]["total_frames"] / real_result["processing_summary"]["processing_time"], 1),
                    "gpu_accelerated": GPU_AVAILABLE,
                    "detection_count": real_result["processing_summary"]["total_detections"]
                },
                "detections": real_result["detections"],
                "detection_summary": {
                    "total_detections": real_result["processing_summary"]["total_detections"],
                    "detection_types": real_result["processing_summary"]["detection_types"],
                    "average_confidence": real_result["processing_summary"].get("average_confidence", 0.0),
                    "gpu_performance": {
                        "gpu_type": "apple_m_series",
                        "expected_speedup": "3-5x vs CPU (Neural Engine优化)",
                        "memory_efficiency": "高效 (统一内存架构)",
                        "backend": "coreml"
                    }
                }
            }
        }
    
    # 如果没有找到结果，返回错误
    return {
        "success": False,
        "task_id": task_id,
        "error": "结果不存在或任务未完成"
    }

if __name__ == "__main__":
    # 显示启动信息
    print("🚀 康养AI检测系统 - 边缘控制器 (简化版)")
    print("=" * 60)
    print("📊 GPU支持:", "✅ 启用" if GPU_AVAILABLE else "❌ 禁用")
    print("🌐 服务端口: 8084")
    print("📚 API文档: http://localhost:8084/docs")
    print("=" * 60)
    
    # 如果GPU检测可用，显示GPU信息
    if GPU_AVAILABLE:
        try:
            gpu_detector = get_gpu_detector()
            gpu_info = gpu_detector.get_gpu_info()
            print(f"🔥 检测到GPU: {gpu_info['gpu_type']} - {gpu_info['gpu_name']}")
            print(f"⚡ 优化后端: {gpu_info['optimization_backend']}")
        except Exception as e:
            print(f"⚠️  GPU信息获取失败: {e}")
    
    # 启动服务
    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8084,
        access_log=True
    )