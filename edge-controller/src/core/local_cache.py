#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本地缓存 - 断网情况下本地存储事件数据
"""

import json
import logging
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, List, Optional
import aiofiles
import sqlite3
import aiosqlite

logger = logging.getLogger(__name__)

class LocalCache:
    """本地缓存管理器"""
    
    def __init__(self, cache_dir: str = "/tmp/edge-cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.db_path = self.cache_dir / "cache.db"
        self.max_events = 10000  # 最大缓存事件数
        self.retention_days = 7   # 保留天数
        
        self._cleanup_task: Optional[asyncio.Task] = None
        
    async def initialize(self):
        """初始化缓存"""
        try:
            await self._create_tables()
            
            # 启动清理任务
            self._cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            logger.info("本地缓存初始化完成")
            
        except Exception as e:
            logger.error(f"本地缓存初始化失败: {e}")
            raise
    
    async def cleanup(self):
        """清理资源"""
        try:
            if self._cleanup_task:
                self._cleanup_task.cancel()
                await asyncio.gather(self._cleanup_task, return_exceptions=True)
            
            logger.info("本地缓存已清理")
            
        except Exception as e:
            logger.error(f"本地缓存清理失败: {e}")
    
    async def _create_tables(self):
        """创建数据库表"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS events (
                    id TEXT PRIMARY KEY,
                    event_type TEXT NOT NULL,
                    camera_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    data TEXT NOT NULL,
                    sent BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            await db.execute("""
                CREATE TABLE IF NOT EXISTS snapshots (
                    id TEXT PRIMARY KEY,
                    event_id TEXT NOT NULL,
                    file_path TEXT NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (event_id) REFERENCES events (id)
                )
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_timestamp 
                ON events (timestamp)
            """)
            
            await db.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_sent 
                ON events (sent)
            """)
            
            await db.commit()
    
    async def save_event(self, event_data: Dict[str, Any]) -> bool:
        """保存事件到本地缓存"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT OR REPLACE INTO events 
                    (id, event_type, camera_id, timestamp, data, sent)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    event_data.get("id"),
                    event_data.get("event_type"),
                    event_data.get("camera_id"),
                    event_data.get("timestamp"),
                    json.dumps(event_data, ensure_ascii=False),
                    False
                ))
                await db.commit()
            
            logger.debug(f"事件已保存到本地缓存: {event_data.get('id')}")
            return True
            
        except Exception as e:
            logger.error(f"保存事件失败: {e}")
            return False
    
    async def get_unsent_events(self, limit: int = 100) -> List[Dict[str, Any]]:
        """获取未发送的事件"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                async with db.execute("""
                    SELECT data FROM events 
                    WHERE sent = FALSE 
                    ORDER BY timestamp ASC 
                    LIMIT ?
                """, (limit,)) as cursor:
                    rows = await cursor.fetchall()
                    
                    events = []
                    for row in rows:
                        try:
                            event_data = json.loads(row[0])
                            events.append(event_data)
                        except json.JSONDecodeError as e:
                            logger.error(f"解析事件数据失败: {e}")
                    
                    return events
                    
        except Exception as e:
            logger.error(f"获取未发送事件失败: {e}")
            return []
    
    async def mark_events_sent(self, event_ids: List[str]) -> bool:
        """标记事件为已发送"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                placeholders = ",".join("?" * len(event_ids))
                await db.execute(f"""
                    UPDATE events 
                    SET sent = TRUE 
                    WHERE id IN ({placeholders})
                """, event_ids)
                await db.commit()
                
            logger.debug(f"已标记 {len(event_ids)} 个事件为已发送")
            return True
            
        except Exception as e:
            logger.error(f"标记事件发送状态失败: {e}")
            return False
    
    async def save_snapshot(self, event_id: str, image_data: bytes, 
                          format: str = "jpg") -> Optional[str]:
        """保存快照图片"""
        try:
            snapshot_id = f"{event_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            file_name = f"{snapshot_id}.{format}"
            file_path = self.cache_dir / "snapshots" / file_name
            
            # 创建快照目录
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            # 保存图片文件
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(image_data)
            
            # 保存到数据库
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("""
                    INSERT INTO snapshots (id, event_id, file_path)
                    VALUES (?, ?, ?)
                """, (snapshot_id, event_id, str(file_path)))
                await db.commit()
            
            logger.debug(f"快照已保存: {file_path}")
            return str(file_path)
            
        except Exception as e:
            logger.error(f"保存快照失败: {e}")
            return None
    
    async def get_cache_stats(self) -> Dict[str, Any]:
        """获取缓存统计信息"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                # 总事件数
                async with db.execute("SELECT COUNT(*) FROM events") as cursor:
                    total_events = (await cursor.fetchone())[0]
                
                # 未发送事件数
                async with db.execute(
                    "SELECT COUNT(*) FROM events WHERE sent = FALSE"
                ) as cursor:
                    unsent_events = (await cursor.fetchone())[0]
                
                # 快照数
                async with db.execute("SELECT COUNT(*) FROM snapshots") as cursor:
                    total_snapshots = (await cursor.fetchone())[0]
                
                # 磁盘使用
                cache_size = sum(f.stat().st_size for f in self.cache_dir.rglob('*') if f.is_file())
                cache_size_mb = cache_size / (1024 * 1024)
                
                return {
                    "total_events": total_events,
                    "unsent_events": unsent_events,
                    "total_snapshots": total_snapshots,
                    "cache_size_mb": round(cache_size_mb, 2),
                    "cache_dir": str(self.cache_dir)
                }
                
        except Exception as e:
            logger.error(f"获取缓存统计失败: {e}")
            return {}
    
    async def _cleanup_loop(self):
        """定期清理过期数据"""
        while True:
            try:
                await self._cleanup_old_data()
                await asyncio.sleep(3600)  # 每小时清理一次
                
            except asyncio.CancelledError:
                break
            except Exception as e:
                logger.error(f"清理循环异常: {e}")
                await asyncio.sleep(300)  # 出错后等待5分钟
    
    async def _cleanup_old_data(self):
        """清理过期数据"""
        try:
            cutoff_date = datetime.now() - timedelta(days=self.retention_days)
            cutoff_str = cutoff_date.isoformat()
            
            async with aiosqlite.connect(self.db_path) as db:
                # 获取要删除的快照文件
                async with db.execute("""
                    SELECT file_path FROM snapshots 
                    WHERE created_at < ?
                """, (cutoff_str,)) as cursor:
                    old_snapshots = await cursor.fetchall()
                
                # 删除快照文件
                for snapshot in old_snapshots:
                    try:
                        Path(snapshot[0]).unlink(missing_ok=True)
                    except Exception as e:
                        logger.warning(f"删除快照文件失败: {e}")
                
                # 删除数据库记录
                await db.execute("""
                    DELETE FROM snapshots WHERE created_at < ?
                """, (cutoff_str,))
                
                await db.execute("""
                    DELETE FROM events 
                    WHERE created_at < ? AND sent = TRUE
                """, (cutoff_str,))
                
                await db.commit()
                
                logger.info(f"清理完成，删除了 {len(old_snapshots)} 个快照")
                
        except Exception as e:
            logger.error(f"清理过期数据失败: {e}")
    
    async def force_cleanup(self):
        """强制清理所有数据"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute("DELETE FROM snapshots")
                await db.execute("DELETE FROM events")
                await db.commit()
            
            # 删除快照目录
            import shutil
            snapshots_dir = self.cache_dir / "snapshots"
            if snapshots_dir.exists():
                shutil.rmtree(snapshots_dir)
            
            logger.info("强制清理完成")
            
        except Exception as e:
            logger.error(f"强制清理失败: {e}")