#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
康养AI检测系统 - 边缘控制器
支持22路摄像头的AI检测，专注于视频流处理和实时检测
"""

import asyncio
import logging
import signal
import sys
from pathlib import Path
from typing import Dict, Any

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
import yaml

# 添加当前目录和上级目录到Python路径
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))
sys.path.insert(0, str(current_dir.parent))

from api.detection import router as detection_router
from api.camera import router as camera_router
from api.health import router as health_router
from api.config import router as config_router
from api.management import router as management_router
from api.video_test import router as video_test_router

from core.camera_manager import EdgeCameraManager
from core.event_sender import EventSender
from core.local_cache import LocalCache

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class EdgeController:
    """边缘控制器主类"""
    
    def __init__(self, config_path: str = "config/edge_config.yaml"):
        self.config = self._load_config(config_path)
        self.app = self._create_app()
        self.camera_manager = None
        self.event_sender = None
        self.local_cache = None
        self._shutdown_event = asyncio.Event()
        
    def _load_config(self, config_path: str) -> Dict[str, Any]:
        """加载配置文件"""
        try:
            config_file = Path(__file__).parent.parent / config_path
            with open(config_file, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            logger.info(f"配置文件加载成功: {config_file}")
            return config
        except Exception as e:
            logger.error(f"配置文件加载失败: {e}")
            # 返回默认配置
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """获取默认配置"""
        return {
            "edge_controller": {
                "id": "edge_controller_1",
                "name": "边缘控制器#1"
            },
            "server": {
                "host": "0.0.0.0",
                "port": 8084,
                "workers": 4
            },
            "cameras": {
                "max_cameras": 11,
                "frame_rate": 8
            },
            "detection": {
                "algorithms": {
                    "fall_detection": {"enabled": True, "confidence_threshold": 0.8},
                    "fire_detection": {"enabled": True, "confidence_threshold": 0.85},
                    "smoke_detection": {"enabled": True, "confidence_threshold": 0.80}
                }
            },
            "management_platform": {
                "api_url": "http://localhost:8080/api",
                "heartbeat_interval": 10
            }
        }
    
    def _create_app(self) -> FastAPI:
        """创建FastAPI应用"""
        app = FastAPI(
            title="康养AI检测系统 - 边缘控制器",
            description="边缘AI检测服务，支持22路摄像头实时处理",
            version="1.0.0",
            docs_url="/docs",
            redoc_url="/redoc"
        )
        
        # CORS中间件
        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )
        
        # 注册路由
        app.include_router(detection_router, prefix="/api")
        app.include_router(camera_router, prefix="/api")
        app.include_router(health_router, prefix="/api")
        app.include_router(config_router, prefix="/api")
        app.include_router(management_router, prefix="/api")
        app.include_router(video_test_router, prefix="/api")
        
        # 根路径
        @app.get("/")
        async def root():
            return {
                "service": "康养AI检测系统 - 边缘控制器",
                "version": "1.0.0",
                "controller_id": self.config["edge_controller"]["id"],
                "controller_name": self.config["edge_controller"]["name"],
                "status": "running",
                "capabilities": [
                    "video_stream_processing",
                    "fall_detection", 
                    "fire_detection",
                    "smoke_detection",
                    "real_time_alerts"
                ]
            }
        
        # 全局异常处理
        @app.exception_handler(Exception)
        async def global_exception_handler(request: Request, exc: Exception):
            logger.error(f"全局异常: {exc}", exc_info=True)
            return JSONResponse(
                status_code=500,
                content={"error": "内部服务器错误", "detail": str(exc)}
            )
        
        # 启动事件
        @app.on_event("startup")
        async def startup_event():
            await self._startup()
        
        # 关闭事件
        @app.on_event("shutdown")
        async def shutdown_event():
            await self._shutdown()
        
        return app
    
    async def _startup(self):
        """启动时初始化"""
        try:
            logger.info("🚀 边缘控制器启动中...")
            
            # 初始化本地缓存
            self.local_cache = LocalCache()
            await self.local_cache.initialize()
            
            # 初始化事件发送器
            self.event_sender = EventSender(
                self.config["management_platform"],
                self.local_cache
            )
            await self.event_sender.initialize()
            
            # 初始化摄像头管理器
            max_cameras = self.config["cameras"]["max_cameras"]
            self.camera_manager = EdgeCameraManager(
                max_cameras=max_cameras,
                config=self.config,
                event_sender=self.event_sender
            )
            await self.camera_manager.initialize()
            
            # 存储到app state供路由使用
            self.app.state.camera_manager = self.camera_manager
            self.app.state.event_sender = self.event_sender
            self.app.state.local_cache = self.local_cache
            self.app.state.config = self.config
            
            logger.info("✅ 边缘控制器启动完成")
            logger.info(f"📷 最大摄像头数: {max_cameras}")
            logger.info(f"🎯 算法支持: {list(self.config['detection']['algorithms'].keys())}")
            logger.info(f"🌐 管理平台: {self.config['management_platform']['api_url']}")
            
        except Exception as e:
            logger.error(f"启动失败: {e}", exc_info=True)
            raise
    
    async def _shutdown(self):
        """关闭时清理"""
        try:
            logger.info("🔴 边缘控制器关闭中...")
            
            # 停止摄像头管理器
            if self.camera_manager:
                await self.camera_manager.shutdown()
            
            # 停止事件发送器
            if self.event_sender:
                await self.event_sender.shutdown()
            
            # 清理缓存
            if self.local_cache:
                await self.local_cache.cleanup()
            
            logger.info("✅ 边缘控制器已关闭")
            
        except Exception as e:
            logger.error(f"关闭失败: {e}", exc_info=True)
    
    def run(self):
        """运行边缘控制器"""
        server_config = self.config["server"]
        
        # 信号处理
        def signal_handler(signum, frame):
            logger.info(f"收到信号 {signum}，准备关闭...")
            self._shutdown_event.set()
        
        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)
        
        try:
            uvicorn.run(
                self.app,
                host=server_config["host"],
                port=server_config["port"],
                log_level=server_config.get("log_level", "info").lower()
            )
        except Exception as e:
            logger.error(f"运行失败: {e}", exc_info=True)
            sys.exit(1)

def main():
    """主入口函数"""
    controller = EdgeController()
    controller.run()

if __name__ == "__main__":
    main()