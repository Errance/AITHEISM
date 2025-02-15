from pathlib import Path
import yaml

def load_config():
    config_path = Path(__file__).parent.parent / "config" / "config.yaml"
    with open(config_path) as f:
        return yaml.safe_load(f)

def load_model_config():
    return load_config()["models"]