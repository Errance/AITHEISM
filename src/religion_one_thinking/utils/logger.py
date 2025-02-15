from datetime import datetime
import logging
from pathlib import Path
from typing import Optional

class DiscussionLogger:
    """Logger for AI Religion Discussion"""
    
    def __init__(self):
        self.log_dir = Path("logs")
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / f"discussion_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.log"
        
        # 设置日志格式
        logging.basicConfig(
            filename=str(self.log_file),
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger("AI_Religion_Discussion")
        
    def log_round_start(self, round_num: int):
        """记录轮次开始"""
        self.logger.info(f"Starting round {round_num}")
        
    def log_response(self, thinker: str, point: str, response: str):
        """记录 AI 的回复"""
        self.logger.info(f"{thinker} responding to: {point[:100]}...")
        self.logger.info(f"Response: {response[:200]}...")
        
    def log_error(self, error_msg: str):
        """记录错误"""
        self.logger.error(f"Error occurred: {error_msg}")
        
    def log_summary(self, round_num: int, summary: str):
        """记录轮次总结"""
        self.logger.info(f"Round {round_num} summary:")
        self.logger.info(summary) 