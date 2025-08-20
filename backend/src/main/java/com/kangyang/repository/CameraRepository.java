package com.kangyang.repository;

import com.kangyang.entity.Camera;
import org.springframework.data.jpa.repository.JpaRepository;
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
    List<Camera> findByStatus(String status);
    
    // 根据位置查询
    List<Camera> findByLocation(String location);
}