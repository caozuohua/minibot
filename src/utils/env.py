"""Environment variable resolver for ${VAR} placeholders."""

import os
import re

from dotenv import load_dotenv


def load_env(env_path: str = ".env") -> None:
    """Load .env file if it exists."""
    if os.path.exists(env_path):
        load_dotenv(env_path)


def resolve_env_vars(value: str) -> str:
    """Replace ${VAR_NAME} placeholders with environment variable values.

    If the variable is not set, returns the original placeholder unchanged.
    """
    if not isinstance(value, str):
        return value

    pattern = re.compile(r"\$\{(\w+)\}")

    def replacer(match):
        var_name = match.group(1)
        env_val = os.environ.get(var_name)
        if env_val is not None:
            return env_val
        return match.group(0)  # keep original if not found

    return pattern.sub(replacer, value)


def resolve_dict(obj):
    """Recursively resolve ${VAR} placeholders in nested dicts/lists."""
    if isinstance(obj, dict):
        return {k: resolve_dict(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [resolve_dict(item) for item in obj]
    elif isinstance(obj, str):
        return resolve_env_vars(obj)
    return obj
