package com.kangyang.service;

import com.kangyang.entity.FallEvent;
import com.kangyang.repository.FallEventRepository;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.Pageable;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Slf4j
@Service
@RequiredArgsConstructor
public class FallEventService {
    
    private final FallEventRepository fallEventRepository;
    
    /**
     * 创建跌倒事件
     */
    @Transactional
    public FallEvent createEvent(FallEvent event) {
        log.info("创建跌倒事件: {}", event);
        return fallEventRepository.save(event);
    }
    
    /**
     * 处理跌倒事件
     */
    @Transactional
    public FallEvent handleEvent(Long eventId, String handler, String remarks) {
        Optional<FallEvent> eventOpt = fallEventRepository.findById(eventId);
        if (eventOpt.isPresent()) {
            FallEvent event = eventOpt.get();
            event.setIsHandled(true);
            event.setHandler(handler);
            event.setRemarks(remarks);
            event.setHandleTime(LocalDateTime.now());
            return fallEventRepository.save(event);
        }
        throw new RuntimeException("跌倒事件不存在: " + eventId);
    }
    
    /**
     * 分页查询跌倒事件
     */
    public Page<FallEvent> getEvents(Pageable pageable) {
        return fallEventRepository.findAll(pageable);
    }
    
    /**
     * 根据处理状态查询
     */
    public Page<FallEvent> getEventsByHandled(Boolean isHandled, Pageable pageable) {
        return fallEventRepository.findByIsHandled(isHandled, pageable);
    }
    
    /**
     * 根据摄像头查询
     */
    public Page<FallEvent> getEventsByCamera(String cameraId, Pageable pageable) {
        return fallEventRepository.findByCameraId(cameraId, pageable);
    }
    
    /**
     * 根据时间范围查询
     */
    public Page<FallEvent> getEventsByTimeRange(LocalDateTime startTime, LocalDateTime endTime, Pageable pageable) {
        return fallEventRepository.findByCreatedTimeBetween(startTime, endTime, pageable);
    }
    
    /**
     * 获取统计数据
     */
    public Map<String, Object> getStatistics() {
        Map<String, Object> stats = new HashMap<>();
        
        // 今日告警数
        stats.put("todayEvents", fallEventRepository.countTodayEvents());
        
        // 未处理告警数
        stats.put("pendingEvents", fallEventRepository.countByIsHandled(false));
        
        // 总告警数
        stats.put("totalEvents", fallEventRepository.count());
        
        // 最近告警
        stats.put("recentEvents", fallEventRepository.findTop10ByOrderByCreatedTimeDesc());
        
        // 按严重程度统计
        List<Object[]> severityStats = fallEventRepository.countBySeverity();
        Map<String, Long> severityMap = new HashMap<>();
        for (Object[] stat : severityStats) {
            severityMap.put((String) stat[0], (Long) stat[1]);
        }
        stats.put("severityStats", severityMap);
        
        return stats;
    }
    
    /**
     * 根据ID获取事件
     */
    public Optional<FallEvent> getEventById(Long id) {
        return fallEventRepository.findById(id);
    }
}