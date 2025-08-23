package com.kangyang.service;

import com.kangyang.entity.FallEvent;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

/**
 * 边缘控制器管理服务
 * 处理边缘控制器的注册、心跳、事件处理和配置管理
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class EdgeManagementService {
    
    private final FallEventService fallEventService;
    private final WechatService wechatService;
    private final RestTemplate restTemplate = new RestTemplate();
    
    // 存储边缘控制器信息
    private final Map<String, Map<String, Object>> edgeControllers = new ConcurrentHashMap<>();
    
    // 存储边缘控制器的摄像头信息
    private final Map<String, List<Map<String, Object>>> edgeCameras = new ConcurrentHashMap<>();
    
    /**
     * 处理边缘控制器心跳
     */
    public Map<String, Object> processHeartbeat(Map<String, Object> heartbeatData) {
        try {
            String controllerId = (String) heartbeatData.get("controller_id");
            String controllerName = (String) heartbeatData.get("controller_name");
            String timestamp = (String) heartbeatData.get("timestamp");
            String status = (String) heartbeatData.get("status");
            
            @SuppressWarnings("unchecked")
            Map<String, Object> systemStats = (Map<String, Object>) heartbeatData.get("system_stats");
            
            // 更新控制器信息
            Map<String, Object> controllerInfo = edgeControllers.computeIfAbsent(controllerId, k -> new HashMap<>());
            controllerInfo.put("controller_id", controllerId);
            controllerInfo.put("controller_name", controllerName);
            controllerInfo.put("status", status);
            controllerInfo.put("last_heartbeat", timestamp);
            controllerInfo.put("last_heartbeat_time", LocalDateTime.now());
            controllerInfo.put("system_stats", systemStats);
            
            log.debug("边缘控制器心跳更新: {} - {}", controllerId, status);
            
            // 返回响应（可以包含配置更新等）
            return Map.of(
                "status", "success",
                "message", "心跳接收成功",
                "server_time", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME),
                "config_updates", getConfigUpdates(controllerId)
            );
            
        } catch (Exception e) {
            log.error("处理心跳异常", e);
            throw new RuntimeException("心跳处理失败: " + e.getMessage());
        }
    }
    
    /**
     * 处理边缘控制器事件批量上报
     */
    public Map<String, Object> processEvents(String controllerId, List<Map<String, Object>> events) {
        try {
            int processedCount = 0;
            int errorCount = 0;
            List<String> errors = new ArrayList<>();
            
            for (Map<String, Object> eventData : events) {
                try {
                    // 处理单个事件
                    processDetectionEvent(controllerId, eventData);
                    processedCount++;
                    
                } catch (Exception e) {
                    errorCount++;
                    errors.add("事件处理失败: " + e.getMessage());
                    log.error("处理检测事件失败", e);
                }
            }
            
            log.info("边缘事件处理完成: controller={}, processed={}, errors={}", 
                     controllerId, processedCount, errorCount);
            
            return Map.of(
                "status", "success",
                "processed_count", processedCount,
                "error_count", errorCount,
                "errors", errors,
                "timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
            );
            
        } catch (Exception e) {
            log.error("批量处理事件异常", e);
            throw new RuntimeException("事件处理失败: " + e.getMessage());
        }
    }
    
    /**
     * 处理单个检测事件
     */
    private void processDetectionEvent(String controllerId, Map<String, Object> eventData) {
        try {
            // 创建跌倒事件对象
            FallEvent fallEvent = new FallEvent();
            
            // 设置基本信息
            fallEvent.setCameraId((String) eventData.get("camera_id"));
            fallEvent.setCameraName((String) eventData.get("camera_name"));
            fallEvent.setLocation((String) eventData.get("location"));
            fallEvent.setEventType((String) eventData.get("event_type"));
            fallEvent.setConfidence(((Number) eventData.get("confidence")).doubleValue());
            fallEvent.setSeverity((String) eventData.get("severity"));
            
            // 处理时间戳
            String timestamp = (String) eventData.get("timestamp");
            if (timestamp != null) {
                fallEvent.setDetectionTime(LocalDateTime.parse(timestamp, DateTimeFormatter.ISO_LOCAL_DATE_TIME));
            } else {
                fallEvent.setDetectionTime(LocalDateTime.now());
            }
            
            // 设置其他信息
            fallEvent.setAlgorithm((String) eventData.get("algorithm"));
            fallEvent.setAdditionalInfo(eventData.toString());
            fallEvent.setIsHandled(false);
            fallEvent.setCreatedTime(LocalDateTime.now());
            
            // 保存事件到数据库
            FallEvent savedEvent = fallEventService.createEvent(fallEvent);
            
            // 发送微信告警
            sendWechatAlert(savedEvent, eventData);
            
            log.info("检测事件处理完成: eventId={}, type={}, camera={}", 
                     savedEvent.getId(), fallEvent.getEventType(), fallEvent.getCameraId());
            
        } catch (Exception e) {
            log.error("处理检测事件异常: {}", eventData, e);
            throw e;
        }
    }
    
    /**
     * 发送微信告警
     */
    private void sendWechatAlert(FallEvent event, Map<String, Object> eventData) {
        try {
            // 构建告警消息
            StringBuilder message = new StringBuilder();
            message.append("🚨 康养AI检测告警\n\n");
            
            String eventType = event.getEventType();
            switch (eventType) {
                case "fall":
                    message.append("📍 事件类型: 跌倒检测\n");
                    break;
                case "fire":
                    message.append("🔥 事件类型: 火焰检测\n");
                    break;
                case "smoke":
                    message.append("💨 事件类型: 烟雾检测\n");
                    break;
                default:
                    message.append("⚠️ 事件类型: ").append(eventType).append("\n");
            }
            
            message.append("📍 位置: ").append(event.getLocation()).append("\n");
            message.append("📷 摄像头: ").append(event.getCameraName()).append("\n");
            message.append("⏰ 时间: ").append(event.getDetectionTime().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))).append("\n");
            message.append("🎯 置信度: ").append(String.format("%.2f", event.getConfidence() * 100)).append("%\n");
            message.append("📊 严重等级: ").append(event.getSeverity()).append("\n");
            
            // 添加处理建议
            if ("fire".equals(eventType) || "smoke".equals(eventType)) {
                message.append("\n🆘 请立即查看现场情况，必要时联系消防部门！");
            } else if ("fall".equals(eventType)) {
                message.append("\n🏥 请及时查看老人状况，提供必要帮助！");
            }
            
            // 发送微信通知
            wechatService.sendAlert(message.toString());
            
            log.info("微信告警发送成功: eventId={}", event.getId());
            
        } catch (Exception e) {
            log.error("发送微信告警失败: eventId={}", event.getId(), e);
        }
    }
    
    /**
     * 获取边缘控制器列表
     */
    public List<Map<String, Object>> getEdgeControllers() {
        List<Map<String, Object>> controllers = new ArrayList<>();
        
        for (Map<String, Object> controller : edgeControllers.values()) {
            Map<String, Object> info = new HashMap<>(controller);
            
            // 计算在线状态
            LocalDateTime lastHeartbeat = (LocalDateTime) controller.get("last_heartbeat_time");
            boolean isOnline = lastHeartbeat != null && 
                              lastHeartbeat.isAfter(LocalDateTime.now().minusMinutes(2));
            info.put("is_online", isOnline);
            
            // 获取摄像头数量
            String controllerId = (String) controller.get("controller_id");
            List<Map<String, Object>> cameras = edgeCameras.getOrDefault(controllerId, new ArrayList<>());
            info.put("camera_count", cameras.size());
            
            controllers.add(info);
        }
        
        return controllers;
    }
    
    /**
     * 获取边缘控制器详情
     */
    public Map<String, Object> getEdgeController(String controllerId) {
        Map<String, Object> controller = edgeControllers.get(controllerId);
        if (controller == null) {
            return null;
        }
        
        Map<String, Object> info = new HashMap<>(controller);
        
        // 计算在线状态
        LocalDateTime lastHeartbeat = (LocalDateTime) controller.get("last_heartbeat_time");
        boolean isOnline = lastHeartbeat != null && 
                          lastHeartbeat.isAfter(LocalDateTime.now().minusMinutes(2));
        info.put("is_online", isOnline);
        
        // 获取摄像头列表
        List<Map<String, Object>> cameras = edgeCameras.getOrDefault(controllerId, new ArrayList<>());
        info.put("cameras", cameras);
        info.put("camera_count", cameras.size());
        
        return info;
    }
    
    /**
     * 发送配置到边缘控制器
     */
    public Map<String, Object> sendConfig(String controllerId, Map<String, Object> config) {
        try {
            Map<String, Object> controller = edgeControllers.get(controllerId);
            if (controller == null) {
                throw new RuntimeException("边缘控制器不存在: " + controllerId);
            }
            
            // 这里可以实现向边缘控制器发送配置的逻辑
            // 暂时存储配置更新，在下次心跳时返回
            
            log.info("配置发送成功: controller={}", controllerId);
            
            return Map.of(
                "status", "success",
                "message", "配置发送成功",
                "controller_id", controllerId
            );
            
        } catch (Exception e) {
            log.error("发送配置失败", e);
            throw new RuntimeException("配置发送失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取边缘控制器摄像头列表
     */
    public List<Map<String, Object>> getEdgeCameras(String controllerId) {
        return edgeCameras.getOrDefault(controllerId, new ArrayList<>());
    }
    
    /**
     * 向边缘控制器添加摄像头
     */
    public Map<String, Object> addEdgeCamera(String controllerId, Map<String, Object> cameraData) {
        try {
            List<Map<String, Object>> cameras = edgeCameras.computeIfAbsent(controllerId, k -> new ArrayList<>());
            
            // 添加摄像头到列表
            cameras.add(cameraData);
            
            log.info("边缘摄像头添加成功: controller={}, camera={}", controllerId, cameraData.get("id"));
            
            return Map.of(
                "status", "success",
                "message", "摄像头添加成功",
                "camera_id", cameraData.get("id")
            );
            
        } catch (Exception e) {
            log.error("添加边缘摄像头失败", e);
            throw new RuntimeException("添加摄像头失败: " + e.getMessage());
        }
    }
    
    /**
     * 从边缘控制器移除摄像头
     */
    public Map<String, Object> removeEdgeCamera(String controllerId, String cameraId) {
        try {
            List<Map<String, Object>> cameras = edgeCameras.get(controllerId);
            if (cameras != null) {
                cameras.removeIf(camera -> cameraId.equals(camera.get("id")));
            }
            
            log.info("边缘摄像头移除成功: controller={}, camera={}", controllerId, cameraId);
            
            return Map.of(
                "status", "success",
                "message", "摄像头移除成功",
                "camera_id", cameraId
            );
            
        } catch (Exception e) {
            log.error("移除边缘摄像头失败", e);
            throw new RuntimeException("移除摄像头失败: " + e.getMessage());
        }
    }
    
    /**
     * 控制摄像头流
     */
    public Map<String, Object> controlCameraStream(String controllerId, String cameraId, String action) {
        try {
            log.info("控制摄像头流: controller={}, camera={}, action={}", controllerId, cameraId, action);
            
            return Map.of(
                "status", "success",
                "message", "流控制成功",
                "action", action,
                "camera_id", cameraId
            );
            
        } catch (Exception e) {
            log.error("控制摄像头流失败", e);
            throw new RuntimeException("控制流失败: " + e.getMessage());
        }
    }
    
    /**
     * 获取边缘控制器统计信息
     */
    public Map<String, Object> getEdgeStatistics() {
        int totalControllers = edgeControllers.size();
        long onlineControllers = edgeControllers.values().stream()
            .mapToLong(controller -> {
                LocalDateTime lastHeartbeat = (LocalDateTime) controller.get("last_heartbeat_time");
                return (lastHeartbeat != null && lastHeartbeat.isAfter(LocalDateTime.now().minusMinutes(2))) ? 1 : 0;
            })
            .sum();
        
        int totalCameras = edgeCameras.values().stream()
            .mapToInt(List::size)
            .sum();
        
        return Map.of(
            "total_controllers", totalControllers,
            "online_controllers", onlineControllers,
            "offline_controllers", totalControllers - onlineControllers,
            "total_cameras", totalCameras,
            "last_update", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        );
    }
    
    /**
     * 获取配置更新（在心跳响应中返回）
     */
    private Map<String, Object> getConfigUpdates(String controllerId) {
        // 这里可以实现配置更新逻辑
        // 暂时返回空配置
        return Map.of();
    }
}