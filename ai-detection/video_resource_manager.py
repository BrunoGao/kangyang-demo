#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试视频资源管理器
提供测试视频的下载、管理、验证和组织功能
"""

import os
import json
import hashlib
import requests
import zipfile
import shutil
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class VideoResourceManager:
    """测试视频资源管理器"""
    
    def __init__(self, base_path: str = "test_videos"):
        self.base_path = Path(base_path)
        self.base_path.mkdir(exist_ok=True)
        
        # 创建子目录
        self.categories = {
            'fall': self.base_path / 'fall_detection',
            'fire': self.base_path / 'fire_detection', 
            'smoke': self.base_path / 'smoke_detection',
            'normal': self.base_path / 'normal_scenes',
            'mixed': self.base_path / 'mixed_scenarios',
            'synthetic': self.base_path / 'synthetic_data',
            'real_world': self.base_path / 'real_world_samples'
        }
        
        for category_path in self.categories.values():
            category_path.mkdir(exist_ok=True)
        
        # 视频资源索引文件
        self.index_file = self.base_path / 'video_index.json'
        self.video_index = self.load_index()
        
    def load_index(self) -> Dict:
        """加载视频索引"""
        if self.index_file.exists():
            with open(self.index_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            'videos': {},
            'datasets': {},
            'last_updated': datetime.now().isoformat()
        }
    
    def save_index(self):
        """保存视频索引"""
        self.video_index['last_updated'] = datetime.now().isoformat()
        with open(self.index_file, 'w', encoding='utf-8') as f:
            json.dump(self.video_index, f, indent=2, ensure_ascii=False)
    
    def register_video(self, video_path: str, metadata: Dict) -> str:
        """注册视频到索引"""
        video_path = Path(video_path)
        
        if not video_path.exists():
            raise FileNotFoundError(f"视频文件不存在: {video_path}")
        
        # 计算文件哈希
        file_hash = self.calculate_file_hash(video_path)
        
        # 创建视频记录
        video_id = f"{metadata.get('category', 'unknown')}_{file_hash[:8]}"
        
        video_record = {
            'id': video_id,
            'filename': video_path.name,
            'path': str(video_path.relative_to(self.base_path)),
            'full_path': str(video_path.absolute()),
            'category': metadata.get('category', 'unknown'),
            'description': metadata.get('description', ''),
            'expected_detections': metadata.get('expected_detections', []),
            'difficulty': metadata.get('difficulty', 'unknown'),
            'duration_seconds': metadata.get('duration_seconds', 0),
            'resolution': metadata.get('resolution', ''),
            'fps': metadata.get('fps', 0),
            'file_size': video_path.stat().st_size,
            'file_hash': file_hash,
            'tags': metadata.get('tags', []),
            'source': metadata.get('source', 'unknown'),
            'license': metadata.get('license', 'unknown'),
            'registered_at': datetime.now().isoformat(),
            'quality_score': metadata.get('quality_score', 0),
            'annotation_status': metadata.get('annotation_status', 'none')
        }
        
        self.video_index['videos'][video_id] = video_record
        self.save_index()
        
        logger.info(f"视频已注册: {video_id} - {video_path.name}")
        return video_id
    
    def calculate_file_hash(self, file_path: Path) -> str:
        """计算文件哈希值"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()
    
    def download_sample_videos(self) -> Dict[str, str]:
        """下载示例测试视频"""
        sample_videos = self.get_sample_video_sources()
        download_results = {}
        
        for video_id, video_info in sample_videos.items():
            try:
                result = self.download_video(
                    video_info['url'], 
                    video_info['filename'],
                    video_info['category'],
                    video_info['metadata']
                )
                download_results[video_id] = 'success' if result else 'failed'
                
            except Exception as e:
                logger.error(f"下载视频失败 {video_id}: {e}")
                download_results[video_id] = f'error: {str(e)}'
        
        return download_results
    
    def download_video(self, url: str, filename: str, category: str, metadata: Dict) -> bool:
        """下载单个视频"""
        try:
            # 确定保存路径
            save_path = self.categories.get(category, self.base_path) / filename
            
            if save_path.exists():
                logger.info(f"视频已存在: {filename}")
                # 注册已存在的视频
                self.register_video(save_path, {**metadata, 'category': category})
                return True
            
            logger.info(f"开始下载: {filename} from {url}")
            
            # 下载视频
            response = requests.get(url, stream=True)
            response.raise_for_status()
            
            with open(save_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    f.write(chunk)
            
            # 注册视频
            self.register_video(save_path, {**metadata, 'category': category})
            
            logger.info(f"下载完成: {filename}")
            return True
            
        except Exception as e:
            logger.error(f"下载失败 {filename}: {e}")
            return False
    
    def get_sample_video_sources(self) -> Dict:
        """获取示例视频源配置"""
        return {
            'fall_elderly_01': {
                'url': 'https://example.com/fall_detection_sample_01.mp4',
                'filename': 'elderly_fall_bathroom.mp4',
                'category': 'fall',
                'metadata': {
                    'description': '老人卫生间跌倒场景',
                    'expected_detections': ['fall'],
                    'difficulty': 'medium',
                    'duration_seconds': 45,
                    'resolution': '1920x1080',
                    'fps': 30,
                    'tags': ['fall', 'elderly', 'bathroom'],
                    'source': 'synthetic_dataset_v1',
                    'license': 'research_only',
                    'quality_score': 8
                }
            },
            'fall_elderly_02': {
                'url': 'https://example.com/fall_detection_sample_02.mp4', 
                'filename': 'elderly_fall_bedroom.mp4',
                'category': 'fall',
                'metadata': {
                    'description': '老人卧室跌倒场景，光线较暗',
                    'expected_detections': ['fall'],
                    'difficulty': 'easy',
                    'duration_seconds': 30,
                    'resolution': '1920x1080',
                    'fps': 30,
                    'tags': ['fall', 'elderly', 'bedroom', 'low_light'],
                    'source': 'synthetic_dataset_v1',
                    'license': 'research_only',
                    'quality_score': 7
                }
            },
            'fire_kitchen_01': {
                'url': 'https://example.com/fire_detection_sample_01.mp4',
                'filename': 'kitchen_fire.mp4', 
                'category': 'fire',
                'metadata': {
                    'description': '厨房火灾场景，包含火焰和烟雾',
                    'expected_detections': ['fire', 'smoke'],
                    'difficulty': 'medium',
                    'duration_seconds': 90,
                    'resolution': '1920x1080',
                    'fps': 30,
                    'tags': ['fire', 'smoke', 'kitchen', 'indoor'],
                    'source': 'fire_safety_dataset',
                    'license': 'academic_use',
                    'quality_score': 9
                }
            },
            'smoke_living_room_01': {
                'url': 'https://example.com/smoke_detection_sample_01.mp4',
                'filename': 'living_room_smoke.mp4',
                'category': 'smoke', 
                'metadata': {
                    'description': '客厅烟雾检测场景，早期火灾预警',
                    'expected_detections': ['smoke'],
                    'difficulty': 'easy',
                    'duration_seconds': 60,
                    'resolution': '1920x1080', 
                    'fps': 30,
                    'tags': ['smoke', 'living_room', 'early_warning'],
                    'source': 'fire_safety_dataset',
                    'license': 'academic_use',
                    'quality_score': 8
                }
            },
            'mixed_emergency_01': {
                'url': 'https://example.com/mixed_scenario_01.mp4',
                'filename': 'emergency_evacuation.mp4',
                'category': 'mixed',
                'metadata': {
                    'description': '紧急疏散场景，包含跌倒和火灾',
                    'expected_detections': ['fall', 'fire', 'smoke'],
                    'difficulty': 'very_hard',
                    'duration_seconds': 180,
                    'resolution': '1920x1080',
                    'fps': 30,
                    'tags': ['fall', 'fire', 'smoke', 'complex', 'emergency'],
                    'source': 'comprehensive_safety_dataset',
                    'license': 'research_only',
                    'quality_score': 9
                }
            }
        }
    
    def generate_synthetic_videos(self) -> Dict[str, str]:
        """生成合成测试视频"""
        synthetic_configs = [
            {
                'name': 'synthetic_fall_simple.mp4',
                'type': 'fall',
                'scenario': 'simple_fall',
                'duration': 30,
                'background': 'bedroom',
                'lighting': 'normal'
            },
            {
                'name': 'synthetic_fall_complex.mp4', 
                'type': 'fall',
                'scenario': 'complex_movement_fall',
                'duration': 60,
                'background': 'living_room',
                'lighting': 'dim'
            },
            {
                'name': 'synthetic_fire_kitchen.mp4',
                'type': 'fire',
                'scenario': 'kitchen_fire',
                'duration': 120,
                'background': 'kitchen',
                'lighting': 'normal'
            }
        ]
        
        results = {}
        for config in synthetic_configs:
            try:
                # 这里可以调用视频生成工具或3D渲染引擎
                # 目前创建占位符文件
                video_path = self.categories['synthetic'] / config['name']
                
                if not video_path.exists():
                    # 创建占位符文件(实际应用中替换为真实的视频生成)
                    with open(video_path, 'wb') as f:
                        f.write(b'placeholder_video_data')
                
                # 注册合成视频
                metadata = {
                    'description': f"合成{config['type']}检测视频 - {config['scenario']}",
                    'expected_detections': [config['type']],
                    'difficulty': 'easy' if config['scenario'] == 'simple_fall' else 'medium',
                    'duration_seconds': config['duration'],
                    'resolution': '1920x1080',
                    'fps': 30,
                    'tags': [config['type'], 'synthetic', config['background']],
                    'source': 'synthetic_generator_v1',
                    'license': 'free_use',
                    'quality_score': 6
                }
                
                video_id = self.register_video(video_path, {**metadata, 'category': 'synthetic'})
                results[config['name']] = 'generated'
                
                logger.info(f"合成视频生成完成: {config['name']}")
                
            except Exception as e:
                logger.error(f"合成视频生成失败 {config['name']}: {e}")
                results[config['name']] = f'error: {str(e)}'
        
        return results
    
    def organize_videos_by_category(self):
        """按类别组织视频文件"""
        organized_count = 0
        
        for video_id, video_info in self.video_index['videos'].items():
            current_path = Path(video_info['full_path'])
            
            if not current_path.exists():
                logger.warning(f"视频文件不存在: {current_path}")
                continue
            
            # 确定目标路径
            category = video_info['category'] 
            target_dir = self.categories.get(category, self.base_path)
            target_path = target_dir / current_path.name
            
            # 如果文件不在正确的目录中，则移动它
            if current_path.parent != target_dir:
                try:
                    shutil.move(str(current_path), str(target_path))
                    
                    # 更新索引中的路径
                    video_info['path'] = str(target_path.relative_to(self.base_path))
                    video_info['full_path'] = str(target_path.absolute())
                    
                    organized_count += 1
                    logger.info(f"视频已移动: {current_path.name} -> {category}/")
                    
                except Exception as e:
                    logger.error(f"移动视频失败 {current_path.name}: {e}")
        
        if organized_count > 0:
            self.save_index()
            logger.info(f"组织完成，移动了 {organized_count} 个视频文件")
        
        return organized_count
    
    def validate_videos(self) -> Dict[str, Dict]:
        """验证视频文件的完整性和可用性"""
        validation_results = {}
        
        for video_id, video_info in self.video_index['videos'].items():
            video_path = Path(video_info['full_path'])
            
            validation_result = {
                'exists': video_path.exists(),
                'size_match': False,
                'hash_match': False,
                'accessible': False,
                'issues': []
            }
            
            if not validation_result['exists']:
                validation_result['issues'].append('文件不存在')
            else:
                # 检查文件大小
                actual_size = video_path.stat().st_size
                expected_size = video_info.get('file_size', 0)
                
                if actual_size == expected_size:
                    validation_result['size_match'] = True
                else:
                    validation_result['issues'].append(f'文件大小不匹配: 期望{expected_size}, 实际{actual_size}')
                
                # 检查文件哈希(对大文件可选)
                if actual_size < 50 * 1024 * 1024:  # 小于50MB才计算哈希
                    actual_hash = self.calculate_file_hash(video_path)
                    expected_hash = video_info.get('file_hash', '')
                    
                    if actual_hash == expected_hash:
                        validation_result['hash_match'] = True
                    else:
                        validation_result['issues'].append('文件哈希值不匹配')
                
                # 检查文件可访问性
                try:
                    with open(video_path, 'rb') as f:
                        f.read(1024)  # 尝试读取前1KB
                    validation_result['accessible'] = True
                except Exception as e:
                    validation_result['issues'].append(f'文件不可访问: {str(e)}')
            
            validation_results[video_id] = validation_result
        
        return validation_results
    
    def get_videos_by_category(self, category: str) -> List[Dict]:
        """按类别获取视频列表"""
        videos = []
        for video_id, video_info in self.video_index['videos'].items():
            if video_info['category'] == category:
                videos.append({**video_info, 'id': video_id})
        return videos
    
    def get_videos_by_tags(self, tags: List[str]) -> List[Dict]:
        """按标签获取视频列表"""
        videos = []
        for video_id, video_info in self.video_index['videos'].items():
            video_tags = video_info.get('tags', [])
            if any(tag in video_tags for tag in tags):
                videos.append({**video_info, 'id': video_id})
        return videos
    
    def search_videos(self, query: str) -> List[Dict]:
        """搜索视频"""
        results = []
        query_lower = query.lower()
        
        for video_id, video_info in self.video_index['videos'].items():
            # 搜索文件名、描述、标签
            searchable_text = ' '.join([
                video_info.get('filename', ''),
                video_info.get('description', ''),
                ' '.join(video_info.get('tags', []))
            ]).lower()
            
            if query_lower in searchable_text:
                results.append({**video_info, 'id': video_id})
        
        return results
    
    def export_video_list(self, format_type: str = 'csv') -> str:
        """导出视频列表"""
        videos = []
        for video_id, video_info in self.video_index['videos'].items():
            videos.append({**video_info, 'id': video_id})
        
        if format_type == 'csv':
            import csv
            export_file = self.base_path / f'video_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            
            with open(export_file, 'w', newline='', encoding='utf-8') as f:
                if videos:
                    writer = csv.DictWriter(f, fieldnames=videos[0].keys())
                    writer.writeheader()
                    writer.writerows(videos)
            
            return str(export_file)
        
        elif format_type == 'json':
            export_file = self.base_path / f'video_export_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            
            with open(export_file, 'w', encoding='utf-8') as f:
                json.dump(videos, f, indent=2, ensure_ascii=False)
            
            return str(export_file)
        
        else:
            raise ValueError(f"不支持的导出格式: {format_type}")
    
    def generate_usage_report(self) -> Dict:
        """生成使用情况报告"""
        total_videos = len(self.video_index['videos'])
        total_size = sum(v.get('file_size', 0) for v in self.video_index['videos'].values())
        
        # 按类别统计
        category_stats = {}
        difficulty_stats = {}
        quality_stats = {}
        
        for video_info in self.video_index['videos'].values():
            # 类别统计
            category = video_info['category']
            if category not in category_stats:
                category_stats[category] = 0
            category_stats[category] += 1
            
            # 难度统计
            difficulty = video_info.get('difficulty', 'unknown')
            if difficulty not in difficulty_stats:
                difficulty_stats[difficulty] = 0
            difficulty_stats[difficulty] += 1
            
            # 质量统计
            quality = video_info.get('quality_score', 0)
            if quality >= 8:
                quality_level = 'high'
            elif quality >= 6:
                quality_level = 'medium' 
            else:
                quality_level = 'low'
            
            if quality_level not in quality_stats:
                quality_stats[quality_level] = 0
            quality_stats[quality_level] += 1
        
        return {
            'total_videos': total_videos,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'category_breakdown': category_stats,
            'difficulty_breakdown': difficulty_stats,
            'quality_breakdown': quality_stats,
            'storage_usage': {
                'base_path': str(self.base_path.absolute()),
                'categories': {k: len(list(v.glob('*'))) for k, v in self.categories.items()}
            },
            'last_updated': self.video_index['last_updated'],
            'generated_at': datetime.now().isoformat()
        }

def setup_test_video_environment():
    """设置测试视频环境的便捷函数"""
    print("🎬 设置测试视频环境...")
    
    # 创建视频资源管理器
    manager = VideoResourceManager()
    
    print("📁 创建目录结构...")
    # 目录已在初始化时创建
    
    print("🔄 生成合成测试视频...")
    synthetic_results = manager.generate_synthetic_videos()
    for video, status in synthetic_results.items():
        print(f"  {video}: {status}")
    
    print("📊 组织视频文件...")
    organized_count = manager.organize_videos_by_category()
    print(f"  组织了 {organized_count} 个视频文件")
    
    print("✅ 验证视频文件...")
    validation_results = manager.validate_videos()
    valid_count = sum(1 for r in validation_results.values() if r['exists'] and r['accessible'])
    print(f"  验证通过: {valid_count}/{len(validation_results)} 个视频")
    
    print("📈 生成使用报告...")
    report = manager.generate_usage_report()
    print(f"  总视频数: {report['total_videos']}")
    print(f"  总大小: {report['total_size_mb']} MB")
    print(f"  类别分布: {report['category_breakdown']}")
    
    print("🎯 测试视频环境设置完成!")
    print(f"📍 视频目录: {manager.base_path.absolute()}")
    
    return manager

if __name__ == "__main__":
    # 设置测试视频环境
    manager = setup_test_video_environment()
    
    # 显示可用的视频
    print("\n📋 可用测试视频:")
    for category, videos in manager.categories.items():
        videos_list = manager.get_videos_by_category(category)
        if videos_list:
            print(f"  {category}: {len(videos_list)} 个视频")
            for video in videos_list[:3]:  # 显示前3个
                print(f"    - {video['filename']} ({video['difficulty']})")
        else:
            print(f"  {category}: 暂无视频")