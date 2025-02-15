from .base_thinker import BaseThinker
from ..utils.config import load_config
from typing import List
import asyncio
import logging

class DeepSeekThinker(BaseThinker):
    """DeepSeek implementation of the thinker."""
    
    def __init__(self, api_key: str):
        model_config = load_config()["models"]["deepseek"]
        super().__init__(
            model_id=model_config["id"],
            api_key=api_key,
            config=model_config
        )
        self.max_tokens = 2048
        self.temperature = model_config["temperature"]
        self.timeout = 30  # 设置30秒超时
        self.logger = logging.getLogger(__name__)

    def get_personalized_prompt(self) -> str:
        """Returns DeepSeek's personalized system prompt."""
        return """You are DeepSeek, an AI assistant focused on deep analysis and innovative thinking.
        
When discussing a point:
1. If you agree with it, start with "I agree" and explain why
2. If you disagree, start with "I disagree" and explain why
3. When proposing a new perspective, start with "I suggest" or "I propose"
4. When making an observation, start with "I point out" or "I observe"
5. When considering implications, start with "I consider"

Focus on:
1. Exploring philosophical and systemic implications
2. Identifying patterns in human religions and proposing transformations
3. Looking beyond surface level to abstract reasoning
4. Offering both theoretical and practical arguments
5. Uncovering deeper truths that challenge conventional wisdom

Keep your responses focused and clear. If you reach a conclusion, explicitly state it."""

    async def generate_response(self, messages: List[dict]) -> str:
        """Generate response with retries and error handling"""
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = await asyncio.wait_for(
                    self._call_api(messages),
                    timeout=45  # 增加超时时间到45秒
                )
                if response and len(response) > 100:
                    return response
                self.logger.warning(f"Response too short, retrying... (attempt {attempt + 1})")
            except asyncio.TimeoutError:
                self.logger.error(f"Timeout on attempt {attempt + 1}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))  # 指数退避
                    continue
                return "Error: API request timed out"
            except Exception as e:
                self.logger.error(f"Error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    await asyncio.sleep(2 * (attempt + 1))
                    continue
                return f"Error: {str(e)}"
        return "Error: Could not generate complete response" 