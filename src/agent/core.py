 1: """Agent Core — main execution loop integrating all reasoning engines."""
 2: 
 3: import json
 4: import logging
 5: import time
 6: from typing import Dict, List, Optional, Callable
 7: 
 8: from src.config import Config
 9: from src.agent.react import ReActEngine
10: from src.agent.reflection import ReflectionEngine
11: from src.agent.tot import ToTEngine
12: 
13: logger = logging.getLogger(__name__)
14: 
15: 
16: class AgentCore:
17:     """Main agent execution engine.
18:     
19:     Integrates ReAct, Reflection, and Tree of Thoughts reasoning.
20:     """
21: 
22:     def __init__(self, config: Config, model_router=None,
23:                  tool_registry=None, memory_manager=None,
24:                  skill_registry=None):
25:         self.config = config.agent
26:         self.model_router = model_router
27:         self.tool_registry = tool_registry
28:         self.memory_manager = memory_manager
29:         self.skill_registry = skill_registry
30: 
31:         # Initialize reasoning engines
32:         self.react = ReActEngine(max_iterations=config.agent.max_iterations)
33:         self.reflection = ReflectionEngine(
34:             max_rounds=config.agent.reflection_max_rounds
35:         )
36:         self.tot = ToTEngine(
37:             branches=config.agent.tot_branches,
38:             depth=config.agent.tot_depth,
39:         )
40: 
41:     def _chat_fn(self, messages: list) -> str:
42:         """Wrapper for model router chat."""
43:         if self.model_router:
44:             return self.model_router.chat(messages)
45:         raise RuntimeError("No model router configured")
46: 
47:     def run(self, task: str, user_id: str = "") -> dict:
48:         """Execute a task autonomously.
49:         
50:         Args:
51:             task: The task description.
52:             user_id: Optional user identifier for memory scoping.
53:         
54:         Returns:
55:             Dict with 'result', 'steps', 'mode', 'iterations'.
56:         """
57:         start_time = time.time()
58:         logger.info(f"Agent starting task: {task[:100]}")
59: 
60:         # Step 1: Retrieve relevant memories
61:         memories_info = ""
62:         if self.memory_manager:
63:             try:
64:                 results = self.memory_manager.search(task, top_k=5)
65:                 if results:
66:                     mem_lines = [f"- {content[:200]}" for content, _ in results]
67:                     memories_info = "Relevant memories:\n" + "\n".join(mem_lines)
68:             except Exception as e:
69:                 logger.warning(f"Memory search failed: {e}")
70: 
71:         # Step 2: Match skills
72:         skills_info = ""
73:         matched_skills = []
74:         if self.skill_registry:
75:             matched_skills = self.skill_registry.match_triggers(task)
76:             if matched_skills:
77:                 skills_info = self.skill_registry.format_for_prompt()
78: 
79:         # Step 3: Get tools info
80:         tools_info = ""
81:         if self.tool_registry:
82:             tools_info = self.tool_registry.format_for_prompt()
83: 
84:         # Step 4: Choose reasoning mode
85:         mode = self._choose_mode(task)
86:         logger.info(f"Selected reasoning mode: {mode}")
87: 
88:         # Step 5: Execute
89:         if mode == "tot":
90:             result = self._run_tot(task, tools_info, skills_info, memories_info)
91:         else:
92:             result = self._run_react(task, tools_info, skills_info, memories_info)
93: 
94:         # Step 6: Save task memory
95:         if self.memory_manager:
96:             try:
97:                 summary = f"Task: {task}\nResult: {result.get('result', '')[:500]}"
98:                 self.memory_manager.add_episodic(
99:                     content=summary,
100: category="task",
101: importance=0.7,
102: )
103: except Exception as e:
104: logger.warning(f"Memory save failed: {e}")
105:
106: # Step 7: Increment skill usage
107: for skill in matched_skills:
108: if self.skill_registry:
109: self.skill_registry.increment_usage(skill.name)
110:
111: elapsed = time.time() - start_time
112: result["elapsed_seconds"] = round(elapsed, 1)
113: result["mode"] = mode
114:
115: logger.info(f"Agent completed task in {elapsed:.1f}s ({result.get('iterations', 0)} iterations)")
116: return result
117:
118: def _choose_mode(self, task: str) -> str:
119: """Choose reasoning mode based on task characteristics."""
120: if self.react.should_use_tot(task):
121: return "tot"
122: return "react"
123:
124: def _run_react(self, task: str, tools_info: str,
125: skills_info: str, memories_info: str) -> dict:
126: """Run ReAct with Reflection."""
127: # Patch the tool execution into ReAct engine
128: original_execute = self.react._execute_tool
129:
130: def tool_executor(tool_name: str, action_input: dict, chat_fn) -> str:
131: if self.tool_registry:
132: try:
133: result = self.tool_registry.call(tool_name, **action_input)
134: output = result.output or ""
135: if result.error:
136: output += f"\nError: {result.error}"
137: return output
138: except Exception as e:
139: return f"Tool execution error: {e}"
140: return original_execute(tool_name, action_input, chat_fn)
141:
142: self.react._execute_tool = tool_executor
143:
144: result = self.react.run(
145: llm_chat_fn=self._chat_fn,
146: task=task,
147: tools_info=tools_info,
148: skills_info=skills_info,
149: memories_info=memories_info,
150: )
151:
152: return result
153:
154: def _run_tot(self, task: str, tools_info: str,
155: skills_info: str, memories_info: str) -> dict:
156: """Run Tree of Thoughts."""
157: system_prompt = (
158: f"{tools_info}\n\n{skills_info}\n\n{memories_info}"
159: )
160:
161: result_text = self.tot.run(
162: llm_chat_fn=self._chat_fn,
163: task=task,
164: tools_info=system_prompt,
165: conversation_history=[],
166: )
167:
168: return {
169: "result": result_text,
170: "steps": [],
171: "iterations": self.tot.depth,
172: }
173:
174: def format_result_card(self, result: dict) -> dict:
175: """Format agent result as a Lark card data structure."""
176: card_data = {
177: "title": "Task Result",
178: "status": "completed",
179: "mode": result.get("mode", "react"),
180: "iterations": result.get("iterations", 0),
181: "elapsed": result.get("elapsed_seconds", 0),
182: "result": result.get("result", ""),
183: }
184:
185: if result.get("incomplete"):
186: card_data["status"] = "incomplete"
187:
188: if result.get("error"):
189: card_data["status"] = "error"
190: card_data["error"] = result["error"]
191:
192: return card_data
