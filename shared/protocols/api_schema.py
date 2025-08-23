#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API模式定义
定义请求和响应的JSON Schema
"""

from typing import Dict, Any

# 检测事件 Schema
DETECTION_EVENT_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "event_type": {"type": "string", "enum": ["fall", "fire", "smoke", "system"]},
        "event_subtype": {"type": "string"},
        "camera_id": {"type": "string"},
        "camera_name": {"type": "string"},
        "location": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "confidence": {"type": "number", "minimum": 0, "maximum": 1},
        "severity": {"type": "string", "enum": ["LOW", "MEDIUM", "HIGH", "CRITICAL"]},
        "bbox": {
            "type": "array",
            "items": {"type": "integer"},
            "minItems": 4,
            "maxItems": 4
        },
        "algorithm": {"type": "string"},
        "additional_data": {"type": "object"}
    },
    "required": ["id", "event_type", "camera_id", "camera_name", "location", "timestamp", "confidence"],
    "additionalProperties": False
}

# 心跳数据 Schema
HEARTBEAT_SCHEMA = {
    "type": "object",
    "properties": {
        "controller_id": {"type": "string"},
        "controller_name": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "status": {"type": "string", "enum": ["running", "stopped", "error", "maintenance"]},
        "camera_count": {"type": "integer", "minimum": 0},
        "active_cameras": {"type": "integer", "minimum": 0},
        "system_stats": {
            "type": "object",
            "properties": {
                "controller_id": {"type": "string"},
                "controller_name": {"type": "string"},
                "total_cameras": {"type": "integer", "minimum": 0},
                "active_cameras": {"type": "integer", "minimum": 0},
                "online_cameras": {"type": "integer", "minimum": 0},
                "total_detections": {"type": "integer", "minimum": 0},
                "total_frames_processed": {"type": "integer", "minimum": 0},
                "uptime_seconds": {"type": "number", "minimum": 0},
                "average_fps": {"type": "number", "minimum": 0},
                "cpu_usage": {"type": "number", "minimum": 0, "maximum": 100},
                "memory_usage": {"type": "number", "minimum": 0, "maximum": 100},
                "gpu_usage": {"type": "number", "minimum": 0, "maximum": 100},
                "disk_usage": {"type": "number", "minimum": 0, "maximum": 100},
                "temperature": {"type": "number"}
            },
            "required": ["controller_id", "total_cameras", "active_cameras", "uptime_seconds"],
            "additionalProperties": False
        }
    },
    "required": ["controller_id", "controller_name", "timestamp", "status", "camera_count", "system_stats"],
    "additionalProperties": False
}

# 事件批量上报 Schema
EVENT_BATCH_SCHEMA = {
    "type": "object",
    "properties": {
        "controller_id": {"type": "string"},
        "timestamp": {"type": "string", "format": "date-time"},
        "events": {
            "type": "array",
            "items": DETECTION_EVENT_SCHEMA,
            "maxItems": 100  # 限制批量大小
        }
    },
    "required": ["controller_id", "timestamp", "events"],
    "additionalProperties": False
}

# 摄像头信息 Schema
CAMERA_INFO_SCHEMA = {
    "type": "object",
    "properties": {
        "id": {"type": "string"},
        "name": {"type": "string"},
        "rtsp_url": {"type": "string", "format": "uri"},
        "location": {"type": "string"},
        "zone_id": {"type": "string"},
        "status": {"type": "string", "enum": ["online", "offline", "error"]},
        "enabled_algorithms": {
            "type": "array",
            "items": {"type": "string", "enum": ["fall_detection", "fire_detection", "smoke_detection"]},
            "uniqueItems": True
        },
        "fps": {"type": "number", "minimum": 0},
        "last_frame_time": {"type": "string", "format": "date-time"},
        "total_detections": {"type": "integer", "minimum": 0}
    },
    "required": ["id", "name", "rtsp_url", "location"],
    "additionalProperties": False
}

# 配置更新 Schema
CONFIG_UPDATE_SCHEMA = {
    "type": "object",
    "properties": {
        "target": {"type": "string", "enum": ["controller", "camera", "algorithm"]},
        "target_id": {"type": "string"},
        "config": {"type": "object"},
        "timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["target", "target_id", "config", "timestamp"],
    "additionalProperties": False
}

# 命令请求 Schema
COMMAND_REQUEST_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {
            "type": "string", 
            "enum": ["start_camera", "stop_camera", "restart_controller", "update_config", "get_status"]
        },
        "target": {"type": "string"},
        "parameters": {"type": "object"},
        "timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["command", "target", "timestamp"],
    "additionalProperties": False
}

# 命令响应 Schema
COMMAND_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "command": {"type": "string"},
        "target": {"type": "string"},
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "data": {"type": "object"},
        "timestamp": {"type": "string", "format": "date-time"}
    },
    "required": ["command", "target", "success", "message", "timestamp"],
    "additionalProperties": False
}

# 标准响应 Schema
STANDARD_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "message": {"type": "string"},
        "data": {"type": "object"},
        "timestamp": {"type": "string", "format": "date-time"},
        "protocol_version": {"type": "string"}
    },
    "required": ["success", "message", "timestamp", "protocol_version"],
    "additionalProperties": False
}

# 错误响应 Schema
ERROR_RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean", "enum": [False]},
        "error": {
            "type": "object",
            "properties": {
                "code": {"type": "string"},
                "message": {"type": "string"},
                "details": {"type": "object"}
            },
            "required": ["code", "message"],
            "additionalProperties": False
        },
        "timestamp": {"type": "string", "format": "date-time"},
        "protocol_version": {"type": "string"}
    },
    "required": ["success", "error", "timestamp", "protocol_version"],
    "additionalProperties": False
}

# API 端点定义
API_ENDPOINTS = {
    # 管理平台端点
    "management_platform": {
        "heartbeat": {
            "method": "POST",
            "path": "/api/edge/heartbeat",
            "request_schema": HEARTBEAT_SCHEMA,
            "response_schema": STANDARD_RESPONSE_SCHEMA
        },
        "events": {
            "method": "POST",
            "path": "/api/edge/events",
            "request_schema": EVENT_BATCH_SCHEMA,
            "response_schema": STANDARD_RESPONSE_SCHEMA
        },
        "get_controllers": {
            "method": "GET",
            "path": "/api/edge/controllers",
            "response_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "data": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "properties": {
                                "controller_id": {"type": "string"},
                                "controller_name": {"type": "string"},
                                "status": {"type": "string"},
                                "is_online": {"type": "boolean"},
                                "camera_count": {"type": "integer"},
                                "last_heartbeat": {"type": "string"}
                            }
                        }
                    }
                }
            }
        }
    },
    
    # 边缘控制器端点
    "edge_controller": {
        "health": {
            "method": "GET",
            "path": "/api/health",
            "response_schema": {
                "type": "object",
                "properties": {
                    "status": {"type": "string"},
                    "service": {"type": "string"},
                    "version": {"type": "string"},
                    "timestamp": {"type": "string"},
                    "components": {"type": "object"},
                    "system_stats": {"type": "object"}
                }
            }
        },
        "add_camera": {
            "method": "POST",
            "path": "/api/cameras",
            "request_schema": CAMERA_INFO_SCHEMA,
            "response_schema": STANDARD_RESPONSE_SCHEMA
        },
        "get_cameras": {
            "method": "GET",
            "path": "/api/cameras",
            "response_schema": {
                "type": "object",
                "properties": {
                    "success": {"type": "boolean"},
                    "cameras": {
                        "type": "array",
                        "items": CAMERA_INFO_SCHEMA
                    },
                    "total": {"type": "integer"}
                }
            }
        },
        "control_camera": {
            "method": "POST",
            "path": "/api/cameras/{camera_id}/{action}",
            "response_schema": STANDARD_RESPONSE_SCHEMA
        }
    }
}

# 错误代码定义
ERROR_CODES = {
    "INVALID_REQUEST": "INVALID_REQUEST",
    "AUTHENTICATION_FAILED": "AUTHENTICATION_FAILED",
    "CAMERA_NOT_FOUND": "CAMERA_NOT_FOUND",
    "CONTROLLER_NOT_FOUND": "CONTROLLER_NOT_FOUND",
    "RTSP_CONNECTION_FAILED": "RTSP_CONNECTION_FAILED",
    "ALGORITHM_ERROR": "ALGORITHM_ERROR",
    "SYSTEM_OVERLOAD": "SYSTEM_OVERLOAD",
    "CONFIG_VALIDATION_FAILED": "CONFIG_VALIDATION_FAILED",
    "INTERNAL_SERVER_ERROR": "INTERNAL_SERVER_ERROR"
}

def get_schema_by_endpoint(endpoint_category: str, endpoint_name: str, schema_type: str) -> Dict[str, Any]:
    """
    根据端点获取Schema
    
    Args:
        endpoint_category: 端点分类 ("management_platform" | "edge_controller")
        endpoint_name: 端点名称
        schema_type: Schema类型 ("request_schema" | "response_schema")
    
    Returns:
        对应的Schema字典
    """
    try:
        return API_ENDPOINTS[endpoint_category][endpoint_name][schema_type]
    except KeyError:
        return None

def validate_request_data(endpoint_category: str, endpoint_name: str, data: Dict[str, Any]) -> bool:
    """
    验证请求数据
    
    Args:
        endpoint_category: 端点分类
        endpoint_name: 端点名称
        data: 要验证的数据
    
    Returns:
        验证是否通过
    """
    schema = get_schema_by_endpoint(endpoint_category, endpoint_name, "request_schema")
    if not schema:
        return False
    
    # 这里可以使用 jsonschema 库进行验证
    # 简化版本的验证逻辑
    return True  # 实际实现中需要真正的JSON Schema验证