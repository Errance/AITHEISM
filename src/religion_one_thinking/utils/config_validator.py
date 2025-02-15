from typing import Dict, Any
from pathlib import Path

def validate_config(config: Dict[str, Any]):
    """Validate configuration structure"""
    required_sections = [
        "api",
        "discussion",
        "logging",
        "models"
    ]  # 移除 "memory"

    for section in required_sections:
        if section not in config:
            raise ValueError(f"Missing required section: {section}")

    # Validate API configuration
    if "openrouter" not in config["api"]:
        raise ValueError("Missing OpenRouter configuration")

    # Validate models configuration
    required_models = ["gpt", "claude", "gemini", "deepseek", "qwen", "context_processor"]
    for model in required_models:
        if model not in config["models"]:
            raise ValueError(f"Missing model configuration: {model}")

    # Check OpenRouter configuration
    openrouter_config = config["api"]["openrouter"]
    required_fields = [
        "base_url",
        "max_tokens",
        "temperature",
        "retry_attempts",
        "retry_delay",
        "timeout"
    ]
    
    for field in required_fields:
        if field not in openrouter_config:
            raise ValueError(f"Missing required OpenRouter field: {field}")

    required_discussion_fields = ["max_rounds", "summary_interval", "save_path"]
    required_logging_fields = ["level", "file_path"]
    
    # Check discussion configuration
    discussion_config = config["discussion"]
    if not all(field in discussion_config for field in required_discussion_fields):
        raise ValueError("Incomplete discussion configuration")
    
    # Check logging configuration
    logging_config = config["logging"]
    if not all(field in logging_config for field in required_logging_fields):
        raise ValueError("Incomplete logging configuration")
    
    return True 