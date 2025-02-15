import os
import json
import logging

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