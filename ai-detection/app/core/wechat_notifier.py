#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
微信公众号告警通知模块
支持跌倒、火焰、烟雾检测事件的实时推送
"""

import aiohttp
import asyncio
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import hashlib
import time

logger = logging.getLogger(__name__)

@dataclass
class WeChatConfig:
    """微信公众号配置"""
    app_id: str
    app_secret: str
    template_id: str = ""  # 消息模板ID
    access_token: str = ""
    token_expires_at: datetime = None

@dataclass
class AlertEvent:
    """告警事件"""
    event_type: str  # fall, fire, smoke
    event_subtype: str
    confidence: float
    timestamp: float
    location: str = "未知位置"
    severity: str = "HIGH"
    video_file: str = ""
    frame_number: int = 0

class WeChatNotifier:
    """微信公众号通知器"""
    
    def __init__(self, app_id: str, app_secret: str):
        """
        初始化微信通知器
        
        Args:
            app_id: 微信公众号AppID
            app_secret: 微信公众号AppSecret
        """
        self.config = WeChatConfig(
            app_id=app_id,
            app_secret=app_secret
        )
        self.session = None
        self.subscribers = []  # 订阅用户openid列表
        
        # 事件类型映射
        self.event_names = {
            'fall': '跌倒检测',
            'fire': '火焰检测',
            'smoke': '烟雾检测'
        }
        
        # 严重级别映射
        self.severity_names = {
            'LOW': '低风险',
            'MEDIUM': '中等风险',
            'HIGH': '高风险',
            'CRITICAL': '紧急'
        }
        
        logger.info("微信通知器初始化完成")
    
    async def __aenter__(self):
        """异步上下文管理器入口"""
        self.session = aiohttp.ClientSession()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """异步上下文管理器出口"""
        if self.session:
            await self.session.close()
    
    async def get_access_token(self) -> str:
        """获取微信访问令牌"""
        # 检查令牌是否有效
        if (self.config.access_token and 
            self.config.token_expires_at and 
            datetime.now() < self.config.token_expires_at):
            return self.config.access_token
        
        # 获取新令牌
        url = "https://api.weixin.qq.com/cgi-bin/token"
        params = {
            'grant_type': 'client_credential',
            'appid': self.config.app_id,
            'secret': self.config.app_secret
        }
        
        try:
            if not self.session:
                self.session = aiohttp.ClientSession()
                
            async with self.session.get(url, params=params) as response:
                data = await response.json()
                
                if 'access_token' in data:
                    self.config.access_token = data['access_token']
                    expires_in = data.get('expires_in', 7200)
                    self.config.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)
                    
                    logger.info("微信访问令牌获取成功")
                    return self.config.access_token
                else:
                    logger.error(f"获取微信访问令牌失败: {data}")
                    return ""
                    
        except Exception as e:
            logger.error(f"获取微信访问令牌异常: {str(e)}")
            return ""
    
    async def send_template_message(self, openid: str, event: AlertEvent) -> bool:
        """
        发送模板消息
        
        Args:
            openid: 用户openid
            event: 告警事件
            
        Returns:
            发送是否成功
        """
        access_token = await self.get_access_token()
        if not access_token:
            return False
        
        url = f"https://api.weixin.qq.com/cgi-bin/message/template/send?access_token={access_token}"
        
        # 构建消息内容
        event_time = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        
        # 根据事件类型选择颜色
        color_map = {
            'fall': '#FF4444',  # 红色
            'fire': '#FF6600',  # 橙色
            'smoke': '#666666'  # 灰色
        }
        
        message_data = {
            "touser": openid,
            "template_id": self.config.template_id,
            "data": {
                "first": {
                    "value": f"🚨 {self.event_names.get(event.event_type, '未知事件')}告警",
                    "color": color_map.get(event.event_type, '#FF0000')
                },
                "keyword1": {
                    "value": self.event_names.get(event.event_type, '未知'),
                    "color": "#173177"
                },
                "keyword2": {
                    "value": event_time,
                    "color": "#173177"
                },
                "keyword3": {
                    "value": event.location,
                    "color": "#173177"
                },
                "keyword4": {
                    "value": f"{self.severity_names.get(event.severity, '未知')} (置信度: {event.confidence:.1%})",
                    "color": color_map.get(event.event_type, '#FF0000')
                },
                "remark": {
                    "value": f"请立即查看监控画面并采取相应措施。事件详情: {event.event_subtype}",
                    "color": "#666666"
                }
            }
        }
        
        try:
            async with self.session.post(url, json=message_data) as response:
                result = await response.json()
                
                if result.get('errcode') == 0:
                    logger.info(f"微信消息发送成功: {openid}")
                    return True
                else:
                    logger.error(f"微信消息发送失败: {result}")
                    return False
                    
        except Exception as e:
            logger.error(f"发送微信消息异常: {str(e)}")
            return False
    
    async def send_text_message(self, event: AlertEvent) -> bool:
        """
        发送文本消息（客服消息接口）
        
        Args:
            event: 告警事件
            
        Returns:
            发送是否成功
        """
        access_token = await self.get_access_token()
        if not access_token:
            return False
        
        # 构建告警文本
        event_time = datetime.fromtimestamp(event.timestamp).strftime("%Y-%m-%d %H:%M:%S")
        alert_text = f"""🚨 康养AI检测告警

📍 事件类型: {self.event_names.get(event.event_type, '未知事件')}
📍 事件子类: {event.event_subtype}
🕐 发生时间: {event_time}
📍 检测位置: {event.location}
⚠️  严重程度: {self.severity_names.get(event.severity, '未知')}
🎯 置信度: {event.confidence:.1%}

请立即查看监控画面并采取相应措施！"""

        success_count = 0
        for openid in self.subscribers:
            url = f"https://api.weixin.qq.com/cgi-bin/message/custom/send?access_token={access_token}"
            
            message_data = {
                "touser": openid,
                "msgtype": "text",
                "text": {
                    "content": alert_text
                }
            }
            
            try:
                async with self.session.post(url, json=message_data) as response:
                    result = await response.json()
                    
                    if result.get('errcode') == 0:
                        logger.info(f"微信文本消息发送成功: {openid}")
                        success_count += 1
                    else:
                        logger.error(f"微信文本消息发送失败: {result}")
                        
            except Exception as e:
                logger.error(f"发送微信文本消息异常: {str(e)}")
        
        return success_count > 0
    
    def add_subscriber(self, openid: str):
        """添加订阅用户"""
        if openid not in self.subscribers:
            self.subscribers.append(openid)
            logger.info(f"添加微信订阅用户: {openid}")
    
    def remove_subscriber(self, openid: str):
        """移除订阅用户"""
        if openid in self.subscribers:
            self.subscribers.remove(openid)
            logger.info(f"移除微信订阅用户: {openid}")
    
    async def send_alert(self, event: AlertEvent) -> bool:
        """
        发送告警通知
        
        Args:
            event: 告警事件
            
        Returns:
            发送是否成功
        """
        if not self.subscribers:
            logger.warning("没有配置微信订阅用户")
            return False
        
        logger.info(f"发送微信告警: {event.event_type} - {event.event_subtype}")
        
        # 优先使用文本消息（更通用）
        return await self.send_text_message(event)

# 全局微信通知器实例
wechat_notifier = None

def init_wechat_notifier(app_id: str, app_secret: str) -> WeChatNotifier:
    """初始化微信通知器"""
    global wechat_notifier
    wechat_notifier = WeChatNotifier(app_id, app_secret)
    return wechat_notifier

def get_wechat_notifier() -> Optional[WeChatNotifier]:
    """获取微信通知器实例"""
    return wechat_notifier

# 测试功能
async def test_wechat_notification():
    """测试微信通知功能"""
    # 使用提供的配置
    app_id = "wx10dcc9f0235e1d77"
    app_secret = "b7e9088f3f5fe18a9cfb990c641138b3"
    
    async with WeChatNotifier(app_id, app_secret) as notifier:
        # 添加测试用户（需要替换为实际的openid）
        # notifier.add_subscriber("test_openid_here")
        
        # 创建测试事件
        test_event = AlertEvent(
            event_type="fall",
            event_subtype="backward_fall",
            confidence=0.95,
            timestamp=time.time(),
            location="养老院一楼客厅",
            severity="CRITICAL"
        )
        
        # 发送测试通知
        result = await notifier.send_alert(test_event)
        print(f"测试结果: {result}")

if __name__ == "__main__":
    # 运行测试
    asyncio.run(test_wechat_notification())