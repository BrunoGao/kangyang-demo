#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
康养AI检测系统 - NVIDIA DeepStream主应用
支持22路RTSP视频流并发处理，跌倒/火焰/烟雾检测
"""

import sys
import gi
import logging
import time
import json
import threading
from datetime import datetime
from typing import Dict, List, Optional

gi.require_version('Gst', '1.0')
gi.require_version('GstRtspServer', '1.0')
from gi.repository import GObject, Gst, GstRtspServer

import pyds
from kafka import KafkaProducer

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class KangYangDeepStreamApp:
    """康养AI检测系统 - DeepStream应用"""
    
    def __init__(self, config_path: str = "/opt/kangyang/configs/deepstream_app.txt"):
        """
        初始化DeepStream应用
        
        Args:
            config_path: DeepStream配置文件路径
        """
        self.config_path = config_path
        self.pipeline = None
        self.loop = None
        self.kafka_producer = None
        self.rtsp_sources = []
        self.detection_stats = {
            'total_frames': 0,
            'fall_detections': 0,
            'fire_detections': 0,
            'smoke_detections': 0
        }
        
        # 初始化GStreamer
        Gst.init(None)
        
        logger.info("康养AI检测系统 - DeepStream版本初始化完成")
    
    def setup_kafka_producer(self):
        """设置Kafka生产者"""
        try:
            self.kafka_producer = KafkaProducer(
                bootstrap_servers=['kafka-edge:9092'],
                value_serializer=lambda x: json.dumps(x).encode('utf-8'),
                key_serializer=lambda x: x.encode('utf-8') if x else None,
                retries=5,
                retry_backoff_ms=100,
                request_timeout_ms=30000
            )
            logger.info("Kafka生产者初始化成功")
        except Exception as e:
            logger.error(f"Kafka生产者初始化失败: {e}")
            self.kafka_producer = None
    
    def send_detection_event(self, event_data: Dict):
        """发送检测事件到Kafka"""
        if not self.kafka_producer:
            return
        
        try:
            # 构建标准化事件消息
            message = {
                "messageid": f"{event_data['event_type']}_event_{int(time.time() * 1000)}",
                "mdsversion": "1.0",
                "timestamp": datetime.utcnow().isoformat() + "Z",
                "@timestamp": datetime.utcnow().isoformat() + "Z",
                "sensorId": f"camera_{event_data['camera_id']:03d}",
                "objects": [{
                    "id": f"{event_data['event_type']}_{event_data['object_id']}",
                    "object": {
                        "class_id": event_data['class_id'],
                        "class_name": event_data['event_type'],
                        "sub_class": event_data.get('sub_class', ''),
                        "severity": event_data.get('severity', 'medium')
                    },
                    "confidence": event_data['confidence'],
                    "rect_params": {
                        "left": event_data['bbox'][0],
                        "top": event_data['bbox'][1],
                        "width": event_data['bbox'][2],
                        "height": event_data['bbox'][3]
                    },
                    "tracker": {
                        "id": event_data.get('tracker_id', 0),
                        "age": event_data.get('tracker_age', 0),
                        "confidence": event_data.get('tracker_confidence', 0.0),
                        "state": "tracked"
                    }
                }],
                "analyticsModule": {
                    "id": "deepstream_kangyang",
                    "description": "康养AI检测系统-NVIDIA优化版",
                    "source": "DeepStream-6.4",
                    "version": "2.0.0-nvidia"
                },
                "place": {
                    "id": f"room_{event_data['camera_id']:03d}",
                    "name": f"监控点{event_data['camera_id']:03d}",
                    "type": "bedroom"
                }
            }
            
            # 发送到Kafka
            topic = "edge-events"
            self.kafka_producer.send(topic, value=message, key=event_data['event_type'])
            
            # 更新统计
            if event_data['event_type'] == 'fall':
                self.detection_stats['fall_detections'] += 1
            elif event_data['event_type'] == 'fire':
                self.detection_stats['fire_detections'] += 1
            elif event_data['event_type'] == 'smoke':
                self.detection_stats['smoke_detections'] += 1
            
            logger.info(f"检测事件已发送: {event_data['event_type']} - 置信度: {event_data['confidence']:.2f}")
            
        except Exception as e:
            logger.error(f"发送检测事件失败: {e}")
    
    def osd_sink_pad_buffer_probe(self, pad, info, u_data):
        """缓冲区探针回调函数 - 处理检测结果"""
        frame_number = 0
        num_rects = 0
        
        gst_buffer = info.get_buffer()
        if not gst_buffer:
            logger.error("无法获取GstBuffer")
            return
        
        # 获取批次元数据
        batch_meta = pyds.gst_buffer_get_nvds_batch_meta(hash(gst_buffer))
        l_frame = batch_meta.frame_meta_list
        
        while l_frame is not None:
            try:
                frame_meta = pyds.NvDsFrameMeta.cast(l_frame.data)
            except StopIteration:
                break
            
            frame_number = frame_meta.frame_num
            num_rects = frame_meta.num_obj_meta
            l_obj = frame_meta.obj_meta_list
            
            # 处理每个检测到的对象
            while l_obj is not None:
                try:
                    obj_meta = pyds.NvDsObjectMeta.cast(l_obj.data)
                except StopIteration:
                    break
                
                # 提取检测信息
                class_id = obj_meta.class_id
                confidence = obj_meta.confidence
                tracker_id = obj_meta.object_id
                
                # 边界框信息
                rect_params = obj_meta.rect_params
                bbox = [
                    rect_params.left,
                    rect_params.top,
                    rect_params.width,
                    rect_params.height
                ]
                
                # 确定事件类型
                if class_id == 0:  # 人体
                    continue  # 跳过正常人体检测
                elif class_id == 1:  # 跌倒
                    event_type = "fall"
                    severity = "high"
                elif class_id == 2:  # 火焰
                    event_type = "fire"
                    severity = "critical"
                elif class_id == 3:  # 烟雾
                    event_type = "smoke"
                    severity = "medium"
                else:
                    continue
                
                # 只处理高置信度检测
                if confidence > 0.7:
                    event_data = {
                        'camera_id': frame_meta.source_id + 1,
                        'event_type': event_type,
                        'class_id': class_id,
                        'confidence': confidence,
                        'bbox': bbox,
                        'object_id': f"obj_{tracker_id}",
                        'tracker_id': tracker_id,
                        'severity': severity,
                        'frame_number': frame_number
                    }
                    
                    # 发送检测事件
                    self.send_detection_event(event_data)
                
                try:
                    l_obj = l_obj.next
                except StopIteration:
                    break
            
            # 更新帧统计
            self.detection_stats['total_frames'] += 1
            
            try:
                l_frame = l_frame.next
            except StopIteration:
                break
        
        return Gst.PadProbeReturn.OK
    
    def create_pipeline(self) -> bool:
        """创建GStreamer流水线"""
        try:
            # 创建流水线
            self.pipeline = Gst.Pipeline()
            
            if not self.pipeline:
                logger.error("无法创建GStreamer流水线")
                return False
            
            # 创建streammux元素（多流输入复用器）
            streammux = Gst.ElementFactory.make("nvstreammux", "streammux")
            if not streammux:
                logger.error("无法创建nvstreammux元素")
                return False
            
            streammux.set_property('width', 1280)
            streammux.set_property('height', 720)
            streammux.set_property('batch-size', 22)
            streammux.set_property('batched-push-timeout', 4000000)
            
            self.pipeline.add(streammux)
            
            # 创建RTSP源（22路摄像头）
            for i in range(22):
                source_name = f"source_{i}"
                source = Gst.ElementFactory.make("rtspsrc", source_name)
                if not source:
                    logger.error(f"无法创建rtspsrc元素: {source_name}")
                    continue
                
                # 设置RTSP地址（示例地址，生产环境需要配置实际地址）
                rtsp_url = f"rtsp://192.168.1.{100+i}/stream"
                source.set_property('location', rtsp_url)
                source.set_property('latency', 2000)
                
                # 创建解码器链
                depay = Gst.ElementFactory.make("rtph264depay", f"depay_{i}")
                parser = Gst.ElementFactory.make("h264parse", f"parser_{i}")
                decoder = Gst.ElementFactory.make("nvv4l2decoder", f"decoder_{i}")
                
                if not all([depay, parser, decoder]):
                    logger.error(f"无法创建解码器元素链: source_{i}")
                    continue
                
                # 添加元素到流水线
                self.pipeline.add(source)
                self.pipeline.add(depay)
                self.pipeline.add(parser)
                self.pipeline.add(decoder)
                
                # 连接解码器链
                depay.link(parser)
                parser.link(decoder)
                
                # 连接到streammux
                sinkpad = streammux.get_request_pad(f"sink_{i}")
                srcpad = decoder.get_static_pad("src")
                srcpad.link(sinkpad)
                
                # 连接RTSP源的动态pad
                source.connect("pad-added", self.on_rtsp_pad_added, depay)
                
                self.rtsp_sources.append({
                    'id': i,
                    'url': rtsp_url,
                    'source': source,
                    'status': 'connecting'
                })
                
                logger.info(f"已配置RTSP源 {i}: {rtsp_url}")
            
            # 创建主推理引擎（跌倒检测 + 火焰烟雾检测）
            pgie_fall = Gst.ElementFactory.make("nvinfer", "pgie-fall")
            if not pgie_fall:
                logger.error("无法创建主推理引擎")
                return False
            
            pgie_fall.set_property('config-file-path', "/opt/kangyang/configs/pgie_fall_config.txt")
            
            # 创建跟踪器
            tracker = Gst.ElementFactory.make("nvtracker", "tracker")
            if not tracker:
                logger.error("无法创建跟踪器")
                return False
            
            tracker.set_property('tracker-config-file', "/opt/kangyang/configs/nvdcf_tracker.txt")
            
            # 创建次级推理引擎（精细化检测）
            sgie_refine = Gst.ElementFactory.make("nvinfer", "sgie-refine")
            if sgie_refine:
                sgie_refine.set_property('config-file-path', "/opt/kangyang/configs/sgie_refine_config.txt")
            
            # 创建OSD（On-Screen Display）
            nvvideoconvert = Gst.ElementFactory.make("nvvideoconvert", "nvvideoconvert")
            nvosd = Gst.ElementFactory.make("nvdsosd", "nvosd")
            
            # 创建输出sink
            nvvideoconvert2 = Gst.ElementFactory.make("nvvideoconvert", "nvvideoconvert2")
            capsfilter = Gst.ElementFactory.make("capsfilter", "capsfilter")
            caps = Gst.Caps.from_string("video/x-raw(memory:NVMM), format=I420")
            capsfilter.set_property("caps", caps)
            
            encoder = Gst.ElementFactory.make("nvv4l2h264enc", "encoder")
            parser2 = Gst.ElementFactory.make("h264parse", "parser2")
            container = Gst.ElementFactory.make("qtmux", "container")
            sink = Gst.ElementFactory.make("filesink", "sink")
            
            if not all([nvvideoconvert, nvosd, nvvideoconvert2, capsfilter, encoder, parser2, container, sink]):
                logger.error("无法创建输出处理元素")
                return False
            
            # 设置输出文件
            sink.set_property("location", f"/opt/kangyang/data/output_{int(time.time())}.mp4")
            
            # 添加所有元素到流水线
            elements = [pgie_fall, tracker, nvvideoconvert, nvosd, nvvideoconvert2, 
                       capsfilter, encoder, parser2, container, sink]
            
            if sgie_refine:
                elements.insert(2, sgie_refine)
            
            for element in elements:
                self.pipeline.add(element)
            
            # 连接元素
            streammux.link(pgie_fall)
            
            if sgie_refine:
                pgie_fall.link(sgie_refine)
                sgie_refine.link(tracker)
            else:
                pgie_fall.link(tracker)
            
            tracker.link(nvvideoconvert)
            nvvideoconvert.link(nvosd)
            nvosd.link(nvvideoconvert2)
            nvvideoconvert2.link(capsfilter)
            capsfilter.link(encoder)
            encoder.link(parser2)
            parser2.link(container)
            container.link(sink)
            
            # 添加探针到OSD的sink pad
            osd_sink_pad = nvosd.get_static_pad("sink")
            if not osd_sink_pad:
                logger.error("无法获取OSD的sink pad")
                return False
            
            osd_sink_pad.add_probe(Gst.PadProbeType.BUFFER, self.osd_sink_pad_buffer_probe, 0)
            
            logger.info("DeepStream流水线创建成功")
            return True
            
        except Exception as e:
            logger.error(f"创建流水线失败: {e}")
            return False
    
    def on_rtsp_pad_added(self, src, pad, depay):
        """RTSP源动态pad连接回调"""
        pad_name = pad.get_name()
        if pad_name.startswith("recv_rtp_src_0"):
            sinkpad = depay.get_static_pad("sink")
            if not sinkpad.is_linked():
                pad.link(sinkpad)
    
    def bus_call(self, bus, message, loop):
        """GStreamer消息处理"""
        t = message.type
        
        if t == Gst.MessageType.EOS:
            logger.info("流结束")
            loop.quit()
        elif t == Gst.MessageType.WARNING:
            err, debug = message.parse_warning()
            logger.warning(f"警告: {err}, 调试信息: {debug}")
        elif t == Gst.MessageType.ERROR:
            err, debug = message.parse_error()
            logger.error(f"错误: {err}, 调试信息: {debug}")
            loop.quit()
        
        return True
    
    def print_stats(self):
        """定期打印统计信息"""
        while True:
            time.sleep(60)  # 每分钟打印一次
            logger.info(f"统计信息: {self.detection_stats}")
            
            # 重置帧计数（保留检测计数）
            self.detection_stats['total_frames'] = 0
    
    def run(self):
        """运行DeepStream应用"""
        try:
            # 设置Kafka
            self.setup_kafka_producer()
            
            # 创建流水线
            if not self.create_pipeline():
                logger.error("流水线创建失败")
                return False
            
            # 创建主循环
            self.loop = GObject.MainLoop()
            bus = self.pipeline.get_bus()
            bus.add_signal_watch()
            bus.connect("message", self.bus_call, self.loop)
            
            # 启动统计线程
            stats_thread = threading.Thread(target=self.print_stats, daemon=True)
            stats_thread.start()
            
            # 启动流水线
            logger.info("启动DeepStream流水线...")
            ret = self.pipeline.set_state(Gst.State.PLAYING)
            
            if ret == Gst.StateChangeReturn.FAILURE:
                logger.error("无法启动流水线")
                return False
            
            logger.info("DeepStream应用已启动，正在处理22路视频流...")
            logger.info("按Ctrl+C停止应用")
            
            # 运行主循环
            try:
                self.loop.run()
            except KeyboardInterrupt:
                logger.info("收到停止信号")
            
            # 清理资源
            logger.info("正在停止流水线...")
            self.pipeline.set_state(Gst.State.NULL)
            
            if self.kafka_producer:
                self.kafka_producer.flush()
                self.kafka_producer.close()
            
            logger.info("应用已安全退出")
            return True
            
        except Exception as e:
            logger.error(f"运行DeepStream应用失败: {e}")
            return False

def main():
    """主函数"""
    logger.info("启动康养AI检测系统 - NVIDIA DeepStream版")
    
    app = KangYangDeepStreamApp()
    success = app.run()
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()