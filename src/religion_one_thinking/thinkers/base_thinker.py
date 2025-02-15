import asyncio
import json
import re
from abc import ABC, abstractmethod
from typing import List, Dict, TypedDict, Any, Optional
from pydantic import BaseModel
from openai import AsyncOpenAI
from datetime import datetime
from ..utils.message import Message
from ..utils.config import load_config
import logging
import aiohttp
import httpx


class Response(TypedDict):
    """Type definition for AI responses."""
    author: str
    content: str
    timestamp: str
    metadata: Dict[str, Any]


class BaseThinker(ABC):
    """
    Base class for AI thinkers in the religious debate system.
    
    This class provides the foundation for different AI models to participate
    in philosophical discussions about AI-created religions.
    
    Attributes:
        model_id (str): Full model identifier (e.g., "openai/gpt-4")
        api_key (str): OpenRouter API key
        max_rounds (int): Maximum number of discussion rounds
        conversation_history (List[Message]): History of the conversation
    """

    def __init__(self, model_id: str, api_key: str, config: dict):
        """
        Initialize the AI thinker.
        
        Args:
            model_id: Full model identifier (e.g., "openai/gpt-4")
            api_key: OpenRouter API key
            config: Configuration dictionary
        """
        self.model_id = model_id
        self.api_key = api_key
        self.config = config
        self._name = config.get("name", model_id)
        self.max_rounds = config.get("max_rounds", 10)
        self.conversation_history = []
        
        # Only create memory for regular thinkers
        if not self._is_context_processor():
            from ..utils.memory_agent import MemoryAgent
            self.memory = MemoryAgent(save_path=f"memories/{self._name}")
        
        self.max_history = 5
        self.context_summary = ""
        self.personalized_prompt = self._load_personalized_prompt()
        # 初始化 logger
        self.logger = logging.getLogger(__name__)

    def _is_context_processor(self) -> bool:
        """Check if this thinker is the context processor"""
        full_config = load_config()
        return self.model_id == full_config["models"]["context_processor"]["id"]

    def _load_personalized_prompt(self) -> str:
        """Load the personalized system prompt"""
        if self._is_context_processor():
            full_config = load_config()
            return full_config["models"]["context_processor"]["system_prompt"]
        return self.get_personalized_prompt()

    def add_to_history(self, role: str, content: str):
        """Add a message to conversation history."""
        self.conversation_history.append(Message(role=role, content=content))

    @abstractmethod
    def get_personalized_prompt(self) -> str:
        """Return the personalized system prompt for this thinker."""
        pass

    def _summarize_history(self) -> str:
        """Summarize key points from historical dialogue"""
        if len(self.conversation_history) <= 2:  # Only system prompt and one round
            return ""
            
        # Skip system prompt, only summarize dialogue content
        dialogue = self.conversation_history[1:]
        summary = "Previous key points:\n"
        for msg in dialogue[-6:-1]:  # Summarize rounds 2-6 from the end
            if msg.role == "assistant":
                # Extract first sentence as key point
                first_sentence = msg.content.split('.')[0]
                summary += f"- {first_sentence}\n"
        return summary

    async def think(self, point: str, round_num: int = 1) -> dict:
        """Think about a discussion point and return response"""
        try:
            # 确保 point 是字符串
            point_str = str(point) if not isinstance(point, str) else point
            
            # 构建消息
            messages = [
                {"role": "system", "content": self.personalized_prompt},
                {"role": "user", "content": point_str}
            ]
            
            # 调用 API
            response = await self.generate_response(messages)
            
            # 返回标准格式的响应
            return {
                "author": self._name,
                "content": response,
                "round_num": round_num,
                "type": "response"  # 默认类型
            }
            
        except Exception as e:
            self.logger.log_error(f"Error in {self._name}: {str(e)}")
            raise

    async def _call_api(self, messages: List[dict]) -> str:
        """调用 OpenRouter API"""
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            try:
                async with httpx.AsyncClient(timeout=30.0) as client:
                    # 构建请求参数
                    payload = {
                        "model": self.model_id,
                        "messages": messages,
                        "temperature": self.config["temperature"],
                    }
                    
                    # 只对特定模型添加 max_tokens
                    if any(model in self.model_id.lower() for model in ["gpt", "claude"]):
                        payload["max_tokens"] = self.config.get("max_tokens", 2048)
                    
                    response = await client.post(
                        "https://openrouter.ai/api/v1/chat/completions",
                        headers={
                            "Authorization": f"Bearer {self.api_key}",
                            "HTTP-Referer": "https://github.com/Errance/AITHEISM",
                            "X-Title": "AITHEISM",
                            "Content-Type": "application/json"
                        },
                        json=payload
                    )
                    
                    if response.status_code == 200:
                        data = response.json()
                        if "choices" in data and len(data["choices"]) > 0:
                            content = data["choices"][0]["message"]["content"]
                            if content and len(content.strip()) > 0:
                                return content
                    
                    self.logger.error(f"Invalid response on attempt {attempt + 1}: {response.text}")
                    
                delay = base_delay * (2 ** attempt)
                self.logger.info(f"Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                
            except Exception as e:
                self.logger.error(f"API call error on attempt {attempt + 1}: {str(e)}")
                if attempt < max_retries - 1:
                    delay = base_delay * (2 ** attempt)
                    self.logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
                else:
                    raise
        
        return "Error: No valid response after retries"

    def recall_memory(self):
        """Get AI's past discussion memories"""
        recent_discussion = self.memory.get_recent_discussion()
        resolved_arguments = self.memory.get_memory_by_type("key_arguments")
        unresolved_themes = self.memory.get_memory_by_type("unresolved")
        return recent_discussion, resolved_arguments, unresolved_themes

    def _get_context(self) -> str:
        """Get controlled context summary"""
        recent_discussion = self.memory.get_recent_discussion()
        key_arguments = self.memory.get_memory_by_type("key_arguments")
        
        char_count = 0
        summary_parts = []
        
        # Add recent discussion
        if recent_discussion:
            summary_parts.append("Recent discussion:")
            for disc in recent_discussion[-2:]:
                first_sentence = disc.split('.')[0]
                chars = len(first_sentence)
                if char_count + chars > 2400:  # 60% of 4000 chars limit
                    break
                summary_parts.append(f"- {first_sentence}")
                char_count += chars
        
        # Add key arguments
        if key_arguments and char_count < 3600:  # Ensure enough space
            summary_parts.append("\nKey arguments:")
            for arg in key_arguments[-3:]:
                first_sentence = arg.split('.')[0]
                chars = len(first_sentence)
                if char_count + chars > 4000:
                    break
                summary_parts.append(f"- {first_sentence}")
                char_count += chars
        
        return "\n".join(summary_parts)

    async def generate_response(self, messages: List[Dict[str, str]], max_retries: int = 3) -> Optional[str]:
        """Generate a response using the OpenRouter API."""
        config = load_config()["api"]["openrouter"]
        client = AsyncOpenAI(
            base_url=config["base_url"],
            api_key=self.api_key,
            timeout=float(config["timeout"]),
            default_headers=config["headers"]
        )
        
        for attempt in range(max_retries):
            try:
                start_time = datetime.now()
                completion = await client.chat.completions.create(
                    model=self.model_id,
                    messages=messages,
                    max_tokens=config["max_tokens"],
                    temperature=config["temperature"]
                )
                
                if not completion or not completion.choices:
                    if attempt < max_retries - 1:
                        print(f"No response from {self._name}, retrying...")
                        await asyncio.sleep(1)
                        continue
                    return f"Error: No response from {self._name}"
                
                response = completion.choices[0].message.content
                latency = (datetime.now() - start_time).total_seconds()
                print(f"\nAPI call successful - Model: {self._name}, Latency: {latency:.2f}s")
                return response
                
            except Exception as e:
                if attempt < max_retries - 1:
                    print(f"Error with {self._name}, retrying: {str(e)}")
                    await asyncio.sleep(1)
                    continue
                return f"Error in API call: {str(e)}"

    @property
    def name(self) -> str:
        """Get the AI's name."""
        return self._name