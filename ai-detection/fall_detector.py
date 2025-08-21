import cv2
import numpy as np
import mediapipe as mp
import time
import os
from typing import Dict, List, Tuple, Optional
import json
import redis
from datetime import datetime

class FallDetector:
    def __init__(self):
        # 初始化MediaPipe姿态检测
        self.mp_pose = mp.solutions.pose
        self.pose = self.mp_pose.Pose(
            static_image_mode=False,
            model_complexity=1,
            enable_segmentation=False,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        self.mp_drawing = mp.solutions.drawing_utils
        
        # 跌倒检测参数
        self.fall_threshold = 0.7  # 跌倒阈值
        self.lying_time_threshold = 5.0  # 躺倒时间阈值(秒)
        self.person_states = {}  # 存储每个人的状态
        
        # Redis连接
        try:
            redis_host = os.getenv('REDIS_HOST', 'localhost')
            redis_port = int(os.getenv('REDIS_PORT', '6379'))
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
        except:
            self.redis_client = None
            print("Redis连接失败，将使用本地存储")

    def calculate_body_angle(self, landmarks) -> float:
        """计算人体倾斜角度"""
        try:
            # 获取关键点
            left_shoulder = landmarks[self.mp_pose.PoseLandmark.LEFT_SHOULDER.value]
            right_shoulder = landmarks[self.mp_pose.PoseLandmark.RIGHT_SHOULDER.value]
            left_hip = landmarks[self.mp_pose.PoseLandmark.LEFT_HIP.value]
            right_hip = landmarks[self.mp_pose.PoseLandmark.RIGHT_HIP.value]
            
            # 计算肩膀和臀部中点
            shoulder_center = [(left_shoulder.x + right_shoulder.x) / 2, 
                             (left_shoulder.y + right_shoulder.y) / 2]
            hip_center = [(left_hip.x + right_hip.x) / 2, 
                         (left_hip.y + right_hip.y) / 2]
            
            # 计算躯干与垂直方向的角度
            dx = hip_center[0] - shoulder_center[0]
            dy = hip_center[1] - shoulder_center[1]
            
            angle = abs(np.arctan2(dx, dy))
            return angle
        except:
            return 0.0

    def detect_fall(self, landmarks, person_id: str = "person_1") -> Dict:
        """检测跌倒"""
        current_time = time.time()
        
        # 计算身体角度
        body_angle = self.calculate_body_angle(landmarks)
        
        # 判断是否跌倒
        is_fallen = body_angle > self.fall_threshold
        
        # 获取或初始化人员状态
        if person_id not in self.person_states:
            self.person_states[person_id] = {
                'is_fallen': False,
                'fall_start_time': None,
                'last_alert_time': 0,
                'consecutive_fall_frames': 0
            }
        
        state = self.person_states[person_id]
        
        if is_fallen:
            state['consecutive_fall_frames'] += 1
            if not state['is_fallen'] and state['consecutive_fall_frames'] > 5:  # 连续5帧确认跌倒
                state['is_fallen'] = True
                state['fall_start_time'] = current_time
                # 发送即时跌倒告警
                self.send_alert({
                    'type': 'fall_detected',
                    'person_id': person_id,
                    'timestamp': datetime.now().isoformat(),
                    'body_angle': round(body_angle, 2),
                    'severity': 'immediate'
                })
        else:
            state['consecutive_fall_frames'] = 0
            if state['is_fallen']:
                state['is_fallen'] = False
                state['fall_start_time'] = None
        
        # 检查长时间躺倒
        if state['is_fallen'] and state['fall_start_time']:
            lying_duration = current_time - state['fall_start_time']
            if lying_duration > self.lying_time_threshold:
                # 每30秒发送一次持续告警
                if current_time - state['last_alert_time'] > 30:
                    state['last_alert_time'] = current_time
                    self.send_alert({
                        'type': 'prolonged_fall',
                        'person_id': person_id,
                        'timestamp': datetime.now().isoformat(),
                        'duration': round(lying_duration, 1),
                        'severity': 'critical'
                    })
        
        return {
            'is_fallen': state['is_fallen'],
            'body_angle': round(body_angle, 2),
            'lying_duration': round(current_time - state['fall_start_time'], 1) if state['fall_start_time'] else 0,
            'person_id': person_id
        }

    def send_alert(self, alert_data: Dict):
        """发送告警信息"""
        try:
            if self.redis_client:
                # 发布到Redis频道
                self.redis_client.publish('fall_alerts', json.dumps(alert_data))
                # 存储到Redis列表
                self.redis_client.lpush('fall_events', json.dumps(alert_data))
                self.redis_client.ltrim('fall_events', 0, 999)  # 保留最近1000条记录
            
            print(f"🚨 跌倒告警: {alert_data}")
        except Exception as e:
            print(f"发送告警失败: {e}")

    def process_frame(self, frame: np.ndarray, camera_id: str = "camera_1") -> Tuple[np.ndarray, List[Dict]]:
        """处理单帧图像"""
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        results = self.pose.process(rgb_frame)
        
        detections = []
        
        if results.pose_landmarks:
            # 绘制姿态关键点
            self.mp_drawing.draw_landmarks(
                frame, results.pose_landmarks, self.mp_pose.POSE_CONNECTIONS)
            
            # 检测跌倒
            detection_result = self.detect_fall(results.pose_landmarks.landmark)
            detections.append(detection_result)
            
            # 在图像上显示检测结果
            status_text = "🚨 跌倒" if detection_result['is_fallen'] else "✅ 正常"
            color = (0, 0, 255) if detection_result['is_fallen'] else (0, 255, 0)
            
            cv2.putText(frame, status_text, (10, 30), 
                       cv2.FONT_HERSHEY_SIMPLEX, 1, color, 2)
            cv2.putText(frame, f"角度: {detection_result['body_angle']}", 
                       (10, 60), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
            
            if detection_result['lying_duration'] > 0:
                cv2.putText(frame, f"持续: {detection_result['lying_duration']}s", 
                           (10, 90), cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)
        
        return frame, detections

    def process_video_stream(self, source=0):
        """处理视频流"""
        cap = cv2.VideoCapture(source)
        
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            processed_frame, detections = self.process_frame(frame)
            
            cv2.imshow('Fall Detection Demo', processed_frame)
            
            if cv2.waitKey(1) & 0xFF == ord('q'):
                break
        
        cap.release()
        cv2.destroyAllWindows()

if __name__ == "__main__":
    detector = FallDetector()
    print("启动跌倒检测演示...")
    print("按 'q' 退出")
    detector.process_video_stream(0)  # 使用摄像头0