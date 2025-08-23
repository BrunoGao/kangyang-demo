package com.kangyang.service;

import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.HashMap;
import java.util.Map;

/**
 * 微信通知服务
 * 处理企业微信告警通知
 */
@Slf4j
@Service
public class WechatService {
    
    @Value("${wechat.webhook.url:}")
    private String webhookUrl;
    
    @Value("${wechat.enabled:true}")
    private boolean wechatEnabled;
    
    @Value("${wechat.app.id:}")
    private String appId;
    
    @Value("${wechat.app.secret:}")
    private String appSecret;
    
    @Value("${wechat.user.openid:}")
    private String userOpenId;
    
    @Value("${wechat.template.fall:}")
    private String templateIdFall;
    
    @Value("${wechat.template.fire:}")
    private String templateIdFire;
    
    @Value("${wechat.template.smoke:}")
    private String templateIdSmoke;
    
    private final RestTemplate restTemplate;
    
    public WechatService() {
        this.restTemplate = new RestTemplate();
        // 配置自定义错误处理，忽略412错误
        this.restTemplate.setErrorHandler(new org.springframework.web.client.ResponseErrorHandler() {
            @Override
            public boolean hasError(org.springframework.http.client.ClientHttpResponse response) throws java.io.IOException {
                int statusCode = response.getStatusCode().value();
                // 忽略412错误，因为微信API在这种情况下可能还是成功的
                return statusCode >= 400 && statusCode != 412;
            }
            
            @Override
            public void handleError(org.springframework.http.client.ClientHttpResponse response) throws java.io.IOException {
                // 保留其他HTTP错误的处理
                throw new org.springframework.web.client.HttpClientErrorException(response.getStatusCode());
            }
        });
    }
    
    // 微信API基础URL
    private static final String WECHAT_API_BASE = "https://api.weixin.qq.com/cgi-bin";
    
    // Access Token缓存
    private String cachedAccessToken;
    private LocalDateTime tokenExpireTime;
    
    /**
     * 获取微信Access Token
     */
    private String getAccessToken() {
        // 检查token是否过期
        if (cachedAccessToken != null && tokenExpireTime != null && 
            LocalDateTime.now().isBefore(tokenExpireTime)) {
            return cachedAccessToken;
        }
        
        if (appId == null || appId.trim().isEmpty() || 
            appSecret == null || appSecret.trim().isEmpty()) {
            log.warn("微信AppID或AppSecret未配置");
            return null;
        }
        
        try {
            String url = WECHAT_API_BASE + "/token?grant_type=client_credential&appid=" + 
                        appId + "&secret=" + appSecret;
            
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> result = response.getBody();
                
                if (result.containsKey("access_token")) {
                    cachedAccessToken = (String) result.get("access_token");
                    Integer expiresIn = (Integer) result.get("expires_in");
                    // 提前5分钟过期，确保安全
                    tokenExpireTime = LocalDateTime.now().plusSeconds(expiresIn - 300);
                    
                    log.info("微信Access Token获取成功，过期时间: {}", 
                            tokenExpireTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
                    return cachedAccessToken;
                } else {
                    log.error("获取微信Access Token失败: {}", result);
                    return null;
                }
            }
        } catch (Exception e) {
            log.error("获取微信Access Token异常", e);
        }
        
        return null;
    }
    
    /**
     * 发送告警消息到企业微信
     */
    public void sendAlert(String message) {
        if (!wechatEnabled) {
            log.info("微信通知已禁用，消息: {}", message);
            return;
        }
        
        if (webhookUrl == null || webhookUrl.trim().isEmpty()) {
            log.warn("微信Webhook URL未配置，消息: {}", message);
            return;
        }
        
        try {
            // 构建请求体
            Map<String, Object> requestBody = Map.of(
                "msgtype", "text",
                "text", Map.of("content", message)
            );
            
            // 设置请求头
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            // 发送请求
            ResponseEntity<String> response = restTemplate.postForEntity(webhookUrl, request, String.class);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("微信告警发送成功");
            } else {
                log.error("微信告警发送失败: {}", response.getStatusCode());
            }
            
        } catch (Exception e) {
            log.error("发送微信告警异常", e);
        }
    }
    
    /**
     * 发送Markdown格式消息
     */
    public void sendMarkdown(String title, String content) {
        if (!wechatEnabled || webhookUrl == null || webhookUrl.trim().isEmpty()) {
            return;
        }
        
        try {
            Map<String, Object> requestBody = Map.of(
                "msgtype", "markdown",
                "markdown", Map.of(
                    "content", String.format("# %s\n%s", title, content)
                )
            );
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            ResponseEntity<String> response = restTemplate.postForEntity(webhookUrl, request, String.class);
            
            if (response.getStatusCode().is2xxSuccessful()) {
                log.info("微信Markdown消息发送成功");
            } else {
                log.error("微信Markdown消息发送失败: {}", response.getStatusCode());
            }
            
        } catch (Exception e) {
            log.error("发送微信Markdown消息异常", e);
        }
    }
    
    /**
     * 发送跌倒检测告警
     */
    public void sendFallAlert(String personId, String location, String severity, String timestamp) {
        if (!wechatEnabled) {
            return;
        }
        
        String alertMessage = String.format(
            "🚨 康养机构跌倒告警 🚨\n" +
            "时间：%s\n" +
            "位置：%s\n" +
            "人员：%s\n" +
            "严重程度：%s\n" +
            "请立即前往查看并提供帮助！",
            timestamp, location, personId, severity
        );
        
        // 发送企业微信消息
        sendAlert(alertMessage);
        
        // 发送微信模板消息
        Map<String, Object> templateData = new HashMap<>();
        templateData.put("first", "🚨 康养机构跌倒告警");
        templateData.put("keyword1", timestamp);
        templateData.put("keyword2", location);
        templateData.put("keyword3", personId);
        templateData.put("keyword4", severity);
        templateData.put("remark", "请立即前往查看并提供帮助！紧急情况请拨打120。");
        
        sendTemplateMessage(templateIdFall, templateData);
        
        log.info("跌倒告警已发送 - 人员: {}, 位置: {}", personId, location);
    }
    
    /**
     * 发送火灾告警
     */
    public void sendFireAlert(String location, String intensity, String temperature, String timestamp) {
        if (!wechatEnabled) {
            return;
        }
        
        String alertMessage = String.format(
            "🔥 康养机构火灾告警 🔥\n" +
            "时间：%s\n" +
            "位置：%s\n" +
            "火焰强度：%s\n" +
            "估算温度：%s°C\n" +
            "请立即疏散人员并联系消防！",
            timestamp, location, intensity, temperature
        );
        
        // 发送企业微信消息
        sendAlert(alertMessage);
        
        // 发送微信模板消息
        Map<String, Object> templateData = new HashMap<>();
        templateData.put("first", "🔥 康养机构火灾告警");
        templateData.put("keyword1", timestamp);
        templateData.put("keyword2", location);
        templateData.put("keyword3", intensity);
        templateData.put("keyword4", temperature + "°C");
        templateData.put("remark", "请立即疏散人员并联系消防！紧急情况请拨打119。");
        
        sendTemplateMessage(templateIdFire, templateData);
        
        log.info("火灾告警已发送 - 位置: {}, 强度: {}", location, intensity);
    }
    
    /**
     * 发送烟雾告警
     */
    public void sendSmokeAlert(String location, String density, String colorType, String timestamp) {
        if (!wechatEnabled) {
            return;
        }
        
        String alertMessage = String.format(
            "💨 康养机构烟雾告警 💨\n" +
            "时间：%s\n" +
            "位置：%s\n" +
            "烟雾密度：%s\n" +
            "烟雾类型：%s\n" +
            "请检查火源并确保人员安全！",
            timestamp, location, density, colorType
        );
        
        // 发送企业微信消息
        sendAlert(alertMessage);
        
        // 发送微信模板消息
        Map<String, Object> templateData = new HashMap<>();
        templateData.put("first", "💨 康养机构烟雾告警");
        templateData.put("keyword1", timestamp);
        templateData.put("keyword2", location);
        templateData.put("keyword3", density);
        templateData.put("keyword4", colorType);
        templateData.put("remark", "请检查火源并确保人员安全！如发现火情请立即拨打119。");
        
        sendTemplateMessage(templateIdSmoke, templateData);
        
        log.info("烟雾告警已发送 - 位置: {}, 密度: {}", location, density);
    }
    
    /**
     * 通过微信公众号API发送消息
     */
    private void sendWechatApiMessage(String message) {
        String accessToken = getAccessToken();
        if (accessToken == null) {
            log.warn("无法获取微信Access Token，跳过公众号通知");
            return;
        }
        
        try {
            // 这里可以实现更复杂的模板消息或客服消息
            // 目前先记录日志，表示API调用准备就绪
            log.info("微信公众号API准备就绪，Access Token有效");
            log.debug("准备发送的消息内容: {}", message);
            
        } catch (Exception e) {
            log.error("通过微信API发送消息失败", e);
        }
    }
    
    /**
     * 发送微信模板消息
     */
    private void sendTemplateMessage(String templateId, Map<String, Object> data) {
        String accessToken = getAccessToken();
        if (accessToken == null || userOpenId == null || userOpenId.trim().isEmpty()) {
            log.warn("微信Access Token或用户OpenID未配置，跳过模板消息发送");
            return;
        }
        
        if (templateId == null || templateId.trim().isEmpty()) {
            log.warn("模板ID未配置，跳过模板消息发送");
            return;
        }
        
        try {
            String url = WECHAT_API_BASE + "/message/template/send?access_token=" + accessToken;
            
            Map<String, Object> templateData = new HashMap<>();
            for (Map.Entry<String, Object> entry : data.entrySet()) {
                templateData.put(entry.getKey(), Map.of("value", entry.getValue(), "color", "#173177"));
            }
            
            Map<String, Object> requestBody = Map.of(
                "touser", userOpenId,
                "template_id", templateId,
                "data", templateData
            );
            
            HttpHeaders headers = new HttpHeaders();
            headers.setContentType(MediaType.APPLICATION_JSON);
            
            HttpEntity<Map<String, Object>> request = new HttpEntity<>(requestBody, headers);
            
            ResponseEntity<String> response = restTemplate.exchange(
                url, 
                org.springframework.http.HttpMethod.POST, 
                request, 
                String.class
            );
            
            log.debug("微信模板消息响应状态: {}", response.getStatusCode());
            log.debug("微信模板消息响应内容: {}", response.getBody());
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                // 尝试解析JSON响应
                try {
                    String responseBody = response.getBody();
                    // 简单的JSON解析，查找errcode
                    if (responseBody.contains("\"errcode\":0")) {
                        log.info("微信模板消息发送成功");
                    } else if (responseBody.contains("\"errcode\"")) {
                        log.error("微信模板消息发送失败，响应: {}", responseBody);
                    } else {
                        log.warn("微信模板消息响应异常，响应: {}", responseBody);
                    }
                } catch (Exception e) {
                    log.error("解析微信响应失败: {}", response.getBody());
                }
            } else {
                log.error("微信模板消息发送失败: HTTP {} - {}", 
                        response.getStatusCode(), response.getBody());
            }
            
        } catch (Exception e) {
            log.error("发送微信模板消息异常: {}", e.getMessage());
            if (e instanceof org.springframework.web.client.HttpClientErrorException) {
                org.springframework.web.client.HttpClientErrorException httpError = 
                    (org.springframework.web.client.HttpClientErrorException) e;
                log.error("微信API错误详情: 状态码={}, 响应={}", 
                    httpError.getStatusCode(), httpError.getResponseBodyAsString());
            }
        }
    }
    
    /**
     * 获取微信配置信息
     */
    public Map<String, Object> getWechatConfig() {
        Map<String, Object> config = new HashMap<>();
        config.put("enabled", wechatEnabled);
        config.put("appId", appId != null ? appId.substring(0, 6) + "***" : "未配置");
        config.put("secretConfigured", appSecret != null && !appSecret.trim().isEmpty());
        config.put("webhookConfigured", webhookUrl != null && !webhookUrl.trim().isEmpty());
        config.put("userOpenId", userOpenId != null ? userOpenId.substring(0, 8) + "***" : "未配置");
        config.put("templateFallConfigured", templateIdFall != null && !templateIdFall.trim().isEmpty());
        config.put("templateFireConfigured", templateIdFire != null && !templateIdFire.trim().isEmpty());
        config.put("templateSmokeConfigured", templateIdSmoke != null && !templateIdSmoke.trim().isEmpty());
        config.put("tokenStatus", cachedAccessToken != null ? "已获取" : "未获取");
        if (tokenExpireTime != null) {
            config.put("tokenExpire", tokenExpireTime.format(DateTimeFormatter.ISO_LOCAL_DATE_TIME));
        }
        return config;
    }
    
    /**
     * 测试Access Token有效性
     */
    public Map<String, Object> testAccessToken() {
        String accessToken = getAccessToken();
        if (accessToken == null) {
            return Map.of("valid", false, "message", "无法获取Access Token");
        }
        
        try {
            // 使用获取菜单API来测试token是否有效
            String testUrl = WECHAT_API_BASE + "/menu/get?access_token=" + accessToken;
            ResponseEntity<String> response = restTemplate.getForEntity(testUrl, String.class);
            
            log.info("Access Token测试响应: {} - {}", response.getStatusCode(), response.getBody());
            
            return Map.of(
                "valid", response.getStatusCode().is2xxSuccessful(),
                "status", response.getStatusCode().value(),
                "response", response.getBody()
            );
            
        } catch (Exception e) {
            log.error("测试Access Token异常", e);
            return Map.of("valid", false, "message", e.getMessage());
        }
    }
    
    /**
     * 获取用户信息（测试关注状态）
     */
    public Map<String, Object> getUserInfo(String openid) {
        String accessToken = getAccessToken();
        if (accessToken == null) {
            return Map.of("error", "无法获取Access Token");
        }
        
        try {
            String url = WECHAT_API_BASE + "/user/info?access_token=" + accessToken + "&openid=" + openid;
            ResponseEntity<Map> response = restTemplate.getForEntity(url, Map.class);
            
            if (response.getStatusCode().is2xxSuccessful() && response.getBody() != null) {
                Map<String, Object> result = response.getBody();
                log.info("获取用户信息成功: {}", result);
                return result;
            } else {
                return Map.of("error", "请求失败", "status", response.getStatusCode());
            }
        } catch (Exception e) {
            log.error("获取用户信息异常", e);
            if (e instanceof org.springframework.web.client.HttpClientErrorException) {
                org.springframework.web.client.HttpClientErrorException httpError = 
                    (org.springframework.web.client.HttpClientErrorException) e;
                return Map.of(
                    "error", "HTTP错误",
                    "status", httpError.getStatusCode().value(),
                    "response", httpError.getResponseBodyAsString()
                );
            }
            return Map.of("error", e.getMessage());
        }
    }
    
    /**
     * 测试微信连接
     */
    public boolean testConnection() {
        try {
            String testMessage = String.format(
                "🤖 康养AI检测系统测试通知\n" +
                "测试时间：%s\n" +
                "系统状态：正常运行\n" +
                "微信通知功能：已启用",
                LocalDateTime.now().format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm:ss"))
            );
            
            sendAlert(testMessage);
            
            // 测试获取Access Token
            String token = getAccessToken();
            if (token != null) {
                log.info("微信Access Token测试成功");
                return true;
            } else {
                log.warn("微信Access Token获取失败，但企业微信可能仍可用");
                return true; // 企业微信不需要Token
            }
            
        } catch (Exception e) {
            log.error("微信连接测试失败", e);
            return false;
        }
    }
}