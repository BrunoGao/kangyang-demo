#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
边缘控制器系统监控模块
支持CPU、GPU、内存、磁盘、网络、IO、温度等全面监控
"""

import asyncio
import time
import logging
import json
import subprocess
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from dataclasses import dataclass, asdict
import psutil
import platform

logger = logging.getLogger(__name__)

@dataclass
class SystemMetrics:
    """系统指标数据类"""
    timestamp: str
    cpu: Dict[str, Any]
    memory: Dict[str, Any]
    disk: Dict[str, Any]
    network: Dict[str, Any]
    gpu: Dict[str, Any]
    temperature: Dict[str, Any]
    io: Dict[str, Any]
    load_avg: List[float]

class SystemMonitor:
    """系统监控器"""
    
    def __init__(self):
        self.system_info = self._get_system_info()
        self.network_io_counters = psutil.net_io_counters()
        self.disk_io_counters = psutil.disk_io_counters()
        self.last_network_check = time.time()
        self.last_disk_check = time.time()
        
    def _get_system_info(self) -> Dict[str, str]:
        """获取系统基本信息"""
        return {
            "system": platform.system(),
            "machine": platform.machine(), 
            "processor": platform.processor(),
            "python_version": platform.python_version(),
            "platform": platform.platform()
        }
    
    async def get_cpu_metrics(self) -> Dict[str, Any]:
        """获取CPU指标"""
        try:
            # CPU使用率 - 按核心
            cpu_percent_per_core = psutil.cpu_percent(interval=0.1, percpu=True)
            cpu_percent = psutil.cpu_percent(interval=0.1)
            
            # CPU频率
            cpu_freq = psutil.cpu_freq()
            
            # CPU负载
            load_avg = psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
            
            # CPU时间
            cpu_times = psutil.cpu_times()
            
            return {
                "usage_percent": round(cpu_percent, 2),
                "per_core": [round(core, 2) for core in cpu_percent_per_core],
                "count_logical": psutil.cpu_count(logical=True),
                "count_physical": psutil.cpu_count(logical=False),
                "frequency": {
                    "current": round(cpu_freq.current, 2) if cpu_freq else 0,
                    "min": round(cpu_freq.min, 2) if cpu_freq else 0,
                    "max": round(cpu_freq.max, 2) if cpu_freq else 0
                } if cpu_freq else {"current": 0, "min": 0, "max": 0},
                "load_average": {
                    "1min": round(load_avg[0], 2),
                    "5min": round(load_avg[1], 2),
                    "15min": round(load_avg[2], 2)
                },
                "times": {
                    "user": cpu_times.user,
                    "system": cpu_times.system,
                    "idle": cpu_times.idle,
                    "iowait": getattr(cpu_times, 'iowait', 0)
                }
            }
        except Exception as e:
            logger.error(f"获取CPU指标失败: {e}")
            return {"error": str(e)}
    
    async def get_memory_metrics(self) -> Dict[str, Any]:
        """获取内存指标"""
        try:
            virtual_mem = psutil.virtual_memory()
            swap_mem = psutil.swap_memory()
            
            return {
                "virtual": {
                    "total": virtual_mem.total,
                    "available": virtual_mem.available,
                    "used": virtual_mem.used,
                    "free": virtual_mem.free,
                    "percent": round(virtual_mem.percent, 2),
                    "active": getattr(virtual_mem, 'active', 0),
                    "inactive": getattr(virtual_mem, 'inactive', 0),
                    "buffers": getattr(virtual_mem, 'buffers', 0),
                    "cached": getattr(virtual_mem, 'cached', 0)
                },
                "swap": {
                    "total": swap_mem.total,
                    "used": swap_mem.used,
                    "free": swap_mem.free,
                    "percent": round(swap_mem.percent, 2),
                    "sin": swap_mem.sin,
                    "sout": swap_mem.sout
                }
            }
        except Exception as e:
            logger.error(f"获取内存指标失败: {e}")
            return {"error": str(e)}
    
    async def get_disk_metrics(self) -> Dict[str, Any]:
        """获取磁盘指标"""
        try:
            disk_usage = {}
            disk_io = {}
            
            # 磁盘使用情况
            partitions = psutil.disk_partitions()
            for partition in partitions:
                try:
                    usage = psutil.disk_usage(partition.mountpoint)
                    disk_usage[partition.device] = {
                        "mountpoint": partition.mountpoint,
                        "fstype": partition.fstype,
                        "total": usage.total,
                        "used": usage.used,
                        "free": usage.free,
                        "percent": round((usage.used / usage.total) * 100, 2)
                    }
                except PermissionError:
                    continue
            
            # 磁盘IO统计
            current_disk_io = psutil.disk_io_counters()
            if current_disk_io and self.disk_io_counters:
                time_delta = time.time() - self.last_disk_check
                if time_delta > 0:
                    read_speed = (current_disk_io.read_bytes - self.disk_io_counters.read_bytes) / time_delta
                    write_speed = (current_disk_io.write_bytes - self.disk_io_counters.write_bytes) / time_delta
                    
                    disk_io = {
                        "read_count": current_disk_io.read_count,
                        "write_count": current_disk_io.write_count,
                        "read_bytes": current_disk_io.read_bytes,
                        "write_bytes": current_disk_io.write_bytes,
                        "read_speed_bps": round(read_speed, 2),
                        "write_speed_bps": round(write_speed, 2),
                        "read_time": current_disk_io.read_time,
                        "write_time": current_disk_io.write_time,
                        "busy_time": getattr(current_disk_io, 'busy_time', 0)
                    }
                    
                self.disk_io_counters = current_disk_io
                self.last_disk_check = time.time()
            
            return {
                "usage": disk_usage,
                "io": disk_io
            }
        except Exception as e:
            logger.error(f"获取磁盘指标失败: {e}")
            return {"error": str(e)}
    
    async def get_network_metrics(self) -> Dict[str, Any]:
        """获取网络指标"""
        try:
            # 网络IO统计
            current_net_io = psutil.net_io_counters()
            network_io = {}
            
            if current_net_io and self.network_io_counters:
                time_delta = time.time() - self.last_network_check
                if time_delta > 0:
                    bytes_sent_per_sec = (current_net_io.bytes_sent - self.network_io_counters.bytes_sent) / time_delta
                    bytes_recv_per_sec = (current_net_io.bytes_recv - self.network_io_counters.bytes_recv) / time_delta
                    
                    network_io = {
                        "bytes_sent": current_net_io.bytes_sent,
                        "bytes_recv": current_net_io.bytes_recv,
                        "packets_sent": current_net_io.packets_sent,
                        "packets_recv": current_net_io.packets_recv,
                        "errin": current_net_io.errin,
                        "errout": current_net_io.errout,
                        "dropin": current_net_io.dropin,
                        "dropout": current_net_io.dropout,
                        "bytes_sent_per_sec": round(bytes_sent_per_sec, 2),
                        "bytes_recv_per_sec": round(bytes_recv_per_sec, 2)
                    }
                    
                self.network_io_counters = current_net_io
                self.last_network_check = time.time()
            
            # 网络连接
            connections = len(psutil.net_connections())
            
            # 网络接口信息
            interfaces = {}
            net_if_addrs = psutil.net_if_addrs()
            net_if_stats = psutil.net_if_stats()
            
            for interface_name, addresses in net_if_addrs.items():
                if interface_name in net_if_stats:
                    stats = net_if_stats[interface_name]
                    interfaces[interface_name] = {
                        "addresses": [{"family": addr.family.name, "address": addr.address, "netmask": addr.netmask} for addr in addresses],
                        "is_up": stats.isup,
                        "duplex": stats.duplex.name if hasattr(stats.duplex, 'name') else str(stats.duplex),
                        "speed": stats.speed,
                        "mtu": stats.mtu
                    }
            
            return {
                "io": network_io,
                "connections": connections,
                "interfaces": interfaces
            }
        except Exception as e:
            logger.error(f"获取网络指标失败: {e}")
            return {"error": str(e)}
    
    async def get_gpu_metrics(self) -> Dict[str, Any]:
        """获取GPU指标"""
        try:
            gpu_info = {}
            
            # 尝试使用nvidia-ml-py获取NVIDIA GPU信息
            try:
                import pynvml
                pynvml.nvmlInit()
                device_count = pynvml.nvmlDeviceGetCount()
                
                for i in range(device_count):
                    handle = pynvml.nvmlDeviceGetHandleByIndex(i)
                    name = pynvml.nvmlDeviceGetName(handle).decode('utf-8')
                    
                    # GPU使用率
                    utilization = pynvml.nvmlDeviceGetUtilizationRates(handle)
                    
                    # GPU内存信息
                    memory_info = pynvml.nvmlDeviceGetMemoryInfo(handle)
                    
                    # GPU温度
                    try:
                        temperature = pynvml.nvmlDeviceGetTemperature(handle, pynvml.NVML_TEMPERATURE_GPU)
                    except:
                        temperature = 0
                    
                    # GPU功耗
                    try:
                        power_draw = pynvml.nvmlDeviceGetPowerUsage(handle) / 1000.0  # 转换为瓦特
                        power_limit = pynvml.nvmlDeviceGetPowerManagementLimitConstraints(handle)[1] / 1000.0
                    except:
                        power_draw = 0
                        power_limit = 0
                    
                    gpu_info[f"gpu_{i}"] = {
                        "name": name,
                        "utilization": {
                            "gpu": utilization.gpu,
                            "memory": utilization.memory
                        },
                        "memory": {
                            "total": memory_info.total,
                            "free": memory_info.free,
                            "used": memory_info.used,
                            "percent": round((memory_info.used / memory_info.total) * 100, 2)
                        },
                        "temperature": temperature,
                        "power": {
                            "draw": round(power_draw, 2),
                            "limit": round(power_limit, 2)
                        }
                    }
                    
            except ImportError:
                # 如果没有pynvml，尝试使用nvidia-smi命令
                try:
                    result = subprocess.run(['nvidia-smi', '--query-gpu=name,utilization.gpu,utilization.memory,memory.total,memory.free,memory.used,temperature.gpu,power.draw', '--format=csv,noheader,nounits'], 
                                          capture_output=True, text=True, timeout=5)
                    if result.returncode == 0:
                        lines = result.stdout.strip().split('\n')
                        for i, line in enumerate(lines):
                            parts = line.split(', ')
                            if len(parts) >= 8:
                                gpu_info[f"gpu_{i}"] = {
                                    "name": parts[0],
                                    "utilization": {
                                        "gpu": float(parts[1]),
                                        "memory": float(parts[2])
                                    },
                                    "memory": {
                                        "total": int(parts[3]) * 1024 * 1024,  # MB转字节
                                        "free": int(parts[4]) * 1024 * 1024,
                                        "used": int(parts[5]) * 1024 * 1024,
                                        "percent": round((int(parts[5]) / int(parts[3])) * 100, 2)
                                    },
                                    "temperature": float(parts[6]),
                                    "power": {
                                        "draw": float(parts[7]),
                                        "limit": 0
                                    }
                                }
                except (subprocess.TimeoutExpired, subprocess.SubprocessError, FileNotFoundError):
                    pass
            
            # 如果没有GPU信息，返回空信息
            if not gpu_info:
                gpu_info = {"message": "No GPU detected or GPU monitoring not available"}
            
            return gpu_info
            
        except Exception as e:
            logger.error(f"获取GPU指标失败: {e}")
            return {"error": str(e)}
    
    async def get_temperature_metrics(self) -> Dict[str, Any]:
        """获取温度指标"""
        try:
            temperatures = {}
            
            # 系统温度传感器
            if hasattr(psutil, 'sensors_temperatures'):
                sensor_temps = psutil.sensors_temperatures()
                for sensor_name, temps in sensor_temps.items():
                    temperatures[sensor_name] = []
                    for temp in temps:
                        temperatures[sensor_name].append({
                            "label": temp.label or "Unknown",
                            "current": temp.current,
                            "high": temp.high,
                            "critical": temp.critical
                        })
            
            # 尝试从/sys/class/thermal读取温度（Linux）
            try:
                import glob
                thermal_zones = glob.glob('/sys/class/thermal/thermal_zone*/temp')
                for i, zone_file in enumerate(thermal_zones):
                    try:
                        with open(zone_file, 'r') as f:
                            temp = int(f.read().strip()) / 1000.0  # 毫度转摄氏度
                            temperatures[f"thermal_zone_{i}"] = [{
                                "label": f"Zone {i}",
                                "current": temp,
                                "high": None,
                                "critical": None
                            }]
                    except:
                        continue
            except:
                pass
            
            if not temperatures:
                temperatures = {"message": "No temperature sensors detected"}
            
            return temperatures
            
        except Exception as e:
            logger.error(f"获取温度指标失败: {e}")
            return {"error": str(e)}
    
    async def get_all_metrics(self) -> SystemMetrics:
        """获取所有系统指标"""
        try:
            timestamp = datetime.now().isoformat()
            
            # 并发获取所有指标
            cpu_task = asyncio.create_task(self.get_cpu_metrics())
            memory_task = asyncio.create_task(self.get_memory_metrics())
            disk_task = asyncio.create_task(self.get_disk_metrics())
            network_task = asyncio.create_task(self.get_network_metrics())
            gpu_task = asyncio.create_task(self.get_gpu_metrics())
            temp_task = asyncio.create_task(self.get_temperature_metrics())
            
            cpu, memory, disk, network, gpu, temperature = await asyncio.gather(
                cpu_task, memory_task, disk_task, network_task, gpu_task, temp_task
            )
            
            # IO指标（从磁盘和网络中提取）
            io_metrics = {
                "disk": disk.get("io", {}),
                "network": network.get("io", {})
            }
            
            # 负载平均值
            load_avg = cpu.get("load_average", {"1min": 0, "5min": 0, "15min": 0})
            
            return SystemMetrics(
                timestamp=timestamp,
                cpu=cpu,
                memory=memory,
                disk=disk,
                network=network,
                gpu=gpu,
                temperature=temperature,
                io=io_metrics,
                load_avg=[load_avg["1min"], load_avg["5min"], load_avg["15min"]]
            )
            
        except Exception as e:
            logger.error(f"获取系统指标失败: {e}")
            # 返回错误信息的空指标
            return SystemMetrics(
                timestamp=datetime.now().isoformat(),
                cpu={"error": str(e)},
                memory={"error": str(e)},
                disk={"error": str(e)},
                network={"error": str(e)},
                gpu={"error": str(e)},
                temperature={"error": str(e)},
                io={"error": str(e)},
                load_avg=[0, 0, 0]
            )
    
    def to_dict(self, metrics: SystemMetrics) -> Dict[str, Any]:
        """将SystemMetrics转换为字典"""
        return asdict(metrics)