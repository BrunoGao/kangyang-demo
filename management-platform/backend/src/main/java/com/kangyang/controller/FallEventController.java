package com.kangyang.controller;

import com.kangyang.entity.FallEvent;
import com.kangyang.service.FallEventService;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.data.domain.Page;
import org.springframework.data.domain.PageRequest;
import org.springframework.data.domain.Pageable;
import org.springframework.data.domain.Sort;
import org.springframework.format.annotation.DateTimeFormat;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.Map;

@Slf4j
@RestController
@RequestMapping("/api/events")
@RequiredArgsConstructor
@CrossOrigin(origins = "*")
public class FallEventController {
    
    private final FallEventService fallEventService;
    
    /**
     * 创建跌倒事件
     */
    @PostMapping
    public ResponseEntity<FallEvent> createEvent(@RequestBody FallEvent event) {
        try {
            FallEvent createdEvent = fallEventService.createEvent(event);
            return ResponseEntity.ok(createdEvent);
        } catch (Exception e) {
            log.error("创建跌倒事件失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 处理跌倒事件
     */
    @PutMapping("/{id}/handle")
    public ResponseEntity<FallEvent> handleEvent(
            @PathVariable Long id,
            @RequestParam String handler,
            @RequestParam(required = false) String remarks) {
        try {
            FallEvent handledEvent = fallEventService.handleEvent(id, handler, remarks);
            return ResponseEntity.ok(handledEvent);
        } catch (Exception e) {
            log.error("处理跌倒事件失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 分页查询跌倒事件
     */
    @GetMapping
    public ResponseEntity<Page<FallEvent>> getEvents(
            @RequestParam(defaultValue = "0") int page,
            @RequestParam(defaultValue = "20") int size,
            @RequestParam(defaultValue = "createdTime") String sortBy,
            @RequestParam(defaultValue = "desc") String sortDir,
            @RequestParam(required = false) Boolean isHandled,
            @RequestParam(required = false) String cameraId,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime startTime,
            @RequestParam(required = false) @DateTimeFormat(iso = DateTimeFormat.ISO.DATE_TIME) LocalDateTime endTime) {
        
        Sort sort = Sort.by(sortDir.equalsIgnoreCase("desc") ? Sort.Direction.DESC : Sort.Direction.ASC, sortBy);
        Pageable pageable = PageRequest.of(page, size, sort);
        
        Page<FallEvent> events;
        
        if (startTime != null && endTime != null) {
            events = fallEventService.getEventsByTimeRange(startTime, endTime, pageable);
        } else if (isHandled != null) {
            events = fallEventService.getEventsByHandled(isHandled, pageable);
        } else if (cameraId != null) {
            events = fallEventService.getEventsByCamera(cameraId, pageable);
        } else {
            events = fallEventService.getEvents(pageable);
        }
        
        return ResponseEntity.ok(events);
    }
    
    /**
     * 获取统计数据
     */
    @GetMapping("/statistics")
    public ResponseEntity<Map<String, Object>> getStatistics() {
        try {
            Map<String, Object> statistics = fallEventService.getStatistics();
            return ResponseEntity.ok(statistics);
        } catch (Exception e) {
            log.error("获取统计数据失败", e);
            return ResponseEntity.badRequest().build();
        }
    }
    
    /**
     * 根据ID获取事件详情
     */
    @GetMapping("/{id}")
    public ResponseEntity<FallEvent> getEventById(@PathVariable Long id) {
        return fallEventService.getEventById(id)
                .map(ResponseEntity::ok)
                .orElse(ResponseEntity.notFound().build());
    }
}