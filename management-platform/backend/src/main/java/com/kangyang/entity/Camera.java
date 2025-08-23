package com.kangyang.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import jakarta.persistence.*;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "cameras")
public class Camera {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "camera_id", unique = true, nullable = false)
    private String cameraId;
    
    @Column(name = "camera_name", nullable = false)
    private String cameraName;
    
    @Column(name = "location", nullable = false)
    private String location;
    
    @Column(name = "rtsp_url")
    private String rtspUrl;
    
    @Column(name = "is_active", nullable = false, columnDefinition = "boolean default true")
    private Boolean isActive = true;
    
    @Enumerated(EnumType.STRING)
    @Column(name = "status", nullable = false)
    private CameraStatus status = CameraStatus.OFFLINE;
    
    // 关联到边缘设备
    @ManyToOne(fetch = FetchType.LAZY)
    @JoinColumn(name = "edge_device_id")
    private EdgeDevice edgeDevice;
    
    // 启用的算法
    @Column(name = "fall_detection_enabled")
    private Boolean fallDetectionEnabled = true;
    
    @Column(name = "smoke_detection_enabled")
    private Boolean smokeDetectionEnabled = false;
    
    @Column(name = "fire_detection_enabled")
    private Boolean fireDetectionEnabled = false;
    
    // 性能指标
    @Column(name = "current_fps")
    private Double currentFps = 0.0;
    
    @Column(name = "frame_count")
    private Long frameCount = 0L;
    
    @Column(name = "detection_count")
    private Long detectionCount = 0L;
    
    @Column(name = "last_frame_time")
    private LocalDateTime lastFrameTime;
    
    @Column(name = "last_heartbeat")
    private LocalDateTime lastHeartbeat;
    
    @Column(name = "created_time", nullable = false)
    private LocalDateTime createdTime;
    
    @Column(name = "updated_time")
    private LocalDateTime updatedTime;
    
    @PrePersist
    protected void onCreate() {
        createdTime = LocalDateTime.now();
        updatedTime = LocalDateTime.now();
        lastHeartbeat = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedTime = LocalDateTime.now();
    }
    
    public enum CameraStatus {
        ONLINE("在线"),
        OFFLINE("离线"),
        RECORDING("录制中"),
        ERROR("错误"),
        MAINTENANCE("维护中");
        
        private final String displayName;
        
        CameraStatus(String displayName) {
            this.displayName = displayName;
        }
        
        public String getDisplayName() {
            return displayName;
        }
    }
}