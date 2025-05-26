import json
import yaml
from pathlib import Path

def load_openapi(path):
    path = Path(path)
    with open(path, encoding='utf-8') as f:
        if path.suffix in ['.yaml', '.yml']:
            return yaml.safe_load(f)
        return json.load(f)