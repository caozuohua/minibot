 1: """ReAct reasoning engine — Plan, Act, Observe, Reflect loop."""
 2: 
 3: import json
 4: import logging
 5: import re
 6: from typing import List, Optional, Tuple
 7: 
 8: logger = logging.getLogger(__name__)
 9: 
10: 
11: class ReActEngine:
12:     """ReAct (Reason + Act) loop with tool execution."""
13: 
14:     SYSTEM_PROMPT = """\
15: You are an autonomous agent that solves tasks by reasoning and using tools.
16: 
17: {tools_info}
18: 
19: {skills_info}
20: 
21: {memories_info}
22: 
23: For each step, respond in this exact JSON format:
24: {{
25:   "thought": "Your reasoning about what to do next",
26:   "action": "tool_name",
27:   "action_input": {{"param1": "value1", "param2": "value2"}},
28:   "done": false
29: }}
30: 
31: When the task is complete, respond with:
32: {{
33:   "thought": "Summary of what was accomplished",
34:   "action": null,
35:   "action_input": null,
36:   "done": true,
37:   "result": "Final result summary"
38: }}
39: """
40: 
41:     # Keywords that suggest ToT mode
42:     TOT_KEYWORDS = [
43:         "math", "algorithm", "prove", "proof", "logic puzzle",
44:         "complex logic", "recursive", "dynamic programming",
45:         "calculate", "compute", "equation", "theorem",
46:     ]
47: 
48:     def __init__(self, max_iterations: int = 20):
49:         self.max_iterations = max_iterations
50: 
51:     def should_use_tot(self, task: str) -> bool:
52:         """Check if the task should use Tree of Thoughts."""
53:         task_lower = task.lower()
54:         return any(kw in task_lower for kw in self.TOT_KEYWORDS)
55: 
56:     def run(self, llm_chat_fn, task: str, tools_info: str,
57:             skills_info: str = "", memories_info: str = "",
58:             conversation_history: list = None) -> dict:
59:         """Execute the ReAct loop.
60:         
61:         Args:
62:             llm_chat_fn: Function that takes messages and returns LLM response.
63:             task: The task to accomplish.
64:             tools_info: Description of available tools.
65:             skills_info: Description of available skills.
66:             memories_info: Relevant memories.
67:             conversation_history: Previous conversation context.
68:         
69:         Returns:
70:             Dict with 'result', 'steps', 'iterations'.
71:         """
72:         system_prompt = self.SYSTEM_PROMPT.format(
73:             tools_info=tools_info,
74:             skills_info=skills_info or "No skills available.",
75:             memories_info=memories_info or "No relevant memories.",
76:         )
77: 
78:         messages = [
79:             {"role": "system", "content": system_prompt},
80:             {"role": "user", "content": f"Task: {task}"},
81:         ]
82: 
83:         if conversation_history:
84:             messages.extend(conversation_history[-6:])
85: 
86:         steps = []
87:         iteration = 0
88: 
89:         while iteration < self.max_iterations:
90:             iteration += 1
91:             logger.info(f"ReAct iteration {iteration}/{self.max_iterations}")
92: 
93:             # Get LLM response
94:             try:
95:                 response = llm_chat_fn(messages)
96:             except Exception as e:
97:                 logger.error(f"LLM call failed: {e}")
98:                 return {
99:                     "result": f"Error: LLM call failed ({e})",
100: "steps": steps,
101: "iterations": iteration,
102: "error": str(e),
103: }
104:
105: # Parse response
106: action_data = self._parse_response(response)
107: if not action_data:
108: # Try to use raw response as result
109: logger.warning("Failed to parse LLM response, using as result")
110: return {
111: "result": response,
112: "steps": steps,
113: "iterations": iteration,
114: }
115:
116: thought = action_data.get("thought", "")
117: done = action_data.get("done", False)
118: action = action_data.get("action")
119:
120: if done:
121: result = action_data.get("result", response)
122: logger.info(f"Task completed in {iteration} iterations")
123: return {
124: "result": result,
125: "steps": steps,
126: "iterations": iteration,
127: }
128:
129: # Execute tool
130: if action:
131: action_input = action_data.get("action_input", {})
132: tool_result = self._execute_tool(
133: action, action_input, llm_chat_fn
134: )
135:
136: step_record = {
137: "iteration": iteration,
138: "thought": thought,
139: "action": action,
140: "action_input": action_input,
141: "result": tool_result,
142: }
143: steps.append(step_record)
144:
145: # Add observation to conversation
146: messages.append({
147: "role": "assistant",
148: "content": response,
149: })
150: messages.append({
151: "role": "user",
152: "content": f"Observation: {tool_result}",
153: })
154: else:
155: # No action specified, ask for clarification
156: messages.append({
157: "role": "assistant",
158: "content": response,
159: })
160: messages.append({
161: "role": "user",
162: "content": "Please specify an action to take.",
163: })
164:
165: # Max iterations reached
166: logger.warning(f"Max iterations ({self.max_iterations}) reached")
167: return {
168: "result": f"Task incomplete after {self.max_iterations} iterations. Last thought: {thought}",
169: "steps": steps,
170: "iterations": iteration,
171: "incomplete": True,
172: }
173:
174: def _parse_response(self, response: str) -> Optional[dict]:
175: """Parse JSON response from LLM."""
176: response = response.strip()
177:
178: # Extract JSON from code block if present
179: if "" in response: 180: lines = response.split("\n") 181: json_str = "" 182: in_block = False 183: for line in lines: 184: if "" in line:
185: in_block = not in_block
186: continue
187: if in_block:
188: json_str += line + "\n"
189: response = json_str.strip()
190:
191: # Try to find JSON object in response
192: match = re.search(r"{.*}", response, re.DOTALL)
193: if match:
194: try:
195: return json.loads(match.group())
196: except json.JSONDecodeError:
197: pass
198:
199: return None
200:
201: def _execute_tool(self, tool_name: str, action_input: dict,
202: llm_chat_fn) -> str:
203: """Execute a tool call.
204:
205: Note: This is a placeholder. In the full implementation,
206: this would call the ToolRegistry.
207: """
208: # For now, return a placeholder
209: return f"[Tool '{tool_name}' would execute with {action_input}]"
