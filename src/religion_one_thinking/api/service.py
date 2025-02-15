from typing import List, Optional
from datetime import datetime
from ..discussion.orchestrator import DiscussionOrchestrator
from ..discussion.discussion_chain import DiscussionChain
from ..utils.config import load_config
import asyncio
from ..utils.discussion_manager import DiscussionManager
from ..services.discussion_service import DiscussionService

class APIService:
    """Service layer between API and discussion system"""
    
    def __init__(self):
        self.orchestrator = DiscussionManager.get_orchestrator()
        self.config = load_config()
        self.discussion_chain = None
        self.current_round = 0
        self.round_start_time = None
        self.round_duration = 180  # 3 minutes in seconds
        self.discussion_service = DiscussionService()
        
    async def get_current_discussion(self, round_num: Optional[int] = None, page: int = 1, page_size: int = 20) -> dict:
        """获取当前或指定轮次的讨论
        
        Args:
            round_num: Optional round number to get discussion for
            page: Page number for messages (1-based)
            page_size: Number of messages per page
        """
        try:
            state = await self.discussion_service.get_current_state(page_size=page_size, page=page)
            return {
                "messages": state['messages'],
                "currentRound": state['round_num'],
                "roundStatus": state['status'],
                "nextRoundStart": datetime.utcnow() if state['status'] == "completed" else None,
                "remainingTime": 0,
                "pagination": state['pagination']
            }
        except Exception as e:
            print(f"Error in get_current_discussion: {str(e)}")
            raise
        
    async def get_more_messages(self, page: int = 1, page_size: int = 20) -> dict:
        """获取更多消息用于无限滚动
        
        Args:
            page: Page number (1-based)
            page_size: Number of messages per page
        """
        try:
            return await self.discussion_service.get_more_messages(page_size=page_size, page=page)
        except Exception as e:
            print(f"Error in get_more_messages: {str(e)}")
            raise
        
    async def get_discussion_nodes(self) -> List[dict]:
        """Get all discussion nodes"""
        if not self.discussion_chain:
            return []
            
        nodes = []
        for point in self.discussion_chain.points:
            nodes.append({
                "id": hash(point.id),
                "argument": point.content[:100],
                "size": len(point.agreements) + len(point.disagreements),
                "roundNum": point.round_num,
                "status": point.status
            })
        return nodes
        
    async def get_node_history(self, node_id: int, cursor: Optional[str] = None) -> dict:
        """Get history for a specific node"""
        if not self.discussion_chain:
            return {"messages": [], "hasMore": False, "nextCursor": None, "roundNum": 0}
            
        point = next((p for p in self.discussion_chain.points if hash(p.id) == node_id), None)
        if not point:
            return {"messages": [], "hasMore": False, "nextCursor": None, "roundNum": 0}
            
        messages = []
        for response in point.agreements + point.disagreements:
            messages.append({
                "model": response["author"],
                "content": response["content"],
                "createdAt": datetime.utcnow(),
                "roundNum": point.round_num
            })
            
        return {
            "messages": messages,
            "hasMore": False,
            "nextCursor": None,
            "roundNum": point.round_num
        } 