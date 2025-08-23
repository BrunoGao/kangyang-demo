package com.kangyang.repository;

import com.kangyang.entity.Camera;
import com.kangyang.entity.EdgeDevice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.data.repository.query.Param;
import org.springframework.stereotype.Repository;
import java.util.Optional;
import java.util.List;

@Repository
public interface CameraRepository extends JpaRepository<Camera, Long> {
    
    // 根据摄像头ID查询
    Optional<Camera> findByCameraId(String cameraId);
    
    // 查询活跃的摄像头
    List<Camera> findByIsActiveTrue();
    
    // 根据状态查询
    List<Camera> findByStatus(Camera.CameraStatus status);
    
    // 根据位置查询
    List<Camera> findByLocation(String location);
    
    // 根据边缘设备查询摄像头
    List<Camera> findByEdgeDevice(EdgeDevice edgeDevice);
    
    // 根据边缘设备ID查询摄像头
    List<Camera> findByEdgeDeviceId(Long edgeDeviceId);
    
    // 查询未分配给任何边缘设备的摄像头
    List<Camera> findByEdgeDeviceIsNull();
    
    // 统计每个设备的摄像头数量
    @Query("SELECT c.edgeDevice, COUNT(c) FROM Camera c WHERE c.edgeDevice IS NOT NULL GROUP BY c.edgeDevice")
    List<Object[]> countCamerasByDevice();
    
    // 查询启用了特定算法的摄像头
    List<Camera> findByFallDetectionEnabledTrue();
    
    List<Camera> findBySmokeDetectionEnabledTrue();
    
    List<Camera> findByFireDetectionEnabledTrue();
    
    // 统计各状态的摄像头数量
    @Query("SELECT c.status, COUNT(c) FROM Camera c GROUP BY c.status")
    List<Object[]> countCamerasByStatus();
}