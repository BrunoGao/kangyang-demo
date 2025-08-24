#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NVIDIA TensorRT模型优化脚本
将康养AI检测模型优化为TensorRT Engine格式
支持INT8校准和性能基准测试
"""

import os
import sys
import json
import argparse
import subprocess
import numpy as np
import logging
from pathlib import Path
from typing import List, Dict, Tuple, Optional
import onnx
import tensorrt as trt
from cuda import cudart

# 配置日志
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ModelOptimizer:
    """模型优化器 - TensorRT引擎生成和优化"""
    
    def __init__(self, workspace_size: int = 8 << 30):  # 8GB workspace
        """
        初始化模型优化器
        
        Args:
            workspace_size: TensorRT工作空间大小
        """
        self.workspace_size = workspace_size
        self.logger = trt.Logger(trt.Logger.INFO)
        
        # 创建TensorRT构建器
        self.builder = trt.Builder(self.logger)
        self.config = self.builder.create_builder_config()
        self.config.set_memory_pool_limit(trt.MemoryPoolType.WORKSPACE, workspace_size)
        
        logger.info("TensorRT模型优化器初始化完成")
    
    def optimize_fall_detector(self, onnx_path: str, engine_path: str, 
                              precision: str = "int8", batch_size: int = 22) -> bool:
        """
        优化跌倒检测模型
        
        Args:
            onnx_path: ONNX模型路径
            engine_path: 输出Engine路径
            precision: 精度模式 (fp32/fp16/int8)
            batch_size: 批处理大小
            
        Returns:
            优化是否成功
        """
        logger.info(f"开始优化跌倒检测模型: {onnx_path} -> {engine_path}")
        
        # 设置输入尺寸 (22, 3, 720, 1280)
        input_shape = (batch_size, 3, 720, 1280)
        
        if precision == "int8":
            # 使用校准数据集进行INT8优化
            calibration_data = self._prepare_fall_calibration_data()
            return self._build_int8_engine(onnx_path, engine_path, input_shape, calibration_data)
        elif precision == "fp16":
            return self._build_fp16_engine(onnx_path, engine_path, input_shape)
        else:
            return self._build_fp32_engine(onnx_path, engine_path, input_shape)
    
    def optimize_fire_smoke_detector(self, onnx_path: str, engine_path: str, 
                                    precision: str = "int8", batch_size: int = 22) -> bool:
        """
        优化火焰烟雾检测模型
        
        Args:
            onnx_path: ONNX模型路径
            engine_path: 输出Engine路径
            precision: 精度模式
            batch_size: 批处理大小
            
        Returns:
            优化是否成功
        """
        logger.info(f"开始优化火焰烟雾检测模型: {onnx_path} -> {engine_path}")
        
        # 设置输入尺寸 (22, 3, 416, 416)
        input_shape = (batch_size, 3, 416, 416)
        
        if precision == "int8":
            calibration_data = self._prepare_fire_smoke_calibration_data()
            return self._build_int8_engine(onnx_path, engine_path, input_shape, calibration_data)
        elif precision == "fp16":
            return self._build_fp16_engine(onnx_path, engine_path, input_shape)
        else:
            return self._build_fp32_engine(onnx_path, engine_path, input_shape)
    
    def _build_int8_engine(self, onnx_path: str, engine_path: str, 
                          input_shape: Tuple, calibration_data: List[np.ndarray]) -> bool:
        """构建INT8精度引擎"""
        try:
            # 设置INT8精度
            self.config.set_flag(trt.BuilderFlag.INT8)
            
            # 创建校准器
            calibrator = FallDetectionCalibrator(calibration_data, input_shape)
            self.config.int8_calibrator = calibrator
            
            # 解析ONNX模型
            network = self.builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
            parser = trt.OnnxParser(network, self.logger)
            
            with open(onnx_path, 'rb') as f:
                if not parser.parse(f.read()):
                    logger.error("ONNX模型解析失败")
                    return False
            
            # 设置输入形状
            input_tensor = network.get_input(0)
            input_tensor.shape = input_shape
            
            # 构建引擎
            logger.info("正在构建INT8 TensorRT引擎...")
            serialized_engine = self.builder.build_serialized_network(network, self.config)
            
            if serialized_engine is None:
                logger.error("引擎构建失败")
                return False
            
            # 保存引擎
            with open(engine_path, 'wb') as f:
                f.write(serialized_engine)
            
            logger.info(f"INT8引擎构建成功: {engine_path}")
            return True
            
        except Exception as e:
            logger.error(f"INT8引擎构建异常: {e}")
            return False
    
    def _build_fp16_engine(self, onnx_path: str, engine_path: str, input_shape: Tuple) -> bool:
        """构建FP16精度引擎"""
        try:
            # 设置FP16精度
            self.config.set_flag(trt.BuilderFlag.FP16)
            
            # 解析ONNX模型
            network = self.builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
            parser = trt.OnnxParser(network, self.logger)
            
            with open(onnx_path, 'rb') as f:
                if not parser.parse(f.read()):
                    logger.error("ONNX模型解析失败")
                    return False
            
            # 设置输入形状
            input_tensor = network.get_input(0)
            input_tensor.shape = input_shape
            
            # 构建引擎
            logger.info("正在构建FP16 TensorRT引擎...")
            serialized_engine = self.builder.build_serialized_network(network, self.config)
            
            if serialized_engine is None:
                logger.error("引擎构建失败")
                return False
            
            # 保存引擎
            with open(engine_path, 'wb') as f:
                f.write(serialized_engine)
            
            logger.info(f"FP16引擎构建成功: {engine_path}")
            return True
            
        except Exception as e:
            logger.error(f"FP16引擎构建异常: {e}")
            return False
    
    def _build_fp32_engine(self, onnx_path: str, engine_path: str, input_shape: Tuple) -> bool:
        """构建FP32精度引擎"""
        try:
            # 解析ONNX模型
            network = self.builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
            parser = trt.OnnxParser(network, self.logger)
            
            with open(onnx_path, 'rb') as f:
                if not parser.parse(f.read()):
                    logger.error("ONNX模型解析失败")
                    return False
            
            # 设置输入形状
            input_tensor = network.get_input(0)
            input_tensor.shape = input_shape
            
            # 构建引擎
            logger.info("正在构建FP32 TensorRT引擎...")
            serialized_engine = self.builder.build_serialized_network(network, self.config)
            
            if serialized_engine is None:
                logger.error("引擎构建失败")
                return False
            
            # 保存引擎
            with open(engine_path, 'wb') as f:
                f.write(serialized_engine)
            
            logger.info(f"FP32引擎构建成功: {engine_path}")
            return True
            
        except Exception as e:
            logger.error(f"FP32引擎构建异常: {e}")
            return False
    
    def _prepare_fall_calibration_data(self) -> List[np.ndarray]:
        """准备跌倒检测模型的校准数据"""
        logger.info("准备跌倒检测校准数据集...")
        
        calibration_data = []
        
        # 生成多样化的校准数据
        scenarios = [
            "normal_standing",    # 正常站立
            "normal_walking",     # 正常行走
            "normal_sitting",     # 正常坐下
            "slow_movement",      # 缓慢移动
            "fall_forward",       # 向前跌倒
            "fall_backward",      # 向后跌倒
            "fall_sideways",      # 侧向跌倒
            "lying_down",         # 躺下状态
        ]
        
        for scenario in scenarios:
            for i in range(20):  # 每种场景20张图片
                # 生成模拟数据 (实际应用中应使用真实标注数据)
                if scenario.startswith("fall_"):
                    # 跌倒场景: 更多低频分量，模拟人体倒地
                    image = self._generate_fall_scenario_image()
                elif scenario.startswith("normal_"):
                    # 正常场景: 更多中频分量，模拟正常人体姿态
                    image = self._generate_normal_scenario_image()
                else:
                    # 其他场景: 混合频率分量
                    image = self._generate_mixed_scenario_image()
                
                calibration_data.append(image)
        
        logger.info(f"校准数据准备完成: {len(calibration_data)}张图片")
        return calibration_data
    
    def _prepare_fire_smoke_calibration_data(self) -> List[np.ndarray]:
        """准备火焰烟雾检测模型的校准数据"""
        logger.info("准备火焰烟雾检测校准数据集...")
        
        calibration_data = []
        
        scenarios = [
            "normal_indoor",      # 正常室内
            "normal_outdoor",     # 正常室外
            "bright_lighting",    # 强光环境
            "dim_lighting",       # 弱光环境
            "small_fire",         # 小火源
            "large_fire",         # 大火源
            "white_smoke",        # 白烟
            "gray_smoke",         # 灰烟
            "steam",              # 蒸汽
            "dust",               # 灰尘
        ]
        
        for scenario in scenarios:
            for i in range(15):  # 每种场景15张图片
                if scenario.endswith("fire"):
                    image = self._generate_fire_scenario_image()
                elif scenario.endswith("smoke"):
                    image = self._generate_smoke_scenario_image()
                else:
                    image = self._generate_normal_environment_image()
                
                calibration_data.append(image)
        
        logger.info(f"校准数据准备完成: {len(calibration_data)}张图片")
        return calibration_data
    
    def _generate_fall_scenario_image(self) -> np.ndarray:
        """生成跌倒场景模拟图像"""
        # 模拟跌倒场景的图像特征
        image = np.random.randint(0, 255, (3, 720, 1280), dtype=np.uint8)
        
        # 添加跌倒特征: 更多水平结构
        for i in range(5):
            y = np.random.randint(300, 500)
            x_start = np.random.randint(0, 800)
            x_end = min(x_start + 200, 1280)
            image[:, y:y+20, x_start:x_end] = np.random.randint(100, 200)
        
        return image.astype(np.float32) / 255.0
    
    def _generate_normal_scenario_image(self) -> np.ndarray:
        """生成正常场景模拟图像"""
        # 模拟正常场景的图像特征
        image = np.random.randint(0, 255, (3, 720, 1280), dtype=np.uint8)
        
        # 添加正常人体特征: 更多垂直结构
        for i in range(3):
            x = np.random.randint(400, 800)
            y_start = np.random.randint(100, 300)
            y_end = min(y_start + 300, 720)
            image[:, y_start:y_end, x:x+40] = np.random.randint(120, 220)
        
        return image.astype(np.float32) / 255.0
    
    def _generate_mixed_scenario_image(self) -> np.ndarray:
        """生成混合场景模拟图像"""
        image = np.random.randint(0, 255, (3, 720, 1280), dtype=np.uint8)
        return image.astype(np.float32) / 255.0
    
    def _generate_fire_scenario_image(self) -> np.ndarray:
        """生成火焰场景模拟图像"""
        # 模拟火焰特征: 红色/黄色区域，不规则边界
        image = np.random.randint(0, 255, (3, 416, 416), dtype=np.uint8)
        
        # 添加火焰颜色特征
        for i in range(3):
            center_x = np.random.randint(100, 316)
            center_y = np.random.randint(100, 316)
            radius = np.random.randint(20, 60)
            
            # 创建火焰区域
            y_indices, x_indices = np.ogrid[:416, :416]
            mask = (x_indices - center_x)**2 + (y_indices - center_y)**2 <= radius**2
            
            image[0, mask] = np.random.randint(200, 255)  # 红色通道
            image[1, mask] = np.random.randint(150, 255)  # 绿色通道
            image[2, mask] = np.random.randint(0, 100)    # 蓝色通道
        
        return image.astype(np.float32) / 255.0
    
    def _generate_smoke_scenario_image(self) -> np.ndarray:
        """生成烟雾场景模拟图像"""
        # 模拟烟雾特征: 灰色区域，模糊边界
        image = np.random.randint(0, 255, (3, 416, 416), dtype=np.uint8)
        
        # 添加烟雾特征
        for i in range(2):
            center_x = np.random.randint(100, 316)
            center_y = np.random.randint(50, 200)  # 烟雾通常在上方
            width = np.random.randint(80, 150)
            height = np.random.randint(100, 200)
            
            # 创建烟雾区域
            y_start = max(0, center_y - height//2)
            y_end = min(416, center_y + height//2)
            x_start = max(0, center_x - width//2)
            x_end = min(416, center_x + width//2)
            
            gray_value = np.random.randint(100, 180)
            image[:, y_start:y_end, x_start:x_end] = gray_value
        
        return image.astype(np.float32) / 255.0
    
    def _generate_normal_environment_image(self) -> np.ndarray:
        """生成正常环境模拟图像"""
        image = np.random.randint(0, 255, (3, 416, 416), dtype=np.uint8)
        return image.astype(np.float32) / 255.0
    
    def benchmark_engine(self, engine_path: str, input_shape: Tuple, iterations: int = 100) -> Dict:
        """
        对TensorRT引擎进行性能基准测试
        
        Args:
            engine_path: 引擎文件路径
            input_shape: 输入张量形状
            iterations: 测试迭代次数
            
        Returns:
            性能统计信息
        """
        logger.info(f"开始性能基准测试: {engine_path}")
        
        try:
            # 加载引擎
            with open(engine_path, 'rb') as f:
                engine_data = f.read()
            
            runtime = trt.Runtime(self.logger)
            engine = runtime.deserialize_cuda_engine(engine_data)
            
            if engine is None:
                logger.error("引擎加载失败")
                return {}
            
            context = engine.create_execution_context()
            
            # 分配GPU内存
            input_size = np.prod(input_shape) * np.dtype(np.float32).itemsize
            output_size = 1000 * 4  # 假设输出1000个类别
            
            cudart.cudaMalloc(input_size)
            cudart.cudaMalloc(output_size)
            
            # 准备测试数据
            test_data = np.random.randn(*input_shape).astype(np.float32)
            
            # 预热
            for _ in range(10):
                context.execute_v2([0, 0])  # 简化的执行调用
            
            # 性能测试
            import time
            times = []
            
            for i in range(iterations):
                start_time = time.time()
                context.execute_v2([0, 0])
                cudart.cudaDeviceSynchronize()
                end_time = time.time()
                times.append((end_time - start_time) * 1000)  # 转换为毫秒
            
            # 计算统计信息
            times = np.array(times)
            stats = {
                'mean_latency_ms': float(np.mean(times)),
                'min_latency_ms': float(np.min(times)),
                'max_latency_ms': float(np.max(times)),
                'p95_latency_ms': float(np.percentile(times, 95)),
                'p99_latency_ms': float(np.percentile(times, 99)),
                'std_latency_ms': float(np.std(times)),
                'throughput_fps': float(1000.0 / np.mean(times)),
                'iterations': iterations
            }
            
            logger.info(f"性能测试完成: {stats}")
            return stats
            
        except Exception as e:
            logger.error(f"性能测试异常: {e}")
            return {}


class FallDetectionCalibrator(trt.IInt8EntropyCalibrator2):
    """跌倒检测模型INT8校准器"""
    
    def __init__(self, calibration_data: List[np.ndarray], input_shape: Tuple):
        trt.IInt8EntropyCalibrator2.__init__(self)
        self.calibration_data = calibration_data
        self.input_shape = input_shape
        self.current_index = 0
        self.cache_file = "fall_detection_calibration.cache"
        
        # 分配GPU内存
        self.device_input = cudart.cudaMalloc(np.prod(input_shape) * 4)[1]
    
    def get_batch_size(self):
        return 1  # 校准时使用batch_size=1
    
    def get_batch(self, names):
        if self.current_index < len(self.calibration_data):
            # 获取当前批次数据
            batch = self.calibration_data[self.current_index]
            self.current_index += 1
            
            # 拷贝到GPU
            cudart.cudaMemcpy(self.device_input, batch.ctypes.data, 
                             batch.nbytes, cudart.cudaMemcpyKind.cudaMemcpyHostToDevice)
            
            return [int(self.device_input)]
        else:
            return None
    
    def read_calibration_cache(self):
        if os.path.exists(self.cache_file):
            with open(self.cache_file, "rb") as f:
                return f.read()
        return None
    
    def write_calibration_cache(self, cache):
        with open(self.cache_file, "wb") as f:
            f.write(cache)


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="NVIDIA TensorRT模型优化工具")
    
    parser.add_argument("--model", type=str, required=True, 
                       choices=["fall_detector", "fire_smoke_detector", "all"],
                       help="要优化的模型类型")
    
    parser.add_argument("--onnx-path", type=str, required=True,
                       help="输入ONNX模型路径")
    
    parser.add_argument("--engine-path", type=str, required=True,
                       help="输出TensorRT引擎路径")
    
    parser.add_argument("--precision", type=str, default="int8",
                       choices=["fp32", "fp16", "int8"],
                       help="推理精度")
    
    parser.add_argument("--batch-size", type=int, default=22,
                       help="批处理大小")
    
    parser.add_argument("--workspace-size", type=int, default=8,
                       help="TensorRT工作空间大小(GB)")
    
    parser.add_argument("--benchmark", action="store_true",
                       help="执行性能基准测试")
    
    parser.add_argument("--iterations", type=int, default=100,
                       help="基准测试迭代次数")
    
    args = parser.parse_args()
    
    # 创建优化器
    optimizer = ModelOptimizer(workspace_size=args.workspace_size << 30)
    
    try:
        # 执行模型优化
        if args.model == "fall_detector":
            success = optimizer.optimize_fall_detector(
                args.onnx_path, args.engine_path, args.precision, args.batch_size
            )
        elif args.model == "fire_smoke_detector":
            success = optimizer.optimize_fire_smoke_detector(
                args.onnx_path, args.engine_path, args.precision, args.batch_size
            )
        elif args.model == "all":
            # 批量优化所有模型
            models = [
                ("fall_fast.onnx", "fall_fast_int8.engine", "int8"),
                ("fall_refine.onnx", "fall_refine_fp16.engine", "fp16"), 
                ("smoke_fire.onnx", "smoke_fire_int8.engine", "int8")
            ]
            
            success = True
            for onnx_name, engine_name, precision in models:
                onnx_path = os.path.join(os.path.dirname(args.onnx_path), onnx_name)
                engine_path = os.path.join(os.path.dirname(args.engine_path), engine_name)
                
                if os.path.exists(onnx_path):
                    if "fall" in onnx_name:
                        result = optimizer.optimize_fall_detector(onnx_path, engine_path, precision, args.batch_size)
                    else:
                        result = optimizer.optimize_fire_smoke_detector(onnx_path, engine_path, precision, args.batch_size)
                    success = success and result
                else:
                    logger.warning(f"ONNX文件不存在: {onnx_path}")
        
        if not success:
            logger.error("模型优化失败")
            sys.exit(1)
        
        # 执行性能基准测试
        if args.benchmark:
            if args.model == "fall_detector":
                input_shape = (args.batch_size, 3, 720, 1280)
            else:
                input_shape = (args.batch_size, 3, 416, 416)
            
            stats = optimizer.benchmark_engine(args.engine_path, input_shape, args.iterations)
            
            # 保存基准测试结果
            benchmark_file = args.engine_path.replace(".engine", "_benchmark.json")
            with open(benchmark_file, 'w') as f:
                json.dump(stats, f, indent=2)
            
            logger.info(f"基准测试结果已保存: {benchmark_file}")
        
        logger.info("模型优化完成")
        
    except Exception as e:
        logger.error(f"模型优化失败: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()