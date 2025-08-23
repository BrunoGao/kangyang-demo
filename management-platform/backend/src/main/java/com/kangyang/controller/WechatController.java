package com.kangyang.controller;

import com.kangyang.service.WechatService;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.Map;

/**
 * 微信通知控制器
 * 提供微信通知测试和管理接口
 */
@Slf4j
@RestController
@RequestMapping("/api/wechat")
@CrossOrigin
public class WechatController {

    @Autowired
    private WechatService wechatService;

    /**
     * 获取微信配置信息
     */
    @GetMapping("/config")
    public ResponseEntity<Map<String, Object>> getWechatConfig() {
        Map<String, Object> config = wechatService.getWechatConfig();
        return ResponseEntity.ok(config);
    }

    /**
     * 测试Access Token
     */
    @PostMapping("/test-token")
    public ResponseEntity<Map<String, Object>> testAccessToken() {
        Map<String, Object> result = wechatService.testAccessToken();
        return ResponseEntity.ok(result);
    }

    /**
     * 测试微信连接
     */
    @PostMapping("/test")
    public ResponseEntity<Map<String, Object>> testWechatConnection() {
        boolean success = wechatService.testConnection();
        
        Map<String, Object> response = Map.of(
            "success", success,
            "message", success ? "微信通知测试成功" : "微信通知测试失败",
            "timestamp", LocalDateTime.now().format(DateTimeFormatter.ISO_LOCAL_DATE_TIME)
        );
        
        return ResponseEntity.ok(response);
    }

    /**
     * 发送自定义告警消息
     */
    @PostMapping("/alert")
    public ResponseEntity<Map<String, Object>> sendAlert(@RequestBody Map<String, String> request) {
        String message = request.get("message");
        if (message == null || message.trim().isEmpty()) {
            return ResponseEntity.badRequest().body(Map.of(
                "success", false,
                "message", "消息内容不能为空"
            ));
        }

        try {
            wechatService.sendAlert(message);
            return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "告警消息发送成功"
            ));
        } catch (Exception e) {
            log.error("发送告警消息失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "message", "告警消息发送失败: " + e.getMessage()
            ));
        }
    }

    /**
     * 发送跌倒告警
     */
    @PostMapping("/alert/fall")
    public ResponseEntity<Map<String, Object>> sendFallAlert(@RequestBody Map<String, String> request) {
        String personId = request.getOrDefault("personId", "未知人员");
        String location = request.getOrDefault("location", "未知位置");
        String severity = request.getOrDefault("severity", "MEDIUM");
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

        try {
            wechatService.sendFallAlert(personId, location, severity, timestamp);
            return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "跌倒告警发送成功",
                "personId", personId,
                "location", location,
                "severity", severity
            ));
        } catch (Exception e) {
            log.error("发送跌倒告警失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "message", "跌倒告警发送失败: " + e.getMessage()
            ));
        }
    }

    /**
     * 发送火灾告警
     */
    @PostMapping("/alert/fire")
    public ResponseEntity<Map<String, Object>> sendFireAlert(@RequestBody Map<String, String> request) {
        String location = request.getOrDefault("location", "未知位置");
        String intensity = request.getOrDefault("intensity", "medium");
        String temperature = request.getOrDefault("temperature", "300");
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

        try {
            wechatService.sendFireAlert(location, intensity, temperature, timestamp);
            return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "火灾告警发送成功",
                "location", location,
                "intensity", intensity,
                "temperature", temperature + "°C"
            ));
        } catch (Exception e) {
            log.error("发送火灾告警失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "message", "火灾告警发送失败: " + e.getMessage()
            ));
        }
    }

    /**
     * 发送烟雾告警
     */
    @PostMapping("/alert/smoke")
    public ResponseEntity<Map<String, Object>> sendSmokeAlert(@RequestBody Map<String, String> request) {
        String location = request.getOrDefault("location", "未知位置");
        String density = request.getOrDefault("density", "medium");
        String colorType = request.getOrDefault("colorType", "gray");
        String timestamp = LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"));

        try {
            wechatService.sendSmokeAlert(location, density, colorType, timestamp);
            return ResponseEntity.ok(Map.of(
                "success", true,
                "message", "烟雾告警发送成功",
                "location", location,
                "density", density,
                "colorType", colorType
            ));
        } catch (Exception e) {
            log.error("发送烟雾告警失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "message", "烟雾告警发送失败: " + e.getMessage()
            ));
        }
    }

    /**
     * 测试用户关注状态
     */
    @PostMapping("/test-user")
    public ResponseEntity<Map<String, Object>> testUserInfo(@RequestBody Map<String, String> request) {
        String openid = request.getOrDefault("openid", "ofYhV6W_mDuDnm8lVbgVbgEMtvWc");
        
        try {
            Map<String, Object> userInfo = wechatService.getUserInfo(openid);
            return ResponseEntity.ok(userInfo);
        } catch (Exception e) {
            log.error("获取用户信息失败", e);
            return ResponseEntity.ok(Map.of(
                "success", false,
                "message", "获取用户信息失败: " + e.getMessage(),
                "openid", openid
            ));
        }
    }
}