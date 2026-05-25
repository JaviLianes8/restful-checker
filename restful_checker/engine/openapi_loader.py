import json
import yaml
from pathlib import Path

def load_openapi(path):
    """
    Load an OpenAPI specification from a JSON or YAML file.

    Args:
        path (str or Path): Path to the OpenAPI file.

    Returns:
        dict: Parsed OpenAPI content as a Python dictionary.

    Raises:
        ValueError: If the file extension is not supported.
        FileNotFoundError: If the file does not exist.
    """
    path = Path(path)
    suffix = path.suffix.lower()

    with open(path, encoding='utf-8') as f:
        if suffix in ('.yaml', '.yml'):
            return yaml.safe_load(f)
        elif suffix == '.json':
            return json.load(f)
        else:
            raise ValueError(f"Unsupported file extension: {suffix}")