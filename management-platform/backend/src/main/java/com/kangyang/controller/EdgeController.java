package com.kangyang.controller;

import com.kangyang.service.EdgeManagementService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 边缘控制器管理接口
 * 处理边缘控制器的心跳、事件上报和配置管理
 */
@Slf4j
@RestController
@RequestMapping("/api/edge")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class EdgeController {
    
    private final EdgeManagementService edgeManagementService;
    
    /**
     * 接收边缘控制器心跳
     */
    @PostMapping("/heartbeat")
    public ResponseEntity<Map<String, Object>> receiveHeartbeat(@RequestBody Map<String, Object> heartbeatData) {
        try {
            log.info("收到边缘控制器心跳: {}", heartbeatData.get("controller_id"));
            
            Map<String, Object> response = edgeManagementService.processHeartbeat(heartbeatData);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("处理心跳失败", e);
            return ResponseEntity.badRequest()
                .body(Map.of("error", "心跳处理失败", "message", e.getMessage()));
        }
    }
    
    /**
     * 接收边缘控制器事件批量上报
     */
    @PostMapping("/events")
    public ResponseEntity<Map<String, Object>> receiveEvents(@RequestBody Map<String, Object> eventData) {
        try {
            String controllerId = (String) eventData.get("controller_id");
            @SuppressWarnings("unchecked")
            List<Map<String, Object>> events = (List<Map<String, Object>>) eventData.get("events");
            
            log.info("收到边缘控制器事件: controller={}, count={}", controllerId, events.size());
            
            Map<String, Object> response = edgeManagementService.processEvents(controllerId, events);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("处理事件失败", e);
            return ResponseEntity.badRequest()
                .body(Map.of("error", "事件处理失败", "message", e.getMessage()));
        }
    }
    
    /**
     * 获取边缘控制器列表
     */
    @GetMapping("/controllers")
    public ResponseEntity<List<Map<String, Object>>> getEdgeControllers() {
        try {
            List<Map<String, Object>> controllers = edgeManagementService.getEdgeControllers();
            return ResponseEntity.ok(controllers);
            
        } catch (Exception e) {
            log.error("获取边缘控制器列表失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 获取边缘控制器详情
     */
    @GetMapping("/controllers/{controllerId}")
    public ResponseEntity<Map<String, Object>> getEdgeController(@PathVariable String controllerId) {
        try {
            Map<String, Object> controller = edgeManagementService.getEdgeController(controllerId);
            if (controller != null) {
                return ResponseEntity.ok(controller);
            } else {
                return ResponseEntity.notFound().build();
            }
            
        } catch (Exception e) {
            log.error("获取边缘控制器详情失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 向边缘控制器发送配置
     */
    @PostMapping("/controllers/{controllerId}/config")
    public ResponseEntity<Map<String, Object>> sendConfig(
            @PathVariable String controllerId,
            @RequestBody Map<String, Object> config) {
        try {
            Map<String, Object> response = edgeManagementService.sendConfig(controllerId, config);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("发送配置失败", e);
            return ResponseEntity.badRequest()
                .body(Map.of("error", "配置发送失败", "message", e.getMessage()));
        }
    }
    
    /**
     * 获取边缘控制器摄像头列表
     */
    @GetMapping("/controllers/{controllerId}/cameras")
    public ResponseEntity<List<Map<String, Object>>> getEdgeCameras(@PathVariable String controllerId) {
        try {
            List<Map<String, Object>> cameras = edgeManagementService.getEdgeCameras(controllerId);
            return ResponseEntity.ok(cameras);
            
        } catch (Exception e) {
            log.error("获取边缘摄像头列表失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 向边缘控制器添加摄像头
     */
    @PostMapping("/controllers/{controllerId}/cameras")
    public ResponseEntity<Map<String, Object>> addEdgeCamera(
            @PathVariable String controllerId,
            @RequestBody Map<String, Object> cameraData) {
        try {
            Map<String, Object> response = edgeManagementService.addEdgeCamera(controllerId, cameraData);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("添加边缘摄像头失败", e);
            return ResponseEntity.badRequest()
                .body(Map.of("error", "添加摄像头失败", "message", e.getMessage()));
        }
    }
    
    /**
     * 从边缘控制器移除摄像头
     */
    @DeleteMapping("/controllers/{controllerId}/cameras/{cameraId}")
    public ResponseEntity<Map<String, Object>> removeEdgeCamera(
            @PathVariable String controllerId,
            @PathVariable String cameraId) {
        try {
            Map<String, Object> response = edgeManagementService.removeEdgeCamera(controllerId, cameraId);
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("移除边缘摄像头失败", e);
            return ResponseEntity.badRequest()
                .body(Map.of("error", "移除摄像头失败", "message", e.getMessage()));
        }
    }
    
    /**
     * 启动/停止边缘摄像头流
     */
    @PostMapping("/controllers/{controllerId}/cameras/{cameraId}/stream")
    public ResponseEntity<Map<String, Object>> controlCameraStream(
            @PathVariable String controllerId,
            @PathVariable String cameraId,
            @RequestParam String action) {
        try {
            Map<String, Object> response = edgeManagementService.controlCameraStream(
                controllerId, cameraId, action
            );
            return ResponseEntity.ok(response);
            
        } catch (Exception e) {
            log.error("控制摄像头流失败", e);
            return ResponseEntity.badRequest()
                .body(Map.of("error", "控制流失败", "message", e.getMessage()));
        }
    }
    
    /**
     * 获取边缘控制器统计信息
     */
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getEdgeStatistics() {
        try {
            Map<String, Object> statistics = edgeManagementService.getEdgeStatistics();
            return ResponseEntity.ok(statistics);
            
        } catch (Exception e) {
            log.error("获取边缘统计信息失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
}