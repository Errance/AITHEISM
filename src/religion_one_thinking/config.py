import yaml
from pathlib import Path
from .utils.config_validator import validate_config

def load_config():
    """Load and validate configuration"""
    config_path = Path(__file__).parent / "config" / "config.yaml"
    with open(config_path, "r", encoding="utf-8") as f:
        config = yaml.safe_load(f)
    
    # Validate configuration
    validate_config(config)
    
    # Ensure required directories exist
    Path(config["discussion"]["save_path"]).mkdir(parents=True, exist_ok=True)
    Path(config["logging"]["file_path"]).parent.mkdir(parents=True, exist_ok=True)
    
    return config 