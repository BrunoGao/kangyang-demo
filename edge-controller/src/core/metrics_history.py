#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
性能指标历史数据管理
基于SQLite存储历史性能数据
"""

import asyncio
import sqlite3
import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
from pathlib import Path
import aiosqlite

logger = logging.getLogger(__name__)

class MetricsHistory:
    """性能指标历史数据管理器"""
    
    def __init__(self, db_path: str = "/tmp/edge-metrics.db"):
        self.db_path = db_path
        self.max_age_days = 7  # 保留7天的数据
        self.cleanup_interval = 3600  # 每小时清理一次
        
    async def initialize(self):
        """初始化数据库"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute('''
                    CREATE TABLE IF NOT EXISTS metrics_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        timestamp TEXT NOT NULL,
                        metric_type TEXT NOT NULL,
                        data JSON NOT NULL,
                        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # 创建索引
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_timestamp 
                    ON metrics_history(timestamp)
                ''')
                
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_metric_type 
                    ON metrics_history(metric_type)
                ''')
                
                await db.execute('''
                    CREATE INDEX IF NOT EXISTS idx_created_at 
                    ON metrics_history(created_at)
                ''')
                
                await db.commit()
                logger.info("指标历史数据库初始化完成")
                
        except Exception as e:
            logger.error(f"初始化指标历史数据库失败: {e}")
            raise
    
    async def store_metrics(self, timestamp: str, metrics_data: Dict[str, Any]):
        """存储性能指标数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 分别存储不同类型的指标
                metric_types = {
                    'system_overview': {
                        'cpu_percent': metrics_data.get('cpu', {}).get('usage_percent', 0),
                        'memory_percent': metrics_data.get('memory', {}).get('virtual', {}).get('percent', 0),
                        'disk_percent': self._get_main_disk_percent(metrics_data.get('disk', {})),
                        'temperature': self._get_system_temperature(metrics_data.get('temperature', {})),
                        'load_average': metrics_data.get('load_average', [0, 0, 0])
                    },
                    'cpu_detailed': metrics_data.get('cpu', {}),
                    'memory_detailed': metrics_data.get('memory', {}),
                    'disk_detailed': metrics_data.get('disk', {}),
                    'network_detailed': metrics_data.get('network', {}),
                    'gpu_detailed': metrics_data.get('gpu', {}),
                    'io_detailed': metrics_data.get('io', {}),
                    'temperature_detailed': metrics_data.get('temperature', {})
                }
                
                for metric_type, data in metric_types.items():
                    await db.execute(
                        'INSERT INTO metrics_history (timestamp, metric_type, data) VALUES (?, ?, ?)',
                        (timestamp, metric_type, json.dumps(data))
                    )
                
                await db.commit()
                
        except Exception as e:
            logger.error(f"存储指标数据失败: {e}")
    
    def _get_main_disk_percent(self, disk_data: Dict[str, Any]) -> float:
        """获取主磁盘使用百分比"""
        usage = disk_data.get('usage', {})
        if not usage:
            return 0.0
        
        # 通常选择根分区或第一个分区
        for device, info in usage.items():
            if info.get('mountpoint') == '/' or info.get('mountpoint') == 'C:':
                return info.get('percent', 0.0)
        
        # 如果没有根分区，返回第一个分区
        first_partition = next(iter(usage.values()), {})
        return first_partition.get('percent', 0.0)
    
    def _get_system_temperature(self, temp_data: Dict[str, Any]) -> float:
        """获取系统温度"""
        if not temp_data or temp_data.get('message') or temp_data.get('error'):
            return 0.0
        
        # 查找第一个有效的温度读数
        for sensor_group in temp_data.values():
            if isinstance(sensor_group, list):
                for sensor in sensor_group:
                    if isinstance(sensor, dict) and sensor.get('current', 0) > 0:
                        return sensor['current']
        return 0.0
    
    async def get_history(self, 
                         metric_type: str = 'system_overview',
                         hours: int = 24,
                         limit: int = 1000) -> List[Dict[str, Any]]:
        """获取历史数据"""
        try:
            since = datetime.now() - timedelta(hours=hours)
            since_str = since.isoformat()
            
            async with aiosqlite.connect(self.db_path) as db:
                db.row_factory = aiosqlite.Row
                
                cursor = await db.execute('''
                    SELECT timestamp, data, created_at
                    FROM metrics_history
                    WHERE metric_type = ? AND timestamp >= ?
                    ORDER BY timestamp ASC
                    LIMIT ?
                ''', (metric_type, since_str, limit))
                
                rows = await cursor.fetchall()
                
                history = []
                for row in rows:
                    try:
                        data = json.loads(row['data'])
                        history.append({
                            'timestamp': row['timestamp'],
                            'data': data,
                            'created_at': row['created_at']
                        })
                    except json.JSONDecodeError:
                        continue
                
                return history
                
        except Exception as e:
            logger.error(f"获取历史数据失败: {e}")
            return []
    
    async def get_aggregated_history(self,
                                   hours: int = 24,
                                   interval_minutes: int = 5) -> Dict[str, Any]:
        """获取聚合的历史数据用于图表显示"""
        try:
            history = await self.get_history('system_overview', hours)
            
            if not history:
                return {
                    'timestamps': [],
                    'cpu': [],
                    'memory': [],
                    'disk': [],
                    'temperature': [],
                    'load_average': []
                }
            
            # 按时间间隔聚合数据
            aggregated = {
                'timestamps': [],
                'cpu': [],
                'memory': [],
                'disk': [],
                'temperature': [],
                'load_average': []
            }
            
            # 简单的时间聚合，每N分钟取一个数据点
            interval_seconds = interval_minutes * 60
            last_time = None
            
            for record in history:
                try:
                    timestamp = datetime.fromisoformat(record['timestamp'])
                    
                    # 如果是第一个数据点或间隔足够长，则添加
                    if last_time is None or (timestamp - last_time).total_seconds() >= interval_seconds:
                        data = record['data']
                        
                        aggregated['timestamps'].append(record['timestamp'])
                        aggregated['cpu'].append(data.get('cpu_percent', 0))
                        aggregated['memory'].append(data.get('memory_percent', 0))
                        aggregated['disk'].append(data.get('disk_percent', 0))
                        aggregated['temperature'].append(data.get('temperature', 0))
                        
                        load_avg = data.get('load_average', [0, 0, 0])
                        aggregated['load_average'].append(load_avg[0] if load_avg else 0)
                        
                        last_time = timestamp
                        
                except (ValueError, KeyError):
                    continue
            
            return aggregated
            
        except Exception as e:
            logger.error(f"获取聚合历史数据失败: {e}")
            return {
                'timestamps': [],
                'cpu': [],
                'memory': [],
                'disk': [],
                'temperature': [],
                'load_average': []
            }
    
    async def cleanup_old_data(self):
        """清理过期数据"""
        try:
            cutoff = datetime.now() - timedelta(days=self.max_age_days)
            cutoff_str = cutoff.isoformat()
            
            async with aiosqlite.connect(self.db_path) as db:
                cursor = await db.execute(
                    'DELETE FROM metrics_history WHERE timestamp < ?',
                    (cutoff_str,)
                )
                
                deleted_count = cursor.rowcount
                await db.commit()
                
                if deleted_count > 0:
                    logger.info(f"清理了 {deleted_count} 条过期的历史数据")
                    
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """获取存储统计信息"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 总记录数
                cursor = await db.execute('SELECT COUNT(*) as total FROM metrics_history')
                total_row = await cursor.fetchone()
                total_count = total_row[0] if total_row else 0
                
                # 最早和最新记录时间
                cursor = await db.execute('''
                    SELECT MIN(timestamp) as earliest, MAX(timestamp) as latest 
                    FROM metrics_history
                ''')
                time_row = await cursor.fetchone()
                earliest = time_row[0] if time_row and time_row[0] else None
                latest = time_row[1] if time_row and time_row[1] else None
                
                # 按指标类型统计
                cursor = await db.execute('''
                    SELECT metric_type, COUNT(*) as count 
                    FROM metrics_history 
                    GROUP BY metric_type
                ''')
                type_stats = {}
                async for row in cursor:
                    type_stats[row[0]] = row[1]
                
                return {
                    'total_records': total_count,
                    'earliest_record': earliest,
                    'latest_record': latest,
                    'records_by_type': type_stats,
                    'database_path': self.db_path
                }
                
        except Exception as e:
            logger.error(f"获取存储统计信息失败: {e}")
            return {}
    
    async def start_background_cleanup(self):
        """启动后台清理任务"""
        async def cleanup_task():
            while True:
                try:
                    await asyncio.sleep(self.cleanup_interval)
                    await self.cleanup_old_data()
                except asyncio.CancelledError:
                    break
                except Exception as e:
                    logger.error(f"后台清理任务错误: {e}")
        
        asyncio.create_task(cleanup_task())