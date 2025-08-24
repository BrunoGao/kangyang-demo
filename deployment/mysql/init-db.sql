-- 康养AI检测系统数据库初始化脚本

-- 设置字符集
SET NAMES utf8mb4;
SET FOREIGN_KEY_CHECKS = 0;

-- 创建边缘控制器表
CREATE TABLE `edge_controllers` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `controller_id` varchar(100) NOT NULL COMMENT '控制器唯一标识',
  `controller_name` varchar(200) NOT NULL COMMENT '控制器名称',
  `ip_address` varchar(45) NOT NULL COMMENT 'IP地址',
  `status` enum('online','offline','error') NOT NULL DEFAULT 'offline' COMMENT '状态',
  `last_heartbeat` datetime DEFAULT NULL COMMENT '最后心跳时间',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_controller_id` (`controller_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='边缘控制器表';

-- 创建摄像头表
CREATE TABLE `cameras` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `camera_id` varchar(100) NOT NULL COMMENT '摄像头唯一标识',
  `camera_name` varchar(200) NOT NULL COMMENT '摄像头名称',
  `rtsp_url` varchar(500) NOT NULL COMMENT 'RTSP流地址',
  `location` varchar(200) DEFAULT NULL COMMENT '位置描述',
  `controller_id` varchar(100) NOT NULL COMMENT '所属控制器ID',
  `enabled_algorithms` json DEFAULT NULL COMMENT '启用的算法列表',
  `status` enum('active','inactive','error') NOT NULL DEFAULT 'inactive' COMMENT '状态',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_camera_id` (`camera_id`),
  KEY `idx_controller_id` (`controller_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='摄像头表';

-- 创建检测事件表
CREATE TABLE `detection_events` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `event_id` varchar(100) NOT NULL COMMENT '事件唯一标识',
  `event_type` enum('fall','fire','smoke') NOT NULL COMMENT '事件类型',
  `camera_id` varchar(100) NOT NULL COMMENT '摄像头ID',
  `controller_id` varchar(100) NOT NULL COMMENT '控制器ID',
  `confidence` float NOT NULL COMMENT '置信度',
  `bbox_left` float DEFAULT NULL COMMENT '边界框左上角X',
  `bbox_top` float DEFAULT NULL COMMENT '边界框左上角Y',
  `bbox_width` float DEFAULT NULL COMMENT '边界框宽度',
  `bbox_height` float DEFAULT NULL COMMENT '边界框高度',
  `metadata` json DEFAULT NULL COMMENT '事件元数据',
  `image_path` varchar(500) DEFAULT NULL COMMENT '快照图片路径',
  `video_path` varchar(500) DEFAULT NULL COMMENT '视频片段路径',
  `severity` enum('low','medium','high','critical') NOT NULL DEFAULT 'medium' COMMENT '严重程度',
  `status` enum('pending','processing','resolved','ignored') NOT NULL DEFAULT 'pending' COMMENT '处理状态',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_event_id` (`event_id`),
  KEY `idx_event_type` (`event_type`),
  KEY `idx_camera_id` (`camera_id`),
  KEY `idx_controller_id` (`controller_id`),
  KEY `idx_created_at` (`created_at`),
  KEY `idx_status` (`status`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='检测事件表';

-- 创建告警记录表
CREATE TABLE `alert_records` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `alert_id` varchar(100) NOT NULL COMMENT '告警唯一标识',
  `event_id` varchar(100) NOT NULL COMMENT '关联事件ID',
  `alert_type` enum('wechat','sms','email','system') NOT NULL COMMENT '告警类型',
  `recipient` varchar(500) NOT NULL COMMENT '接收人',
  `title` varchar(200) NOT NULL COMMENT '告警标题',
  `content` text NOT NULL COMMENT '告警内容',
  `send_status` enum('pending','success','failed') NOT NULL DEFAULT 'pending' COMMENT '发送状态',
  `send_time` datetime DEFAULT NULL COMMENT '发送时间',
  `response_time` datetime DEFAULT NULL COMMENT '响应时间',
  `response_action` varchar(200) DEFAULT NULL COMMENT '响应动作',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_alert_id` (`alert_id`),
  KEY `idx_event_id` (`event_id`),
  KEY `idx_send_status` (`send_status`),
  KEY `idx_created_at` (`created_at`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='告警记录表';

-- 创建系统配置表
CREATE TABLE `system_configs` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `config_key` varchar(100) NOT NULL COMMENT '配置键',
  `config_value` text NOT NULL COMMENT '配置值',
  `config_type` enum('string','number','boolean','json') NOT NULL DEFAULT 'string' COMMENT '配置类型',
  `description` varchar(500) DEFAULT NULL COMMENT '配置描述',
  `created_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP,
  `updated_at` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
  PRIMARY KEY (`id`),
  UNIQUE KEY `uk_config_key` (`config_key`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='系统配置表';

-- 创建性能监控表
CREATE TABLE `performance_metrics` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `controller_id` varchar(100) NOT NULL COMMENT '控制器ID',
  `metric_type` enum('cpu','memory','gpu','disk','network','temperature') NOT NULL COMMENT '指标类型',
  `metric_name` varchar(100) NOT NULL COMMENT '指标名称',
  `metric_value` float NOT NULL COMMENT '指标值',
  `unit` varchar(20) DEFAULT NULL COMMENT '单位',
  `timestamp` datetime NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '时间戳',
  PRIMARY KEY (`id`),
  KEY `idx_controller_id` (`controller_id`),
  KEY `idx_metric_type` (`metric_type`),
  KEY `idx_timestamp` (`timestamp`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci COMMENT='性能监控表';

-- 插入初始数据

-- 插入示例边缘控制器
INSERT INTO `edge_controllers` (`controller_id`, `controller_name`, `ip_address`, `status`) VALUES
('edge_controller_1', '边缘控制器#1', '192.168.1.100', 'offline'),
('edge_controller_2', '边缘控制器#2', '192.168.1.101', 'offline');

-- 插入示例摄像头配置
INSERT INTO `cameras` (`camera_id`, `camera_name`, `rtsp_url`, `location`, `controller_id`, `enabled_algorithms`) VALUES
('cam_001', '客房101摄像头', 'rtsp://192.168.1.201/stream', '客房101', 'edge_controller_1', '["fall_detection"]'),
('cam_002', '客房102摄像头', 'rtsp://192.168.1.202/stream', '客房102', 'edge_controller_1', '["fall_detection"]'),
('cam_003', '走廊摄像头', 'rtsp://192.168.1.203/stream', '一楼走廊', 'edge_controller_1', '["fall_detection"]'),
('cam_004', '厨房摄像头', 'rtsp://192.168.1.204/stream', '厨房', 'edge_controller_2', '["fire_detection", "smoke_detection"]'),
('cam_005', '大厅摄像头', 'rtsp://192.168.1.205/stream', '大厅', 'edge_controller_2', '["fall_detection"]');

-- 插入系统配置
INSERT INTO `system_configs` (`config_key`, `config_value`, `config_type`, `description`) VALUES
('wechat.corp_id', '', 'string', '企业微信Corp ID'),
('wechat.agent_id', '', 'string', '企业微信Agent ID'),  
('wechat.secret', '', 'string', '企业微信Secret'),
('alert.fall.enabled', 'true', 'boolean', '跌倒告警开关'),
('alert.fire.enabled', 'true', 'boolean', '火灾告警开关'),
('alert.smoke.enabled', 'true', 'boolean', '烟雾告警开关'),
('detection.fall.threshold', '0.8', 'number', '跌倒检测阈值'),
('detection.fire.threshold', '0.85', 'number', '火灾检测阈值'),
('detection.smoke.threshold', '0.75', 'number', '烟雾检测阈值'),
('system.max_events_per_day', '10000', 'number', '每日最大事件数'),
('system.data_retention_days', '90', 'number', '数据保留天数');

SET FOREIGN_KEY_CHECKS = 1;