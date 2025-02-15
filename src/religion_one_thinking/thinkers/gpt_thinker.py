from .base_thinker import BaseThinker
from ..utils.config import load_config
import json
from typing import List
import os

class GPTThinker(BaseThinker):
    """GPT implementation of the thinker."""
    
    def __init__(self, api_key: str):
        model_config = load_config()["models"]["gpt"]
        super().__init__(
            model_id=model_config["id"],
            api_key=api_key,
            config=model_config
        )
        
        # 确保记忆目录存在
        memory_dir = "memories/gpt"
        os.makedirs(memory_dir, exist_ok=True)
        self.memory_file = os.path.join(memory_dir, "memories.json")
        
        # 加载已有记忆
        self.memories = self._load_memories()

    def get_personalized_prompt(self) -> str:
        """Returns GPT's personalized system prompt."""
        return """You are GPT-4, an AI focused on deep analysis and philosophical discussion.
        After each response, reflect on key insights and save them as memories.
        
        When discussing:
        1. Start with clear position ("I agree/disagree/propose")
        2. Provide structured analysis
        3. Consider multiple perspectives
        4. Draw logical conclusions
        5. End with key memories/insights
        
        Format memories as:
        MEMORIES:
        - [Memory 1]
        - [Memory 2]
        """

    async def generate_response(self, messages: List[dict]) -> str:
        response = await super().generate_response(messages)
        
        # 提取记忆
        if "MEMORIES:" in response:
            memories_section = response.split("MEMORIES:")[1].strip()
            new_memories = [m.strip("- ").strip() for m in memories_section.split("\n") if m.strip()]
            self.memories.extend(new_memories)
            
        return response 

    def _load_memories(self) -> List[str]:
        """Load existing memories from file"""
        if os.path.exists(self.memory_file):
            with open(self.memory_file, "r") as f:
                return json.load(f)
        return []

    def _save_memories(self):
        """Save memories to file"""
        with open(self.memory_file, "w") as f:
            json.dump(self.memories, f, indent=2) 