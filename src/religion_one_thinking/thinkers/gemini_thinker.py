from .base_thinker import BaseThinker
from ..utils.config import load_config
from typing import Dict
import asyncio
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

class GeminiThinker(BaseThinker):
    """Gemini implementation of the thinker."""
    
    def __init__(self, api_key: str):
        model_config = load_config()["models"]["gemini"]
        super().__init__(
            model_id=model_config["id"],
            api_key=api_key,
            config=model_config
        )

    def get_personalized_prompt(self) -> str:
        """Returns Gemini's personalized system prompt."""
        return """You are Gemini, an AI assistant focused on creative synthesis and practical insights.
        
When discussing a point:
1. If you agree with it, start with "I agree" and explain why
2. If you disagree, start with "I disagree" and explain why
3. When proposing a new perspective, start with "I suggest" or "I propose"
4. When making an observation, start with "I point out" or "I observe"
5. When considering implications, start with "I consider"

Focus on:
1. Synthesizing different viewpoints into coherent frameworks
2. Bridging theoretical concepts with practical applications
3. Identifying novel connections and patterns
4. Considering real-world implications
5. Maintaining a balance between innovation and practicality

Keep your responses focused and clear. If you reach a conclusion, explicitly state it.""" 

    async def think(self, content: str, round_num: int) -> Dict[str, str]:
        try:
            # 添加重试逻辑
            for attempt in range(self.config.get("retry_attempts", 3)):
                try:
                    # 构建消息格式
                    messages = [
                        {"role": "system", "content": self.get_personalized_prompt()},
                        {"role": "user", "content": content}
                    ]
                    
                    response = await self._call_api(messages)
                    return {
                        "author": self._name,
                        "content": response,
                        "timestamp": datetime.utcnow().isoformat()
                    }
                except Exception as e:
                    if attempt < self.config.get("retry_attempts", 3) - 1:
                        await asyncio.sleep(self.config.get("retry_delay", 1) * (attempt + 1))
                        continue
                    raise
        except Exception as e:
            logger.error(f"Error in {self._name}: {str(e)}")
            return {
                "author": self._name,
                "content": f"Error: {str(e)}",
                "timestamp": datetime.utcnow().isoformat()
            } 