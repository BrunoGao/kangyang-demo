package com.kangyang.repository;

import com.kangyang.entity.FallEvent;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.data.jpa.repository.JpaRepository;
import org.springframework.data.jpa.repository.Query;
import org.springframework.stereotype.Repository;
import java.time.LocalDateTime;
import java.util.List;

@Repository
public interface FallEventRepository extends JpaRepository<FallEvent, Long> {
    
    // 根据处理状态查询
    Page<FallEvent> findByIsHandled(Boolean isHandled, Pageable pageable);
    
    // 根据摄像头ID查询
    Page<FallEvent> findByCameraId(String cameraId, Pageable pageable);
    
    // 根据时间范围查询
    Page<FallEvent> findByCreatedTimeBetween(LocalDateTime startTime, LocalDateTime endTime, Pageable pageable);
    
    // 统计今日告警数量
    @Query("SELECT COUNT(e) FROM FallEvent e WHERE DATE(e.createdTime) = CURRENT_DATE")
    Long countTodayEvents();
    
    // 统计未处理告警数量
    Long countByIsHandled(Boolean isHandled);
    
    // 获取最近的告警事件
    List<FallEvent> findTop10ByOrderByCreatedTimeDesc();
    
    // 根据严重程度统计
    @Query("SELECT e.severity, COUNT(e) FROM FallEvent e GROUP BY e.severity")
    List<Object[]> countBySeverity();
}