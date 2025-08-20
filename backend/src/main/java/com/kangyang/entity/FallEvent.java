package com.kangyang.entity;

import lombok.Data;
import lombok.NoArgsConstructor;
import lombok.AllArgsConstructor;
import javax.persistence.*;
import java.time.LocalDateTime;

@Data
@NoArgsConstructor
@AllArgsConstructor
@Entity
@Table(name = "fall_events")
public class FallEvent {
    
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;
    
    @Column(name = "person_id", nullable = false)
    private String personId;
    
    @Column(name = "camera_id", nullable = false)
    private String cameraId;
    
    @Column(name = "event_type", nullable = false)
    private String eventType; // fall_detected, prolonged_fall
    
    @Column(name = "severity", nullable = false)
    private String severity; // immediate, critical
    
    @Column(name = "body_angle")
    private Double bodyAngle;
    
    @Column(name = "duration")
    private Double duration;
    
    @Column(name = "location")
    private String location;
    
    @Column(name = "is_handled", nullable = false, columnDefinition = "boolean default false")
    private Boolean isHandled = false;
    
    @Column(name = "handler")
    private String handler;
    
    @Column(name = "handle_time")
    private LocalDateTime handleTime;
    
    @Column(name = "remarks")
    private String remarks;
    
    @Column(name = "created_time", nullable = false)
    private LocalDateTime createdTime;
    
    @Column(name = "updated_time")
    private LocalDateTime updatedTime;
    
    @PrePersist
    protected void onCreate() {
        createdTime = LocalDateTime.now();
        updatedTime = LocalDateTime.now();
    }
    
    @PreUpdate
    protected void onUpdate() {
        updatedTime = LocalDateTime.now();
    }
}