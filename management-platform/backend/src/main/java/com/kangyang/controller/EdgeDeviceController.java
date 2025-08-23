package com.kangyang.controller;

import com.kangyang.entity.EdgeDevice;
import com.kangyang.service.EdgeDeviceService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;
import java.util.Optional;

/**
 * 边缘设备管理控制器
 */
@Slf4j
@RestController
@RequestMapping("/api/edge-devices")
@CrossOrigin
public class EdgeDeviceController {
    
    @Autowired
    private EdgeDeviceService edgeDeviceService;
    
    /**
     * 获取所有边缘设备
     */
    @GetMapping
    public ResponseEntity<List<EdgeDevice>> getAllDevices() {
        List<EdgeDevice> devices = edgeDeviceService.getAllDevices();
        return ResponseEntity.ok(devices);
    }
    
    /**
     * 根据ID获取边缘设备
     */
    @GetMapping("/{id}")
    public ResponseEntity<EdgeDevice> getDevice(@PathVariable Long id) {
        Optional<EdgeDevice> device = edgeDeviceService.getDeviceById(id);
        return device.map(ResponseEntity::ok)
                    .orElse(ResponseEntity.notFound().build());
    }
    
    /**
     * 创建边缘设备
     */
    @PostMapping
    public ResponseEntity<EdgeDevice> createDevice(@RequestBody EdgeDevice device) {
        try {
            EdgeDevice savedDevice = edgeDeviceService.saveDevice(device);
            log.info("创建边缘设备: {}", device.getDeviceId());
            return ResponseEntity.ok(savedDevice);
        } catch (Exception e) {
            log.error("创建边缘设备失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 更新边缘设备
     */
    @PutMapping("/{id}")
    public ResponseEntity<EdgeDevice> updateDevice(@PathVariable Long id, @RequestBody EdgeDevice device) {
        try {
            device.setId(id);
            EdgeDevice updatedDevice = edgeDeviceService.saveDevice(device);
            log.info("更新边缘设备: {}", device.getDeviceId());
            return ResponseEntity.ok(updatedDevice);
        } catch (Exception e) {
            log.error("更新边缘设备失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 删除边缘设备
     */
    @DeleteMapping("/{id}")
    public ResponseEntity<Void> deleteDevice(@PathVariable Long id) {
        try {
            edgeDeviceService.deleteDevice(id);
            log.info("删除边缘设备: {}", id);
            return ResponseEntity.ok().build();
        } catch (Exception e) {
            log.error("删除边缘设备失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 设备心跳接口
     */
    @PostMapping("/{deviceId}/heartbeat")
    public ResponseEntity<Map<String, Object>> heartbeat(@PathVariable String deviceId, @RequestBody(required = false) Map<String, Object> data) {
        try {
            edgeDeviceService.updateHeartbeat(deviceId);
            return ResponseEntity.ok(Map.of(
                "success", true,
                "deviceId", deviceId,
                "timestamp", System.currentTimeMillis()
            ));
        } catch (Exception e) {
            log.error("设备心跳更新失败: {}", deviceId, e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
    
    /**
     * 检查设备健康状态
     */
    @GetMapping("/{deviceId}/health")
    public ResponseEntity<Map<String, Object>> checkHealth(@PathVariable String deviceId) {
        Map<String, Object> result = edgeDeviceService.checkDeviceHealth(deviceId);
        return ResponseEntity.ok(result);
    }
    
    /**
     * 获取设备统计信息
     */
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getStatistics() {
        Map<String, Object> stats = edgeDeviceService.getDeviceStatistics();
        return ResponseEntity.ok(stats);
    }
    
    /**
     * 发送命令到边缘设备
     */
    @PostMapping("/{deviceId}/command")
    public ResponseEntity<Map<String, Object>> sendCommand(
            @PathVariable String deviceId, 
            @RequestBody Map<String, Object> command) {
        
        Map<String, Object> result = edgeDeviceService.sendCommandToDevice(deviceId, command);
        return ResponseEntity.ok(result);
    }
    
    /**
     * 批量健康检查
     */
    @PostMapping("/health-check")
    public ResponseEntity<Map<String, Object>> batchHealthCheck() {
        List<EdgeDevice> devices = edgeDeviceService.getAllDevices();
        Map<String, Object> results = Map.of("results", 
            devices.stream().map(device -> 
                edgeDeviceService.checkDeviceHealth(device.getDeviceId())
            ).toList()
        );
        return ResponseEntity.ok(results);
    }
    
    /**
     * 模拟AI检测事件（用于测试）
     */
    @PostMapping("/{deviceId}/simulate-detection")
    public ResponseEntity<Map<String, Object>> simulateDetection(
            @PathVariable String deviceId,
            @RequestBody Map<String, Object> detectionData) {
        
        try {
            String eventType = (String) detectionData.getOrDefault("type", "fall");
            String location = (String) detectionData.getOrDefault("location", "未知位置");
            Double confidence = (Double) detectionData.getOrDefault("confidence", 0.95);
            
            // 这里可以集成实际的AI检测逻辑
            log.info("模拟AI检测事件 - 设备: {}, 类型: {}, 位置: {}, 置信度: {}", 
                    deviceId, eventType, location, confidence);
            
            return ResponseEntity.ok(Map.of(
                "success", true,
                "deviceId", deviceId,
                "event", Map.of(
                    "type", eventType,
                    "location", location,
                    "confidence", confidence,
                    "timestamp", System.currentTimeMillis()
                )
            ));
            
        } catch (Exception e) {
            log.error("模拟AI检测失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
    
    /**
     * 更新设备算法配置
     */
    @PostMapping("/{deviceId}/algorithm-config")
    public ResponseEntity<Map<String, Object>> updateAlgorithmConfig(
            @PathVariable String deviceId,
            @RequestBody Map<String, Object> config) {
        
        try {
            Map<String, Object> result = edgeDeviceService.updateAlgorithmConfig(deviceId, config);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("更新算法配置失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
    
    /**
     * 获取设备性能监控数据
     */
    @GetMapping("/{deviceId}/performance")
    public ResponseEntity<Map<String, Object>> getPerformanceMetrics(@PathVariable String deviceId) {
        Map<String, Object> metrics = edgeDeviceService.getPerformanceMetrics(deviceId);
        return ResponseEntity.ok(metrics);
    }
    
    /**
     * 启动/停止边缘设备
     */
    @PostMapping("/{deviceId}/control")
    public ResponseEntity<Map<String, Object>> controlDevice(
            @PathVariable String deviceId,
            @RequestBody Map<String, Object> controlData) {
        
        try {
            String action = (String) controlData.get("action"); // start, stop, restart
            Map<String, Object> result = edgeDeviceService.controlDevice(deviceId, action);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("控制设备失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
    
    /**
     * 分配摄像头到边缘设备
     */
    @PostMapping("/{deviceId}/assign-cameras")
    public ResponseEntity<Map<String, Object>> assignCameras(
            @PathVariable String deviceId,
            @RequestBody Map<String, Object> assignmentData) {
        
        try {
            @SuppressWarnings("unchecked")
            List<String> cameraIds = (List<String>) assignmentData.get("cameraIds");
            Map<String, Object> result = edgeDeviceService.assignCamerasToDevice(deviceId, cameraIds);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("分配摄像头失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
    
    /**
     * 负载均衡 - 重新分配摄像头
     */
    @PostMapping("/load-balance")
    public ResponseEntity<Map<String, Object>> rebalanceLoad() {
        try {
            Map<String, Object> result = edgeDeviceService.rebalanceCameraLoad();
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("负载均衡失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
    
    /**
     * 视频分析代理接口
     */
    @PostMapping("/video-analysis")
    public ResponseEntity<Map<String, Object>> analyzeVideo(
            @RequestParam("file") org.springframework.web.multipart.MultipartFile file,
            @RequestParam(value = "algorithms", defaultValue = "fall_detection") String algorithms) {
        
        try {
            Map<String, Object> result = edgeDeviceService.analyzeVideoWithEdgeService(file, algorithms);
            return ResponseEntity.ok(result);
        } catch (Exception e) {
            log.error("视频分析失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "error", e.getMessage()
            ));
        }
    }
    
    /**
     * 获取默认测试视频
     */
    @GetMapping("/default-videos/{filename}")
    public ResponseEntity<org.springframework.core.io.Resource> getDefaultVideo(@PathVariable String filename) {
        try {
            // 安全检查：只允许访问特定的测试视频
            if (!filename.matches("^[a-zA-Z0-9_-]+\\.(mp4|avi|mov)$")) {
                return ResponseEntity.badRequest().build();
            }
            
            // 查找视频文件
            java.nio.file.Path videoPath = java.nio.file.Paths.get("../mp4/" + filename);
            if (!java.nio.file.Files.exists(videoPath)) {
                // 如果文件不存在，返回404
                return ResponseEntity.notFound().build();
            }
            
            org.springframework.core.io.Resource resource = 
                new org.springframework.core.io.FileSystemResource(videoPath.toFile());
            
            return ResponseEntity.ok()
                    .header(org.springframework.http.HttpHeaders.CONTENT_DISPOSITION, 
                            "inline; filename=\"" + filename + "\"")
                    .contentType(org.springframework.http.MediaType.valueOf("video/mp4"))
                    .body(resource);
                    
        } catch (Exception e) {
            log.error("获取默认视频失败: {}", filename, e);
            return ResponseEntity.notFound().build();
        }
    }
}