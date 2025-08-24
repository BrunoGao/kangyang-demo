#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
GPU检测和适配系统
支持苹果M系列、NVIDIA、AMD等不同GPU的检测和优化
"""

import platform
import subprocess
import logging
import os
from typing import Dict, Any, Optional, List
from enum import Enum

logger = logging.getLogger(__name__)

class GPUType(Enum):
    """GPU类型枚举"""
    APPLE_M_SERIES = "apple_m_series"
    NVIDIA = "nvidia"
    AMD = "amd"
    INTEL = "intel"
    CPU_ONLY = "cpu_only"
    UNKNOWN = "unknown"

class GPUInfo:
    """GPU信息类"""
    def __init__(self):
        self.gpu_type: GPUType = GPUType.UNKNOWN
        self.gpu_name: str = ""
        self.gpu_memory: int = 0
        self.compute_capability: str = ""
        self.driver_version: str = ""
        self.supports_ml_compute: bool = False
        self.supports_metal: bool = False
        self.supports_cuda: bool = False
        self.supports_opencl: bool = False
        self.optimization_backend: str = ""
        
class GPUDetector:
    """GPU检测器"""
    
    def __init__(self):
        self.gpu_info = GPUInfo()
        self._detect_gpu()
        
    def _detect_gpu(self):
        """检测GPU类型和信息"""
        system = platform.system()
        
        if system == "Darwin":  # macOS
            self._detect_apple_gpu()
        elif system == "Linux":
            self._detect_linux_gpu()
        elif system == "Windows":
            self._detect_windows_gpu()
        else:
            self.gpu_info.gpu_type = GPUType.CPU_ONLY
            
        self._set_optimization_backend()
        
    def _detect_apple_gpu(self):
        """检测苹果GPU（M1/M2/M3/M4系列）"""
        try:
            # 检测苹果芯片类型
            result = subprocess.run(
                ["system_profiler", "SPHardwareDataType"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                # 检测M系列芯片
                if any(chip in output for chip in ["apple m1", "apple m2", "apple m3", "apple m4"]):
                    self.gpu_info.gpu_type = GPUType.APPLE_M_SERIES
                    
                    # 提取具体芯片型号
                    for line in result.stdout.split('\n'):
                        if 'Chip:' in line:
                            self.gpu_info.gpu_name = line.split('Chip:')[1].strip()
                            break
                    
                    # 检测GPU支持
                    self.gpu_info.supports_metal = True
                    self.gpu_info.supports_ml_compute = True
                    
                    # 检测内存
                    self._detect_apple_memory()
                    
                    logger.info(f"检测到苹果M系列芯片: {self.gpu_info.gpu_name}")
                    return
                    
            # 如果不是M系列，检查是否有独立GPU
            self._detect_macos_discrete_gpu()
            
        except Exception as e:
            logger.warning(f"苹果GPU检测失败: {e}")
            self.gpu_info.gpu_type = GPUType.CPU_ONLY
            
    def _detect_apple_memory(self):
        """检测苹果设备内存（统一内存架构）"""
        try:
            result = subprocess.run(
                ["sysctl", "hw.memsize"],
                capture_output=True,
                text=True
            )
            if result.returncode == 0:
                memory_bytes = int(result.stdout.split(':')[1].strip())
                self.gpu_info.gpu_memory = memory_bytes // (1024 * 1024)  # MB
                logger.info(f"检测到统一内存: {self.gpu_info.gpu_memory}MB")
        except Exception as e:
            logger.warning(f"内存检测失败: {e}")
            
    def _detect_macos_discrete_gpu(self):
        """检测macOS独立GPU"""
        try:
            result = subprocess.run(
                ["system_profiler", "SPDisplaysDataType"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                output = result.stdout.lower()
                
                if "nvidia" in output:
                    self.gpu_info.gpu_type = GPUType.NVIDIA
                    self.gpu_info.supports_cuda = self._check_cuda_support()
                elif "amd" in output or "radeon" in output:
                    self.gpu_info.gpu_type = GPUType.AMD
                    self.gpu_info.supports_opencl = True
                else:
                    self.gpu_info.gpu_type = GPUType.CPU_ONLY
                    
        except Exception as e:
            logger.warning(f"独立GPU检测失败: {e}")
            self.gpu_info.gpu_type = GPUType.CPU_ONLY
            
    def _detect_linux_gpu(self):
        """检测Linux GPU"""
        try:
            # 首先检测NVIDIA
            if self._check_nvidia_gpu():
                return
                
            # 检测AMD GPU
            if self._check_amd_gpu():
                return
                
            # 检测Intel GPU
            if self._check_intel_gpu():
                return
                
            # 默认CPU only
            self.gpu_info.gpu_type = GPUType.CPU_ONLY
            
        except Exception as e:
            logger.warning(f"Linux GPU检测失败: {e}")
            self.gpu_info.gpu_type = GPUType.CPU_ONLY
            
    def _check_nvidia_gpu(self) -> bool:
        """检测NVIDIA GPU"""
        try:
            result = subprocess.run(
                ["nvidia-smi", "--query-gpu=name,memory.total,driver_version,compute_cap", "--format=csv,noheader,nounits"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                lines = result.stdout.strip().split('\n')
                if lines and lines[0]:
                    parts = lines[0].split(', ')
                    if len(parts) >= 4:
                        self.gpu_info.gpu_type = GPUType.NVIDIA
                        self.gpu_info.gpu_name = parts[0]
                        self.gpu_info.gpu_memory = int(parts[1])
                        self.gpu_info.driver_version = parts[2]
                        self.gpu_info.compute_capability = parts[3]
                        self.gpu_info.supports_cuda = True
                        
                        logger.info(f"检测到NVIDIA GPU: {self.gpu_info.gpu_name}")
                        return True
                        
        except FileNotFoundError:
            pass
        except Exception as e:
            logger.warning(f"NVIDIA GPU检测失败: {e}")
            
        return False
        
    def _check_amd_gpu(self) -> bool:
        """检测AMD GPU"""
        try:
            # 检测AMD GPU
            result = subprocess.run(
                ["lspci", "-v"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and "amd" in result.stdout.lower():
                self.gpu_info.gpu_type = GPUType.AMD
                self.gpu_info.supports_opencl = True
                
                # 尝试获取更多信息
                for line in result.stdout.split('\n'):
                    if 'VGA compatible controller' in line and 'AMD' in line:
                        self.gpu_info.gpu_name = line.split('controller: ')[1]
                        break
                        
                logger.info(f"检测到AMD GPU: {self.gpu_info.gpu_name}")
                return True
                
        except Exception as e:
            logger.warning(f"AMD GPU检测失败: {e}")
            
        return False
        
    def _check_intel_gpu(self) -> bool:
        """检测Intel GPU"""
        try:
            result = subprocess.run(
                ["lspci", "-v"],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0 and "intel" in result.stdout.lower():
                self.gpu_info.gpu_type = GPUType.INTEL
                self.gpu_info.supports_opencl = True
                
                for line in result.stdout.split('\n'):
                    if 'VGA compatible controller' in line and 'Intel' in line:
                        self.gpu_info.gpu_name = line.split('controller: ')[1]
                        break
                        
                logger.info(f"检测到Intel GPU: {self.gpu_info.gpu_name}")
                return True
                
        except Exception as e:
            logger.warning(f"Intel GPU检测失败: {e}")
            
        return False
        
    def _detect_windows_gpu(self):
        """检测Windows GPU"""
        try:
            # Windows GPU检测逻辑
            self.gpu_info.gpu_type = GPUType.CPU_ONLY
            logger.info("Windows GPU检测尚未实现，使用CPU模式")
            
        except Exception as e:
            logger.warning(f"Windows GPU检测失败: {e}")
            self.gpu_info.gpu_type = GPUType.CPU_ONLY
            
    def _check_cuda_support(self) -> bool:
        """检查CUDA支持"""
        try:
            import torch
            return torch.cuda.is_available()
        except ImportError:
            return False
            
    def _set_optimization_backend(self):
        """设置优化后端"""
        if self.gpu_info.gpu_type == GPUType.APPLE_M_SERIES:
            if self.gpu_info.supports_ml_compute:
                self.gpu_info.optimization_backend = "coreml"
            else:
                self.gpu_info.optimization_backend = "cpu"
                
        elif self.gpu_info.gpu_type == GPUType.NVIDIA:
            if self.gpu_info.supports_cuda:
                self.gpu_info.optimization_backend = "cuda"
            else:
                self.gpu_info.optimization_backend = "cpu"
                
        elif self.gpu_info.gpu_type in [GPUType.AMD, GPUType.INTEL]:
            if self.gpu_info.supports_opencl:
                self.gpu_info.optimization_backend = "opencl"
            else:
                self.gpu_info.optimization_backend = "cpu"
                
        else:
            self.gpu_info.optimization_backend = "cpu"
            
    def get_gpu_info(self) -> Dict[str, Any]:
        """获取GPU信息字典"""
        return {
            "gpu_type": self.gpu_info.gpu_type.value,
            "gpu_name": self.gpu_info.gpu_name,
            "gpu_memory": self.gpu_info.gpu_memory,
            "compute_capability": self.gpu_info.compute_capability,
            "driver_version": self.gpu_info.driver_version,
            "supports_ml_compute": self.gpu_info.supports_ml_compute,
            "supports_metal": self.gpu_info.supports_metal,
            "supports_cuda": self.gpu_info.supports_cuda,
            "supports_opencl": self.gpu_info.supports_opencl,
            "optimization_backend": self.gpu_info.optimization_backend
        }
        
    def get_recommended_settings(self) -> Dict[str, Any]:
        """获取推荐的算法设置"""
        settings = {
            "batch_size": 1,
            "num_threads": 4,
            "use_fp16": False,
            "input_size": (640, 480),
            "detection_backends": []
        }
        
        if self.gpu_info.gpu_type == GPUType.APPLE_M_SERIES:
            settings.update({
                "batch_size": 2,
                "num_threads": 8,
                "use_fp16": True,
                "input_size": (640, 480),
                "detection_backends": ["coreml", "onnx"],
                "memory_optimization": True,
                "neural_engine": True
            })
            
        elif self.gpu_info.gpu_type == GPUType.NVIDIA:
            # 根据计算能力调整设置
            if self.gpu_info.compute_capability and float(self.gpu_info.compute_capability) >= 7.0:
                settings.update({
                    "batch_size": 4,
                    "num_threads": 6,
                    "use_fp16": True,
                    "input_size": (640, 640),
                    "detection_backends": ["tensorrt", "cuda", "onnx"],
                    "tensor_cores": True
                })
            else:
                settings.update({
                    "batch_size": 2,
                    "num_threads": 4,
                    "use_fp16": False,
                    "detection_backends": ["cuda", "onnx"]
                })
                
        elif self.gpu_info.gpu_type in [GPUType.AMD, GPUType.INTEL]:
            settings.update({
                "batch_size": 1,
                "num_threads": 4,
                "use_fp16": False,
                "detection_backends": ["opencl", "cpu"]
            })
            
        else:  # CPU_ONLY
            settings.update({
                "batch_size": 1,
                "num_threads": min(4, os.cpu_count() or 4),
                "use_fp16": False,
                "detection_backends": ["cpu"],
                "cpu_optimization": True
            })
            
        return settings

def get_gpu_detector() -> GPUDetector:
    """获取GPU检测器单例"""
    if not hasattr(get_gpu_detector, '_instance'):
        get_gpu_detector._instance = GPUDetector()
    return get_gpu_detector._instance

if __name__ == "__main__":
    # 测试代码
    logging.basicConfig(level=logging.INFO)
    detector = GPUDetector()
    
    print("GPU检测结果:")
    print("-" * 50)
    gpu_info = detector.get_gpu_info()
    for key, value in gpu_info.items():
        print(f"{key}: {value}")
        
    print("\n推荐设置:")
    print("-" * 50)
    settings = detector.get_recommended_settings()
    for key, value in settings.items():
        print(f"{key}: {value}")