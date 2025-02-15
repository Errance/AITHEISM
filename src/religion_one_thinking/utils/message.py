from pydantic import BaseModel
from typing import Optional, Dict, Any
from datetime import datetime

class Message(BaseModel):
    """Represents a conversation message"""
    role: str
    content: str
    point_id: Optional[str] = None
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "content": self.content,
            "point_id": self.point_id,
            "timestamp": self.timestamp.isoformat()
        } 