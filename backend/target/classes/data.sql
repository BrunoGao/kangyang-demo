-- 初始化摄像头数据
INSERT INTO cameras (camera_id, camera_name, location, rtsp_url, is_active, status, last_heartbeat, created_time, updated_time) 
VALUES 
('camera_1', '摄像头-01', '201房间客厅', 'rtsp://192.168.1.100:554/stream1', true, 'online', NOW(), NOW(), NOW()),
('camera_2', '摄像头-02', '201房间卧室', 'rtsp://192.168.1.101:554/stream1', true, 'online', NOW(), NOW(), NOW()),
('camera_3', '摄像头-03', '202房间客厅', 'rtsp://192.168.1.102:554/stream1', false, 'offline', NOW(), NOW(), NOW());

-- 插入一些演示用的跌倒事件数据
INSERT INTO fall_events (person_id, camera_id, event_type, severity, body_angle, duration, location, is_handled, handler, handle_time, remarks, created_time, updated_time)
VALUES 
('person_001', 'camera_1', 'fall_detected', 'immediate', 1.2, 0, '201房间客厅', true, '张护士', NOW() - INTERVAL 2 HOUR, '老人起身时失去平衡，已协助起身', NOW() - INTERVAL 3 HOUR, NOW() - INTERVAL 2 HOUR),
('person_002', 'camera_2', 'prolonged_fall', 'critical', 1.4, 120, '201房间卧室', true, '李医生', NOW() - INTERVAL 1 HOUR, '老人夜间如厕时跌倒，已送医检查', NOW() - INTERVAL 4 HOUR, NOW() - INTERVAL 1 HOUR),
('person_001', 'camera_1', 'fall_detected', 'immediate', 0.9, 0, '201房间客厅', false, NULL, NULL, NULL, NOW() - INTERVAL 30 MINUTE, NOW() - INTERVAL 30 MINUTE),
('person_003', 'camera_3', 'fall_detected', 'immediate', 1.1, 0, '202房间客厅', false, NULL, NULL, NULL, NOW() - INTERVAL 15 MINUTE, NOW() - INTERVAL 15 MINUTE);