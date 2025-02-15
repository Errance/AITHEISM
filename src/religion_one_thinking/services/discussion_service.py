from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import json
from ..utils.discussion_manager import DiscussionManager

class DiscussionService:
    """服务层：管理讨论状态和进度"""
    
    def __init__(self):
        self.orchestrator = DiscussionManager.get_orchestrator()
        
    async def get_current_state(self, page_size: int = 20, page: int = 1) -> Dict:
        """获取当前讨论状态
        
        Args:
            page_size: Number of messages per page
            page: Page number (1-based)
        """
        try:
            latest_round = self._get_latest_round_file()
            if latest_round:
                with open(latest_round, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                
                all_messages = self._get_round_messages(data)
                total_messages = len(all_messages)
                start_idx = (page - 1) * page_size
                end_idx = start_idx + page_size
                
                return {
                    'round_num': data['round_num'],
                    'status': data['status'],
                    'points': data['points'],
                    'messages': all_messages[start_idx:end_idx],
                    'timestamp': data['timestamp'],
                    'pagination': {
                        'total': total_messages,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': (total_messages + page_size - 1) // page_size
                    }
                }
            return {
                'round_num': 0,
                'status': 'not_started',
                'points': [],
                'messages': [],
                'timestamp': None,
                'pagination': {
                    'total': 0,
                    'page': 1,
                    'page_size': page_size,
                    'total_pages': 0
                }
            }
        except Exception as e:
            print(f"Error getting discussion state: {str(e)}")
            raise
            
    def _get_latest_round_file(self) -> Optional[Path]:
        """获取最新的讨论文件"""
        discussion_dir = Path('discussions')
        if not discussion_dir.exists():
            return None
            
        round_files = list(discussion_dir.glob('round_*.json'))
        if not round_files:
            return None
            
        return max(round_files, key=lambda p: int(p.stem.split('_')[1]))
        
    def _get_round_messages(self, data: Dict) -> List[Dict]:
        """从讨论数据中提取消息，按时间戳排序"""
        messages = []
        for point in data['points']:
            for response in point.get('agreements', []) + point.get('disagreements', []):
                messages.append({
                    'model': response['author'],
                    'content': response['content'],
                    'timestamp': response.get('timestamp', data['timestamp']),
                    'round_num': point['round_num']
                })
        
        # Sort messages by timestamp in descending order (newest first)
        messages.sort(key=lambda x: x['timestamp'], reverse=True)
        return messages

    async def get_more_messages(self, page_size: int = 20, page: int = 1) -> Dict:
        """获取更多消息用于无限滚动
        
        Args:
            page_size: Number of messages per page
            page: Page number (1-based)
            
        Returns:
            Dict containing messages and pagination info
        """
        try:
            latest_round = self._get_latest_round_file()
            if not latest_round:
                return {
                    'messages': [],
                    'pagination': {
                        'total': 0,
                        'page': page,
                        'page_size': page_size,
                        'total_pages': 0
                    }
                }
                
            with open(latest_round, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            all_messages = self._get_round_messages(data)
            total_messages = len(all_messages)
            start_idx = (page - 1) * page_size
            end_idx = start_idx + page_size
            
            return {
                'messages': all_messages[start_idx:end_idx],
                'pagination': {
                    'total': total_messages,
                    'page': page,
                    'page_size': page_size,
                    'total_pages': (total_messages + page_size - 1) // page_size
                }
            }
        except Exception as e:
            print(f"Error getting more messages: {str(e)}")
            raise