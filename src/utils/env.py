 1: """Environment variable resolver for ${VAR} placeholders."""
 2: 
 3: import os
 4: import re
 5: from dotenv import load_dotenv
 6: 
 7: 
 8: def load_env(env_path: str = ".env") -> None:
 9:     """Load .env file if it exists."""
10:     if os.path.exists(env_path):
11:         load_dotenv(env_path)
12: 
13: 
14: def resolve_env_vars(value: str) -> str:
15:     """Replace ${VAR_NAME} placeholders with environment variable values.
16:     
17:     If the variable is not set, returns the original placeholder unchanged.
18:     """
19:     if not isinstance(value, str):
20:         return value
21: 
22:     pattern = re.compile(r"\$\{(\w+)\}")
23: 
24:     def replacer(match):
25:         var_name = match.group(1)
26:         env_val = os.environ.get(var_name)
27:         if env_val is not None:
28:             return env_val
29:         return match.group(0)  # keep original if not found
30: 
31:     return pattern.sub(replacer, value)
32: 
33: 
34: def resolve_dict(obj):
35:     """Recursively resolve ${VAR} placeholders in nested dicts/lists."""
36:     if isinstance(obj, dict):
37:         return {k: resolve_dict(v) for k, v in obj.items()}
38:     elif isinstance(obj, list):
39:         return [resolve_dict(item) for item in obj]
40:     elif isinstance(obj, str):
41:         return resolve_env_vars(obj)
42:     return obj
