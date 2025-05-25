import json

def load_openapi(path):
    with open(path, encoding='utf-8') as f:
        return json.load(f)