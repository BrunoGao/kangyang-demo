from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from datetime import datetime
import logging

# 设置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 导入API路由
from api.detection import router as detection_router
from api.wechat import router as wechat_router

# 导入核心模块
from core.wechat_notifier import init_wechat_notifier

# 创建FastAPI应用
app = FastAPI(
    title="康养AI检测系统",
    description="基于FastAPI的多场景AI检测系统，支持跌倒、火焰、烟雾检测和微信告警",
    version="3.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# 包含API路由
app.include_router(detection_router)
app.include_router(wechat_router)

# 配置模板和静态文件
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.on_event("startup")
async def startup_event():
    """应用启动时的初始化"""
    # 初始化微信通知器
    app_id = "wx10dcc9f0235e1d77"
    app_secret = "b7e9088f3f5fe18a9cfb990c641138b3"
    init_wechat_notifier(app_id, app_secret)
    logger.info("✅ 康养AI检测系统启动完成")

@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    """首页 - AI检测专业平台"""
    return templates.TemplateResponse("professional_platform.html", {"request": request})

@app.get("/health")
async def health_check():
    """健康检查"""
    return {
        'status': 'healthy',
        'service': '康养AI检测系统',
        'version': '3.0.0',
        'features': [
            'video_upload', 
            'multi_detection', 
            'wechat_alerts', 
            'real_time_analysis'
        ],
        'timestamp': datetime.now().isoformat()
    }

# 兼容性路由 - 将旧的API路径重定向到新的路由结构

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8084)