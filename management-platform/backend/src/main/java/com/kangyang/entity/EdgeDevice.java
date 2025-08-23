package com.kangyang.entity;

import jakarta.persistence.*;
import lombok.Data;
import java.time.LocalDateTime;

/**
 * 边缘设备实体类
 */
@Data
@Entity
@Table(name = "edge_devices")
public class EdgeDevice {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(unique = true, nullable = false)
    private String deviceId;
    
    @Column(nullable = false)
    private String deviceName;
    
    @Column(nullable = false)
    private String ipAddress;
    
    @Column(nullable = false)
    private Integer port;
    
    @Enumerated(EnumType.STRING)
    @Column(nullable = false)
    private DeviceStatus status;
    
    @Column(columnDefinition = "TEXT")
    private String configuration;
    
    private String version;
    
    private LocalDateTime lastHeartbeat;
    
    private LocalDateTime createdAt;
    
    private LocalDateTime updatedAt;
    
    // 算法配置
    private Boolean fallDetectionEnabled = true;
    
    private Boolean smokeDetectionEnabled = false;
    
    private Boolean fireDetectionEnabled = false;
    
    private Double fallConfidenceThreshold = 0.8;
    
    private Double smokeConfidenceThreshold = 0.7;
    
    private Double fireConfidenceThreshold = 0.9;
    
    // 摄像头管理
    private Integer maxCameras = 11;
    
    private Integer activeCameras = 0;
    
    // 性能监控
    private Double cpuUsage = 0.0;
    
    private Double memoryUsage = 0.0;
    
    private Double averageFps = 0.0;
    
    private Long totalDetections = 0L;
    
    @PrePersist
    protected void onCreate() {
        createdAt = LocalDateTime.now();
        updatedAt = LocalDateTime.now();
        if (status == null) {
            status = DeviceStatus.OFFLINE;
        }
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedAt = LocalDateTime.now();
    }
    
    public enum DeviceStatus {
        ONLINE("在线"),
        OFFLINE("离线"), 
        ERROR("错误"),
        MAINTENANCE("维护中");
        
        private final String displayName;
        
        DeviceStatus(String displayName) {
            this.displayName = displayName;
        }
        
        public String getDisplayName() {
            return displayName;
        }
    }
}