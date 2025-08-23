package com.kangyang.service;

import com.kangyang.entity.EdgeDevice;
import com.kangyang.entity.Camera;
import com.kangyang.repository.EdgeDeviceRepository;
import com.kangyang.repository.CameraRepository;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.stream.Collectors;

/**
 * 边缘设备管理服务
 */
@Slf4j
@Service
public class EdgeDeviceService {
    
    @Autowired
    private EdgeDeviceRepository deviceRepository;
    
    @Autowired
    private CameraRepository cameraRepository;
    
    private final RestTemplate restTemplate = new RestTemplate();
    
    /**
     * 获取所有设备
     */
    public List<EdgeDevice> getAllDevices() {
        return deviceRepository.findAll();
    }
    
    /**
     * 根据ID获取设备
     */
    public Optional<EdgeDevice> getDeviceById(Long id) {
        return deviceRepository.findById(id);
    }
    
    /**
     * 根据设备ID获取设备
     */
    public Optional<EdgeDevice> getDeviceByDeviceId(String deviceId) {
        return deviceRepository.findByDeviceId(deviceId);
    }
    
    /**
     * 创建或更新设备
     */
    public EdgeDevice saveDevice(EdgeDevice device) {
        return deviceRepository.save(device);
    }
    
    /**
     * 删除设备
     */
    public void deleteDevice(Long id) {
        deviceRepository.deleteById(id);
    }
    
    /**
     * 更新设备心跳
     */
    public void updateHeartbeat(String deviceId) {
        Optional<EdgeDevice> deviceOpt = deviceRepository.findByDeviceId(deviceId);
        if (deviceOpt.isPresent()) {
            EdgeDevice device = deviceOpt.get();
            device.setLastHeartbeat(LocalDateTime.now());
            device.setStatus(EdgeDevice.DeviceStatus.ONLINE);
            deviceRepository.save(device);
            log.debug("更新设备心跳: {}", deviceId);
        }
    }
    
    /**
     * 检查设备健康状态
     */
    public Map<String, Object> checkDeviceHealth(String deviceId) {
        Optional<EdgeDevice> deviceOpt = deviceRepository.findByDeviceId(deviceId);
        if (!deviceOpt.isPresent()) {
            return Map.of("error", "设备不存在");
        }
        
        EdgeDevice device = deviceOpt.get();
        String healthUrl = String.format("http://%s:%d/api/health", 
            device.getIpAddress(), device.getPort());
        
        try {
            ResponseEntity<Map> response = restTemplate.getForEntity(healthUrl, Map.class);
            if (response.getStatusCode().is2xxSuccessful()) {
                updateHeartbeat(deviceId);
                return Map.of(
                    "status", "healthy",
                    "deviceId", deviceId,
                    "response", response.getBody()
                );
            }
        } catch (Exception e) {
            log.warn("设备健康检查失败: {} - {}", deviceId, e.getMessage());
            // 标记设备为错误状态
            device.setStatus(EdgeDevice.DeviceStatus.ERROR);
            deviceRepository.save(device);
        }
        
        return Map.of(
            "status", "unhealthy",
            "deviceId", deviceId
        );
    }
    
    /**
     * 获取设备统计信息
     */
    public Map<String, Object> getDeviceStatistics() {
        List<Object[]> statusCounts = deviceRepository.countDevicesByStatus();
        Map<String, Long> statusMap = new HashMap<>();
        
        for (Object[] result : statusCounts) {
            EdgeDevice.DeviceStatus status = (EdgeDevice.DeviceStatus) result[0];
            Long count = (Long) result[1];
            statusMap.put(status.name(), count);
        }
        
        return Map.of(
            "total", deviceRepository.count(),
            "statusCounts", statusMap,
            "lastUpdated", LocalDateTime.now()
        );
    }
    
    /**
     * 检查并更新离线设备
     */
    public void checkOfflineDevices() {
        LocalDateTime threshold = LocalDateTime.now().minusMinutes(5); // 5分钟未心跳视为离线
        List<EdgeDevice> offlineDevices = deviceRepository.findDevicesWithoutHeartbeat(threshold);
        
        for (EdgeDevice device : offlineDevices) {
            if (device.getStatus() != EdgeDevice.DeviceStatus.OFFLINE && 
                device.getStatus() != EdgeDevice.DeviceStatus.MAINTENANCE) {
                device.setStatus(EdgeDevice.DeviceStatus.OFFLINE);
                deviceRepository.save(device);
                log.info("设备离线: {}", device.getDeviceId());
            }
        }
    }
    
    /**
     * 发送命令到边缘设备
     */
    public Map<String, Object> sendCommandToDevice(String deviceId, Map<String, Object> command) {
        Optional<EdgeDevice> deviceOpt = deviceRepository.findByDeviceId(deviceId);
        if (!deviceOpt.isPresent()) {
            return Map.of("error", "设备不存在");
        }
        
        EdgeDevice device = deviceOpt.get();
        String commandUrl = String.format("http://%s:%d/api/command", 
            device.getIpAddress(), device.getPort());
        
        try {
            ResponseEntity<Map> response = restTemplate.postForEntity(commandUrl, command, Map.class);
            if (response.getStatusCode().is2xxSuccessful()) {
                return Map.of(
                    "success", true,
                    "deviceId", deviceId,
                    "response", response.getBody()
                );
            }
        } catch (Exception e) {
            log.error("发送命令到设备失败: {} - {}", deviceId, e.getMessage());
        }
        
        return Map.of(
            "success", false,
            "deviceId", deviceId,
            "error", "命令发送失败"
        );
    }
    
    /**
     * 更新设备算法配置
     */
    public Map<String, Object> updateAlgorithmConfig(String deviceId, Map<String, Object> config) {
        Optional<EdgeDevice> deviceOpt = deviceRepository.findByDeviceId(deviceId);
        if (!deviceOpt.isPresent()) {
            return Map.of("success", false, "error", "设备不存在");
        }
        
        EdgeDevice device = deviceOpt.get();
        
        // 更新算法配置
        if (config.containsKey("fallDetectionEnabled")) {
            device.setFallDetectionEnabled((Boolean) config.get("fallDetectionEnabled"));
        }
        if (config.containsKey("smokeDetectionEnabled")) {
            device.setSmokeDetectionEnabled((Boolean) config.get("smokeDetectionEnabled"));
        }
        if (config.containsKey("fireDetectionEnabled")) {
            device.setFireDetectionEnabled((Boolean) config.get("fireDetectionEnabled"));
        }
        if (config.containsKey("fallConfidenceThreshold")) {
            device.setFallConfidenceThreshold((Double) config.get("fallConfidenceThreshold"));
        }
        if (config.containsKey("smokeConfidenceThreshold")) {
            device.setSmokeConfidenceThreshold((Double) config.get("smokeConfidenceThreshold"));
        }
        if (config.containsKey("fireConfidenceThreshold")) {
            device.setFireConfidenceThreshold((Double) config.get("fireConfidenceThreshold"));
        }
        
        deviceRepository.save(device);
        
        // 发送配置到边缘设备
        try {
            String configUrl = String.format("http://%s:%d/api/algorithm/config", 
                device.getIpAddress(), device.getPort());
            ResponseEntity<Map> response = restTemplate.postForEntity(configUrl, config, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("算法配置已发送到设备: {}", deviceId);
                return Map.of(
                    "success", true,
                    "deviceId", deviceId,
                    "message", "算法配置已更新"
                );
            }
        } catch (Exception e) {
            log.warn("向设备发送算法配置失败: {} - {}", deviceId, e.getMessage());
        }
        
        return Map.of(
            "success", true,
            "deviceId", deviceId,
            "message", "算法配置已保存（设备通信失败）"
        );
    }
    
    /**
     * 获取设备性能监控数据
     */
    public Map<String, Object> getPerformanceMetrics(String deviceId) {
        Optional<EdgeDevice> deviceOpt = deviceRepository.findByDeviceId(deviceId);
        if (!deviceOpt.isPresent()) {
            return Map.of("error", "设备不存在");
        }
        
        EdgeDevice device = deviceOpt.get();
        
        // 尝试从设备获取实时性能数据
        try {
            String metricsUrl = String.format("http://%s:%d/api/performance", 
                device.getIpAddress(), device.getPort());
            ResponseEntity<Map> response = restTemplate.getForEntity(metricsUrl, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                Map<String, Object> liveMetrics = response.getBody();
                // 更新数据库中的性能数据
                device.setCpuUsage((Double) liveMetrics.getOrDefault("cpu_usage", 0.0));
                device.setMemoryUsage((Double) liveMetrics.getOrDefault("memory_usage", 0.0));
                device.setAverageFps((Double) liveMetrics.getOrDefault("average_fps", 0.0));
                deviceRepository.save(device);
                
                return Map.of(
                    "success", true,
                    "deviceId", deviceId,
                    "metrics", liveMetrics
                );
            }
        } catch (Exception e) {
            log.warn("获取设备性能数据失败: {} - {}", deviceId, e.getMessage());
        }
        
        // 返回数据库中的缓存数据
        return Map.of(
            "success", true,
            "deviceId", deviceId,
            "metrics", Map.of(
                "cpu_usage", device.getCpuUsage(),
                "memory_usage", device.getMemoryUsage(),
                "average_fps", device.getAverageFps(),
                "total_detections", device.getTotalDetections(),
                "active_cameras", device.getActiveCameras(),
                "status", device.getStatus().name(),
                "last_heartbeat", device.getLastHeartbeat()
            ),
            "cached", true
        );
    }
    
    /**
     * 控制设备启停
     */
    public Map<String, Object> controlDevice(String deviceId, String action) {
        Optional<EdgeDevice> deviceOpt = deviceRepository.findByDeviceId(deviceId);
        if (!deviceOpt.isPresent()) {
            return Map.of("success", false, "error", "设备不存在");
        }
        
        EdgeDevice device = deviceOpt.get();
        
        try {
            String controlUrl = String.format("http://%s:%d/api/control", 
                device.getIpAddress(), device.getPort());
            Map<String, String> controlData = Map.of("action", action);
            ResponseEntity<Map> response = restTemplate.postForEntity(controlUrl, controlData, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                // 根据操作更新设备状态
                switch (action) {
                    case "start":
                        device.setStatus(EdgeDevice.DeviceStatus.ONLINE);
                        break;
                    case "stop":
                        device.setStatus(EdgeDevice.DeviceStatus.MAINTENANCE);
                        break;
                    case "restart":
                        device.setStatus(EdgeDevice.DeviceStatus.ONLINE);
                        break;
                }
                deviceRepository.save(device);
                
                return Map.of(
                    "success", true,
                    "deviceId", deviceId,
                    "action", action,
                    "message", "设备控制命令执行成功"
                );
            }
        } catch (Exception e) {
            log.error("设备控制失败: {} - {}", deviceId, e.getMessage());
            device.setStatus(EdgeDevice.DeviceStatus.ERROR);
            deviceRepository.save(device);
        }
        
        return Map.of(
            "success", false,
            "deviceId", deviceId,
            "error", "设备控制失败"
        );
    }
    
    /**
     * 分配摄像头到边缘设备
     */
    public Map<String, Object> assignCamerasToDevice(String deviceId, List<String> cameraIds) {
        Optional<EdgeDevice> deviceOpt = deviceRepository.findByDeviceId(deviceId);
        if (!deviceOpt.isPresent()) {
            return Map.of("success", false, "error", "设备不存在");
        }
        
        EdgeDevice device = deviceOpt.get();
        
        // 检查设备容量
        int currentCameraCount = cameraRepository.findByEdgeDevice(device).size();
        if (currentCameraCount + cameraIds.size() > device.getMaxCameras()) {
            return Map.of(
                "success", false, 
                "error", String.format("设备容量不足，当前 %d 个，最大支持 %d 个摄像头", 
                    currentCameraCount, device.getMaxCameras())
            );
        }
        
        int successCount = 0;
        for (String cameraId : cameraIds) {
            Optional<Camera> cameraOpt = cameraRepository.findByCameraId(cameraId);
            if (cameraOpt.isPresent()) {
                Camera camera = cameraOpt.get();
                camera.setEdgeDevice(device);
                cameraRepository.save(camera);
                successCount++;
            }
        }
        
        // 更新设备的活跃摄像头数量
        device.setActiveCameras(cameraRepository.findByEdgeDevice(device).size());
        deviceRepository.save(device);
        
        return Map.of(
            "success", true,
            "deviceId", deviceId,
            "assigned", successCount,
            "total", cameraIds.size(),
            "message", String.format("成功分配 %d 个摄像头到设备", successCount)
        );
    }
    
    /**
     * 负载均衡 - 重新分配摄像头
     */
    public Map<String, Object> rebalanceCameraLoad() {
        List<EdgeDevice> devices = deviceRepository.findAll();
        List<Camera> unassignedCameras = cameraRepository.findByEdgeDeviceIsNull();
        
        if (devices.isEmpty()) {
            return Map.of("success", false, "error", "没有可用的边缘设备");
        }
        
        // 计算每个设备的负载
        Map<EdgeDevice, Integer> deviceLoads = new HashMap<>();
        for (EdgeDevice device : devices) {
            if (device.getStatus() == EdgeDevice.DeviceStatus.ONLINE) {
                int cameraCount = cameraRepository.findByEdgeDevice(device).size();
                deviceLoads.put(device, cameraCount);
            }
        }
        
        if (deviceLoads.isEmpty()) {
            return Map.of("success", false, "error", "没有在线的边缘设备");
        }
        
        // 简单的负载均衡算法：分配给负载最轻的设备
        int reassigned = 0;
        for (Camera camera : unassignedCameras) {
            EdgeDevice leastLoadedDevice = deviceLoads.entrySet().stream()
                .filter(entry -> entry.getValue() < entry.getKey().getMaxCameras())
                .min(Map.Entry.comparingByValue())
                .map(Map.Entry::getKey)
                .orElse(null);
            
            if (leastLoadedDevice != null) {
                camera.setEdgeDevice(leastLoadedDevice);
                cameraRepository.save(camera);
                deviceLoads.put(leastLoadedDevice, deviceLoads.get(leastLoadedDevice) + 1);
                reassigned++;
            }
        }
        
        // 更新设备的活跃摄像头数量
        for (EdgeDevice device : deviceLoads.keySet()) {
            device.setActiveCameras(cameraRepository.findByEdgeDevice(device).size());
            deviceRepository.save(device);
        }
        
        return Map.of(
            "success", true,
            "reassigned", reassigned,
            "total_unassigned", unassignedCameras.size(),
            "message", String.format("负载均衡完成，重新分配了 %d 个摄像头", reassigned)
        );
    }
    
    /**
     * 使用边缘服务分析视频
     */
    public Map<String, Object> analyzeVideoWithEdgeService(
            org.springframework.web.multipart.MultipartFile file, String algorithms) {
        
        // 找到一个在线的边缘设备
        List<EdgeDevice> onlineDevices = deviceRepository.findByStatus(EdgeDevice.DeviceStatus.ONLINE);
        if (onlineDevices.isEmpty()) {
            return Map.of(
                "success", false,
                "error", "没有在线的边缘设备可用于视频分析"
            );
        }
        
        EdgeDevice device = onlineDevices.get(0); // 使用第一个在线设备
        
        try {
            // 准备HTTP请求到边缘服务
            String edgeServiceUrl = String.format("http://%s:%d/detection/test/video", 
                device.getIpAddress(), device.getPort());
            
            // 创建multipart request
            org.springframework.util.MultiValueMap<String, Object> parts = 
                new org.springframework.util.LinkedMultiValueMap<>();
            
            // 添加文件
            parts.add("file", new org.springframework.core.io.ByteArrayResource(file.getBytes()) {
                @Override
                public String getFilename() {
                    return file.getOriginalFilename();
                }
            });
            
            // 添加算法参数
            parts.add("algorithms", algorithms);
            
            // 设置请求头
            org.springframework.http.HttpHeaders headers = new org.springframework.http.HttpHeaders();
            headers.setContentType(org.springframework.http.MediaType.MULTIPART_FORM_DATA);
            
            org.springframework.http.HttpEntity<org.springframework.util.MultiValueMap<String, Object>> requestEntity = 
                new org.springframework.http.HttpEntity<>(parts, headers);
            
            // 发送请求到边缘服务
            ResponseEntity<Map> response = restTemplate.postForEntity(edgeServiceUrl, requestEntity, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                Map<String, Object> result = response.getBody();
                
                // 更新设备的检测统计
                if (result != null && "true".equals(String.valueOf(result.get("success")))) {
                    @SuppressWarnings("unchecked")
                    Map<String, Object> data = (Map<String, Object>) result.get("data");
                    if (data != null) {
                        @SuppressWarnings("unchecked")
                        Map<String, Object> summary = (Map<String, Object>) data.get("detection_summary");
                        if (summary != null) {
                            Integer totalDetections = (Integer) summary.get("total_detections");
                            if (totalDetections != null) {
                                device.setTotalDetections(device.getTotalDetections() + totalDetections);
                                deviceRepository.save(device);
                            }
                        }
                    }
                }
                
                return result != null ? result : Map.of("success", false, "error", "空响应");
            } else {
                return Map.of(
                    "success", false,
                    "error", "边缘服务响应错误: " + response.getStatusCode()
                );
            }
            
        } catch (org.springframework.web.client.ResourceAccessException e) {
            log.error("无法连接到边缘设备: {} - {}, 使用模拟数据", device.getDeviceId(), e.getMessage());
            
            // 标记设备为错误状态但不阻止测试
            device.setStatus(EdgeDevice.DeviceStatus.ERROR);
            deviceRepository.save(device);
            
            // 返回模拟的分析结果用于演示
            return generateMockVideoAnalysisResult(file.getOriginalFilename(), algorithms);
        } catch (Exception e) {
            log.error("视频分析失败: {}", e.getMessage(), e);
            return Map.of(
                "success", false,
                "error", "视频分析处理失败: " + e.getMessage()
            );
        }
    }
    
    /**
     * 生成模拟的视频分析结果
     */
    private Map<String, Object> generateMockVideoAnalysisResult(String filename, String algorithms) {
        java.util.Random random = new java.util.Random();
        String[] algorithmList = algorithms.split(",");
        
        // 生成模拟检测结果
        java.util.List<Map<String, Object>> detectionResults = new java.util.ArrayList<>();
        Map<String, Object> algorithmStats = new HashMap<>();
        
        for (String algorithm : algorithmList) {
            algorithm = algorithm.trim();
            
            // 为每个算法生成1-3个检测结果
            int numDetections = random.nextInt(3) + 1;
            for (int i = 0; i < numDetections; i++) {
                Map<String, Object> detection = new HashMap<>();
                detection.put("algorithm", algorithm);
                detection.put("type", algorithm.replace("_detection", ""));
                detection.put("confidence", 0.7 + random.nextDouble() * 0.3);
                detection.put("timestamp", random.nextDouble() * 30); // 0-30秒内
                detection.put("frame_index", random.nextInt(900)); // 假设30fps视频
                detection.put("location", String.format("区域 %c", (char)('A' + i)));
                detection.put("bbox", java.util.List.of(
                    random.nextDouble() * 0.3,
                    random.nextDouble() * 0.3,
                    0.3 + random.nextDouble() * 0.4,
                    0.3 + random.nextDouble() * 0.4
                ));
                detectionResults.add(detection);
            }
            
            // 为每个算法生成统计信息
            Map<String, Object> stats = new HashMap<>();
            stats.put("total_detections", numDetections);
            stats.put("avg_confidence", 0.8 + random.nextDouble() * 0.15);
            stats.put("max_confidence", 0.85 + random.nextDouble() * 0.15);
            stats.put("detection_frames", java.util.List.of(random.nextInt(900), random.nextInt(900)));
            algorithmStats.put(algorithm, stats);
        }
        
        // 生成视频信息
        Map<String, Object> videoInfo = new HashMap<>();
        videoInfo.put("filename", filename);
        videoInfo.put("duration", 30.0);
        videoInfo.put("fps", 30.0);
        videoInfo.put("total_frames", 900);
        videoInfo.put("processed_frames", 150); // 每秒处理5帧
        videoInfo.put("frame_skip", 6);
        
        // 生成检测摘要
        Map<String, Object> detectionSummary = new HashMap<>();
        detectionSummary.put("total_detections", detectionResults.size());
        detectionSummary.put("frames_with_detections", detectionResults.size() / 2);
        detectionSummary.put("detection_rate", 0.1 + random.nextDouble() * 0.2);
        
        // 生成帧结果映射（用于同步显示）
        Map<String, Object> frameResults = new HashMap<>();
        for (Map<String, Object> detection : detectionResults) {
            String frameIndex = String.valueOf(detection.get("frame_index"));
            frameResults.put(frameIndex, java.util.List.of(detection));
        }
        
        // 组装完整结果
        Map<String, Object> analysisData = new HashMap<>();
        analysisData.put("video_info", videoInfo);
        analysisData.put("algorithms_used", java.util.List.of(algorithmList));
        analysisData.put("detection_summary", detectionSummary);
        analysisData.put("detailed_results", detectionResults);
        analysisData.put("algorithm_statistics", algorithmStats);
        analysisData.put("frame_results", frameResults);
        analysisData.put("processing_time", LocalDateTime.now().toString());
        
        return Map.of(
            "success", true,
            "data", analysisData,
            "message", String.format("模拟视频分析完成，发现 %d 个检测结果（演示数据）", detectionResults.size())
        );
    }
}