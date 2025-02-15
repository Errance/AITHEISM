from typing import List, Dict, Any, Optional
from datetime import datetime
import json
from pathlib import Path
import tiktoken

class MemoryAgent:
    """Manages conversation memory and context retrieval"""
    
    def __init__(self, save_path: Optional[str] = None):
        """
        Initialize memory agent.
        
        Args:
            save_path: Path to save memory files. Defaults to "memories"
        """
        self.memories = []  # Store conversation records
        self.save_path = Path(save_path or "memories")
        self.save_path.mkdir(parents=True, exist_ok=True)
        self.max_memories = 100
        
    def add_memory(self, content: str, author: str, round_num: int, 
                  memory_type: str = "discussion"):
        """
        Add new memory record.
        
        Args:
            content: Content of the memory
            author: Author of the content
            round_num: Discussion round number
            memory_type: Type of memory (discussion/key_argument/unresolved)
        """
        memory = {
            "content": content,
            "author": author,
            "round": round_num,
            "type": memory_type,
            "timestamp": datetime.utcnow().isoformat()
        }
        self.memories.append(memory)
        
        # Maintain memory limit
        if len(self.memories) > self.max_memories:
            self.memories = self.memories[-self.max_memories:]
            
        self._save_memory(memory)
        
    def get_round_discussion(self, round_num: int) -> List[Dict[str, str]]:
        """Get all memories from a specific round"""
        return [m for m in self.memories if m["round"] == round_num]
        
    def _save_memory(self, memory: Dict[str, Any]):
        """Save memory to file"""
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        save_file = self.save_path / f"memory_{timestamp}.json"
        with open(save_file, "w", encoding="utf-8") as f:
            json.dump(memory, f, ensure_ascii=False, indent=2)

    def get_recent_discussion(self, limit: int = 5) -> List[str]:
        """Get recent discussion records"""
        recent_memories = [
            m["content"] for m in self.memories 
            if m["type"] == "discussion"
        ]
        return recent_memories[-limit:]

    def get_memory_by_type(self, memory_type: str) -> List[str]:
        """Get memories of specified type"""
        return [
            m["content"] for m in self.memories 
            if m["type"] == memory_type
        ]

    def get_context_summary(self, max_chars: int = 2000) -> str:
        """
        Get summarized context from memory.
        
        Args:
            max_chars: Maximum characters in summary
        
        Returns:
            Formatted context summary
        """
        recent_discussion = self.get_recent_discussion()
        key_arguments = self.get_memory_by_type("key_arguments")
        
        char_count = 0
        summary_parts = []
        
        # Add recent discussion
        if recent_discussion:
            summary_parts.append("Recent discussion:")
            for disc in recent_discussion[-2:]:  # Last 2 discussions
                first_sentence = disc.split('.')[0]
                chars = len(first_sentence)
                if char_count + chars > max_chars * 0.6:  # Use 60% for discussion
                    break
                summary_parts.append(f"- {first_sentence}")
                char_count += chars
        
        # Add key arguments
        if key_arguments and char_count < max_chars * 0.9:  # Leave 10% buffer
            summary_parts.append("\nKey arguments:")
            for arg in key_arguments[-3:]:  # Last 3 key arguments
                first_sentence = arg.split('.')[0]
                chars = len(first_sentence)
                if char_count + chars > max_chars:
                    break
                summary_parts.append(f"- {first_sentence}")
                char_count += chars
        
        return "\n".join(summary_parts)