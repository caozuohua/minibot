 1: #!/usr/bin/env python3
 2: """MiniBot — Lightweight autonomous agent for small VPS.
 3: 
 4: Usage:
 5:     python main.py              # Start with default config.yaml
 6:     python main.py --config /path/to/config.yaml
 7:     python main.py --validate   # Validate config and exit
 8: """
 9: 
10: import asyncio
11: import logging
12: import os
13: import signal
14: import sys
15: import argparse
16: 
17: from src.config import Config
18: from src.models.router import ModelRouter
19: from src.memory.manager import MemoryManager
20: from src.tools.registry import ToolRegistry
21: from src.skills.registry import SkillRegistry
22: from src.agent.core import AgentCore
23: from src.gateway.lark_gateway import LarkGateway
24: 
25: 
26: def setup_logging(config: Config) -> None:
27:     """Configure logging based on config."""
28:     log_file = config.logging.file
29:     log_dir = os.path.dirname(os.path.abspath(log_file))
30:     os.makedirs(log_dir, exist_ok=True)
31: 
32:     logging.basicConfig(
33:         level=getattr(logging, config.logging.level.upper(), logging.INFO),
34:         format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
35:         handlers=[
36:             logging.StreamHandler(sys.stdout),
37:             logging.FileHandler(log_file, encoding="utf-8"),
38:         ],
39:     )
40: 
41: 
42: def build_app(config: Config):
43:     """Build all application components."""
44:     logger = logging.getLogger("minibot")
45: 
46:     # 1. Model Router
47:     logger.info("Initializing Model Router...")
48:     model_router = ModelRouter(config)
49:     logger.info(f"Available providers: {model_router.available_providers}")
50: 
51:     # 2. Memory Manager (with embedding function from model router)
52:     logger.info("Initializing Memory Manager...")
53:     embed_fn = None
54:     if model_router.available_providers:
55:         embed_fn = lambda text: model_router.embed(text)
56:     memory_manager = MemoryManager(config, embed_fn=embed_fn)
57: 
58:     # 3. Tool Registry
59:     logger.info("Initializing Tool Registry...")
60:     tool_registry = ToolRegistry(config)
61:     logger.info(f"Available tools: {tool_registry.get_tool_names()}")
62: 
63:     # 4. Skill Registry
64:     logger.info("Initializing Skill Registry...")
65:     skill_registry = SkillRegistry(config)
66:     logger.info(f"Loaded skills: {[s.name for s in skill_registry.list_skills()]}")
67: 
68:     # 5. Agent Core
69:     logger.info("Initializing Agent Core...")
70:     agent = AgentCore(
71:         config=config,
72:         model_router=model_router,
73:         tool_registry=tool_registry,
74:         memory_manager=memory_manager,
75:         skill_registry=skill_registry,
76:     )
77: 
78:     # 6. Lark Gateway
79:     logger.info("Initializing Lark Gateway...")
80:     gateway = LarkGateway(config)
81: 
82:     # Wire up message handler
83:     async def handle_message(user_id: str, text: str):
84:         """Handle incoming message from Lark."""
85:         logger.info(f"Processing message from {user_id}: {text[:100]}")
86: 
87:         try:
88:             # Send task start notification
89:             await gateway.send_task_start(user_id, text)
90: 
91:             # Run agent
92:             result = agent.run(task=text, user_id=user_id)
93: 
94:             # Send result
95:             if result.get("error") or result.get("incomplete"):
96:                 await gateway.send_task_error(
97:                     user_id,
98:                     error=result.get("error", "Task incomplete"),
99:                     partial_result=result.get("result", ""),
100: )
101: else:
102: await gateway.send_task_result(
103: user_id,
104: summary=result.get("result", "Task completed"),
105: mode=result.get("mode", "react"),
106: iterations=result.get("iterations", 0),
107: elapsed=result.get("elapsed_seconds", 0),
108: )
109:
110: except Exception as e:
111: logger.error(f"Error processing message: {e}", exc_info=True)
112: await gateway.send_task_error(user_id, str(e))
113:
114: gateway.on_message(handle_message)
115:
116: return gateway, agent, memory_manager
117:
118:
119: def main():
120: parser = argparse.ArgumentParser(description="MiniBot Agent")
121: parser.add_argument("--config", default="config.yaml", help="Path to config file")
122: parser.add_argument("--validate", action="store_true", help="Validate config and exit")
123: args = parser.parse_args()
124:
125: # Load configuration
126: try:
127: config = Config.load(args.config)
128: except FileNotFoundError:
129: print(f"Error: Config file not found: {args.config}")
130: sys.exit(1)
131: except Exception as e:
132: print(f"Error loading config: {e}")
133: sys.exit(1)
134:
135: # Validate
136: issues = config.validate()
137: if issues:
138: print("Configuration issues found:")
139: for issue in issues:
140: print(f" - {issue}")
141: if args.validate:
142: sys.exit(1)
143:
144: if args.validate:
145: print("Configuration is valid.")
146: print(f" Providers: {[p.name for p in config.models.providers]}")
147: print(f" Default: {config.models.default_provider}")
148: print(f" Memory: {config.memory.db_path}")
149: print(f" Skills dir: {config.skills.dir}")
150: print(f" Work dir: {config.tools.work_dir}")
151: sys.exit(0)
152:
153: # Setup logging
154: setup_logging(config)
155: logger = logging.getLogger("minibot")
156:
157: logger.info("=" * 60)
158: logger.info("MiniBot starting up...")
159: logger.info("=" * 60)
160:
161: # Build application
162: gateway, agent, memory_manager = build_app(config)
163:
164: logger.info("MiniBot ready.")
165: logger.info("Press Ctrl+C to stop.")
166:
167: # Graceful shutdown
168: shutdown_event = asyncio.Event()
169:
170: def signal_handler():
171: logger.info("Shutdown signal received...")
172: shutdown_event.set()
173:
174: # Run async gateway
175: async def run():
176: await gateway.start()
177:
178: try:
179: asyncio.run(run())
180: except KeyboardInterrupt:
181: logger.info("Shutting down...")
182: finally:
183: gateway.stop()
184: memory_manager.close()
185: logger.info("MiniBot stopped.")
186:
187:
188: if name == "main":
189: main()
