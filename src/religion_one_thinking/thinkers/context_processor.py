import logging
from typing import List, Dict
from .base_thinker import BaseThinker
from ..utils.config import load_config
from ..utils.file_utils import read_round_data
import httpx
import os
import json

# 设置日志
logger = logging.getLogger(__name__)

def read_round_data(round_num: int) -> dict:
    """Read discussion data for a specific round"""
    try:
        file_path = f"discussions/round_{round_num}.json"
        if not os.path.exists(file_path):
            return None
            
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error reading round data: {str(e)}")
        return None

class ContextProcessor(BaseThinker):
    """Specialized thinker for processing discussion context and history."""
    
    def __init__(self, api_key: str):
        model_config = load_config()["models"]["context_processor"]
        super().__init__(
            model_id=model_config["id"],
            api_key=api_key,
            config=model_config
        )
        self.temperature = model_config["temperature"]
        self.max_tokens = model_config["max_tokens"]
        self.api_key = api_key

    def get_personalized_prompt(self) -> str:
        """Returns context processor's system prompt."""
        return self.config["system_prompt"]
        
    async def summarize_discussion(self, round_num: int) -> str:
        """Summarize the discussion from a specific round"""
        try:
            # 如果收到列表，尝试从中提取有用信息
            if isinstance(round_num, list):
                logger.warning(f"Received list instead of round number, attempting to process...")
                # 构建提示
                prompt = "Please summarize the following discussion points:\n\n"
                for response in round_num:
                    if isinstance(response, str):
                        prompt += f"- {response}\n"
                
                # 使用正确的系统提示
                system_prompt = self.get_personalized_prompt()
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                summary = await self._call_api(messages)
                return summary
                
            # 正常的轮次号处理
            round_data = read_round_data(round_num)
            if not round_data:
                raise ValueError(f"No data found for round {round_num}")
                
            # 构建提示
            prompt = f"Please summarize the following discussion points and responses:\n\n"
            for point in round_data.get("points", []):
                prompt += f"Point: {point['content']}\n"
                for response in point.get("agreements", []):
                    prompt += f"{response['author']} agrees: {response['content']}\n"
                for response in point.get("disagreements", []):
                    prompt += f"{response['author']} disagrees: {response['content']}\n"
                prompt += "\n"
                
            # 调用 API 获取总结
            messages = [
                {"role": "system", "content": self.get_personalized_prompt()},
                {"role": "user", "content": prompt}
            ]
            summary = await self._call_api(messages)
            return summary
            
        except Exception as e:
            logger.error(f"Error summarizing discussion: {str(e)}")
            raise

    async def generate_next_points(self, summary: str) -> List[str]:
        """Generate discussion points for the next round based on the summary"""
        try:
            prompt = f"Based on this summary of the previous discussion:\n{summary}\n\n"
            prompt += "Please generate 3-5 new discussion points that would deepen or expand the conversation."
            
            messages = [
                {"role": "system", "content": self.get_personalized_prompt()},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._call_api(messages)
            
            # 解析响应获取讨论点
            points = [point.strip() for point in response.split("\n") if point.strip()]
            return points
            
        except Exception as e:
            logger.error(f"Error generating next points: {str(e)}")
            raise

    async def analyze_patterns(self, discussion_history: list) -> str:
        """Analyze patterns and themes in discussion history."""
        prompt = (
            "Please analyze the following discussion history to identify key patterns, "
            "emerging themes, and potential areas for deeper exploration:\n\n"
        )
        for entry in discussion_history:
            prompt += f"- {entry}\n"
            
        messages = [
            {"role": "system", "content": self.get_personalized_prompt()},
            {"role": "user", "content": prompt}
        ]
        
        return await self.generate_response(messages)

    async def generate_discussion_points(self, prompt: str) -> List[str]:
        """生成下一轮的讨论点"""
        try:
            # 使用 GPT-4 来分析讨论并生成新的问题
            messages = [
                {"role": "system", "content": "You are a discussion moderator. Based on the previous responses, identify key points and generate 2-3 focused questions for the next round."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self._call_api(messages)
            
            # 解析响应，提取问题
            questions = [q.strip() for q in response.split('\n') if '?' in q]
            return questions if questions else None
            
        except Exception as e:
            print(f"Error generating discussion points: {str(e)}")
            return None
            
    async def _call_api(self, messages: List[dict]) -> str:
        """调用 OpenRouter API"""
        url = "https://openrouter.ai/api/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        data = {
            "model": "gpt-4",
            "messages": messages
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=data)
            if response.status_code == 200:
                return response.json()["choices"][0]["message"]["content"] 

    def _build_messages(self, prompt: str) -> List[Dict[str, str]]:
        """构建 API 消息格式"""
        return [
            {"role": "system", "content": self.get_personalized_prompt()},
            {"role": "user", "content": prompt}
        ] 