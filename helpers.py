from pathlib import Path
import os
import yaml

ACTION_PATH = Path(os.getenv("GITHUB_ACTION_PATH", Path(__file__).parent))
REPO_PATH = Path.cwd()


def load_yaml(path: Path):
    if not path.exists():
        return {}

    with path.open("r", encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def merge(default: dict, user: dict) -> dict:
    result = default.copy()

    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = merge(result[key], value)
        else:
            result[key] = value

    return result
