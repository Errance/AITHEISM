from typing import Dict, Optional, List
from datetime import datetime

class DiscussionPoint:
    """Discussion point node"""
    def __init__(self, content: str, round_num: int, timestamp: datetime = None, agreements: List[Dict] = None, disagreements: List[Dict] = None, participants: List[str] = None):
        self.id = f"point_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        self.content = content  # 移除前缀，保持原始内容
        self.round_num = round_num
        self.timestamp = timestamp or datetime.utcnow()
        self.status = "ongoing"  # Status: 'ongoing', 'concluded'
        self.conclusion = None
        self.discussion_refs = []
        self.agreements = agreements or []
        self.disagreements = disagreements or []
        self.consensus_score = 0.0
        self.participants = participants or []
        self.point_type = None

    def __str__(self):
        return self.content
        
    def __repr__(self):
        return self.content

    def add_response(self, response: Dict[str, str]):
        """Add an AI's response"""
        author = response["author"]
        content = response["content"]
        self.participants.add(author)
        
        # Analyze response type
        if self._is_agreement(content):
            self.agreements.append({"author": author, "content": content})
        elif self._is_disagreement(content):
            self.disagreements.append({"author": author, "content": content})
            
        self._calculate_consensus()

    # ... (其他方法保持不变) 