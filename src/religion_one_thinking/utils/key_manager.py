from typing import List, Optional
import os
from dotenv import load_dotenv
import logging

logger = logging.getLogger(__name__)

class KeyManager:
    def __init__(self):
        self.keys = []
        self.current_index = 0
        self.load_keys()

    def load_keys(self):
        """从 .env 文件加载 API keys"""
        try:
            load_dotenv()
            
            # 加载 API key
            api_key = os.getenv('OPENROUTER_API_KEY')
            if api_key:
                self.keys.append(api_key)
                logger.info("Loaded API key successfully")
                return
            else:
                logger.error("No API key found in .env file")
                raise ValueError("No API key found. Please set OPENROUTER_API_KEY in .env file")
                
        except Exception as e:
            logger.error(f"Error loading API key: {str(e)}")
            raise

    def get_current_key(self) -> str:
        """获取当前的 API key"""
        if not self.keys:
            raise ValueError("No API key available")
        return self.keys[self.current_index]

    def switch_to_next_key(self) -> Optional[str]:
        """切换到下一个可用的 key"""
        if not self.keys:
            return None
        self.current_index = (self.current_index + 1) % len(self.keys)
        return self.get_current_key()