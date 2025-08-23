package com.kangyang.repository;

import com.kangyang.entity.EdgeDevice;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Optional;

/**
 * 边缘设备数据访问接口
 */
@Repository
public interface EdgeDeviceRepository extends JpaRepository<EdgeDevice, Long> {
    
    /**
     * 根据设备ID查找设备
     */
    Optional<EdgeDevice> findByDeviceId(String deviceId);
    
    /**
     * 查找所有在线设备
     */
    List<EdgeDevice> findByStatus(EdgeDevice.DeviceStatus status);
    
    /**
     * 查找指定时间后有心跳的设备
     */
    @Query("SELECT e FROM EdgeDevice e WHERE e.lastHeartbeat > :since")
    List<EdgeDevice> findActiveDevicesSince(LocalDateTime since);
    
    /**
     * 统计各种状态的设备数量
     */
    @Query("SELECT e.status, COUNT(e) FROM EdgeDevice e GROUP BY e.status")
    List<Object[]> countDevicesByStatus();
    
    /**
     * 查找长时间未心跳的设备
     */
    @Query("SELECT e FROM EdgeDevice e WHERE e.lastHeartbeat < :threshold OR e.lastHeartbeat IS NULL")
    List<EdgeDevice> findDevicesWithoutHeartbeat(LocalDateTime threshold);
}