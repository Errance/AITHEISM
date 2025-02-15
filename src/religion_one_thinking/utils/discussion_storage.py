from typing import Dict
import json
from datetime import datetime

class DiscussionStorage:
    def save_round(self, round_num: int, discussion_data: Dict):
        """保存完整的讨论记录到文件"""
        filename = f"discussions/round_{round_num}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(filename, 'w') as f:
            json.dump(discussion_data, f, indent=2) 