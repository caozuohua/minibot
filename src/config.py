 1: """Configuration loader for MiniBot."""
 2: 
 3: import os
 4: import yaml
 5: from dataclasses import dataclass, field
 6: from typing import List, Dict, Any, Optional
 7: 
 8: from src.utils.env import load_env, resolve_dict
 9: 
10: 
11: @dataclass
12: class ProviderConfig:
13:     name: str
14:     api_key: str
15:     base_url: Optional[str] = None
16:     models: Dict[str, str] = field(default_factory=dict)
17: 
18: 
19: @dataclass
20: class ModelConfig:
21:     providers: List[ProviderConfig] = field(default_factory=list)
22:     default_provider: str = "openai"
23: 
24: 
25: @dataclass
26: class LarkConfig:
27:     app_id: str = ""
28:     app_secret: str = ""
29: 
30: 
31: @dataclass
32: class MemoryConfig:
33:     db_path: str = "./data/memory.db"
34:     top_k: int = 5
35:     decay_rate: float = 0.02
36:     archive_threshold: float = 0.1
37:     cleanup_days: int = 90
38: 
39: 
40: @dataclass
41: class AgentConfig:
42:     max_iterations: int = 20
43:     timeout_minutes: int = 30
44:     reflection_max_rounds: int = 3
45:     tot_branches: int = 3
46:     tot_depth: int = 3
47: 
48: 
49: @dataclass
50: class ToolConfig:
51:     shell_timeout: int = 30
52:     output_max_bytes: int = 10240
53:     work_dir: str = "./workspace"
54:     search_backend: str = "tavily"
55:     search_api_key: str = ""
56: 
57: 
58: @dataclass
59: class SkillConfig:
60:     dir: str = "./skills"
61: 
62: 
63: @dataclass
64: class LoggingConfig:
65:     level: str = "INFO"
66:     file: str = "./data/minibot.log"
67: 
68: 
69: @dataclass
70: class Config:
71:     """Root configuration object."""
72:     lark: LarkConfig = field(default_factory=LarkConfig)
73:     models: ModelConfig = field(default_factory=ModelConfig)
74:     memory: MemoryConfig = field(default_factory=MemoryConfig)
75:     agent: AgentConfig = field(default_factory=AgentConfig)
76:     tools: ToolConfig = field(default_factory=ToolConfig)
77:     skills: SkillConfig = field(default_factory=SkillConfig)
78:     logging: LoggingConfig = field(default_factory=LoggingConfig)
79: 
80:     @classmethod
81:     def load(cls, config_path: str = "config.yaml", env_path: str = ".env") -> "Config":
82:         """Load configuration from YAML file with environment variable resolution."""
83:         # Resolve to absolute path
84:         base_dir = os.path.dirname(os.path.abspath(config_path))
85:         config_path = os.path.abspath(config_path)
86:         env_path = os.path.abspath(env_path) if os.path.isabs(env_path) else os.path.join(base_dir, env_path)
87: 
88:         # Load environment variables
89:         load_env(env_path)
90: 
91:         # Read YAML
92:         with open(config_path, "r") as f:
93:             raw = yaml.safe_load(f) or {}
94: 
95:         # Resolve ${VAR} placeholders
96:         resolved = resolve_dict(raw)
97: 
98:         return cls._from_dict(resolved)
99: 
100: @classmethod
101: def _from_dict(cls, data: Dict[str, Any]) -> "Config":
102: """Build Config from resolved dictionary."""
103: # Lark
104: lark_data = data.get("lark", {})
105: lark = LarkConfig(
106: app_id=lark_data.get("app_id", ""),
107: app_secret=lark_data.get("app_secret", ""),
108: )
109:
110: # Models
111: models_data = data.get("models", {})
112: providers = []
113: for p in models_data.get("providers", []):
114: providers.append(ProviderConfig(
115: name=p["name"],
116: api_key=p.get("api_key", ""),
117: base_url=p.get("base_url"),
118: models=p.get("models", {}),
119: ))
120: models = ModelConfig(
121: providers=providers,
122: default_provider=models_data.get("default_provider", "openai"),
123: )
124:
125: # Memory
126: mem_data = data.get("memory", {})
127: memory = MemoryConfig(
128: db_path=mem_data.get("db_path", "./data/memory.db"),
129: top_k=mem_data.get("top_k", 5),
130: decay_rate=mem_data.get("decay_rate", 0.02),
131: archive_threshold=mem_data.get("archive_threshold", 0.1),
132: cleanup_days=mem_data.get("cleanup_days", 90),
133: )
134:
135: # Agent
136: agent_data = data.get("agent", {})
137: agent = AgentConfig(
138: max_iterations=agent_data.get("max_iterations", 20),
139: timeout_minutes=agent_data.get("timeout_minutes", 30),
140: reflection_max_rounds=agent_data.get("reflection_max_rounds", 3),
141: tot_branches=agent_data.get("tot_branches", 3),
142: tot_depth=agent_data.get("tot_depth", 3),
143: )
144:
145: # Tools
146: tools_data = data.get("tools", {})
147: tools = ToolConfig(
148: shell_timeout=tools_data.get("shell_timeout", 30),
149: output_max_bytes=tools_data.get("output_max_bytes", 10240),
150: work_dir=tools_data.get("work_dir", "./workspace"),
151: search_backend=tools_data.get("search_backend", "tavily"),
152: search_api_key=tools_data.get("search_api_key", ""),
153: )
154:
155: # Skills
156: skills_data = data.get("skills", {})
157: skills = SkillConfig(dir=skills_data.get("dir", "./skills"))
158:
159: # Logging
160: log_data = data.get("logging", {})
161: logging_cfg = LoggingConfig(
162: level=log_data.get("level", "INFO"),
163: file=log_data.get("file", "./data/minibot.log"),
164: )
165:
166: return cls(
167: lark=lark,
168: models=models,
169: memory=memory,
170: agent=agent,
171: tools=tools,
172: skills=skills,
173: logging=logging_cfg,
174: )
175:
176: def validate(self) -> List[str]:
177: """Validate configuration, return list of issues."""
178: issues = []
179:
180: if not self.lark.app_id or not self.lark.app_secret:
181: issues.append("Lark app_id and app_secret are required (set LARK_APP_ID and LARK_APP_SECRET)")
182:
183: active_providers = [p for p in self.models.providers if p.api_key]
184: if not active_providers:
185: issues.append("At least one model provider with a valid API key is required")
186:
187: if self.models.default_provider not in [p.name for p in self.models.providers]:
188: issues.append(f"Default provider '{self.models.default_provider}' not found in providers list")
189:
190: return issues
