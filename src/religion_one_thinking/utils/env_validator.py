import os
from typing import List

def validate_env_vars():
    """Validate required environment variables"""
    required_vars = ["OPENROUTER_API_KEY"]
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        raise ValueError(f"Missing required environment variables: {', '.join(missing_vars)}")
        
    # Validate API key format
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key.startswith("sk-or-"):
        raise ValueError("Invalid OpenRouter API key format") 