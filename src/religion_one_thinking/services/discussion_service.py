from typing import Optional, List, Dict
from datetime import datetime
from pathlib import Path
import json
from ..utils.discussion_manager import DiscussionManager

class DiscussionService:
    """服务层：管理讨论状态和进度"""
    
    def __init__(self):
        self.orchestrator = DiscussionManager.get_orchestrator()
        
    async def get_current_state(self) -> Dict:
        """获取当前讨论状态"""
        try:
            # 从最新的讨论文件中读取状态
            latest_round = self._get_latest_round_file()
            if latest_round:
                with open(latest_round, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                return {
                    'round_num': data['round_num'],
                    'status': data['status'],
                    'points': data['points'],
                    'messages': self._get_round_messages(data),
                    'timestamp': data['timestamp']
                }
            return {
                'round_num': 0,
                'status': 'not_started',
                'points': [],
                'messages': [],
                'timestamp': None
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
        """从讨论数据中提取消息"""
        messages = []
        for point in data['points']:
            for response in point.get('agreements', []) + point.get('disagreements', []):
                messages.append({
                    'model': response['author'],
                    'content': response['content'],
                    'timestamp': response.get('timestamp', data['timestamp']),
                    'round_num': point['round_num']
                })
        return messages 