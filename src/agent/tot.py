1: """Tree of Thoughts (ToT) reasoning engine."""
 2: 
 3: import json
 4: import logging
 5: from typing import List, Optional, Tuple
 6: 
 7: logger = logging.getLogger(__name__)
 8: 
 9: 
10: class ToTEngine:
11:     """Tree of Thoughts — branching exploration with self-evaluation."""
12: 
13:     EXPLORE_PROMPT = """\
14: You are solving: {task}
15: 
16: Current state: {state}
17: 
18: Generate {branches} different approaches/thinking directions for the next step.
19: Each direction should be a distinct way to proceed.
20: 
21: Respond as a JSON array of exactly {branches} strings:
22: ["approach 1", "approach 2", "approach 3"]
23: """
24: 
25:     EVALUATE_PROMPT = """\
26: You are solving: {task}
27: 
28: Evaluate these approaches and rate each as GOOD, MEDIUM, or BAD:
29: 
30: {approaches}
31: 
32: Respond as a JSON array of ratings:
33: ["GOOD", "MEDIUM", "BAD"]
34: """
35: 
36:     def __init__(self, branches: int = 3, depth: int = 3):
37:         self.branches = branches
38:         self.depth = depth
39: 
40:     def run(self, llm_chat_fn, task: str, tools_info: str,
41:             conversation_history: list) -> str:
42:         """Execute Tree of Thoughts reasoning.
43:         
44:         Args:
45:             llm_chat_fn: Function that takes messages and returns LLM response.
46:             task: The task to solve.
47:             tools_info: Description of available tools.
48:             conversation_history: Previous conversation context.
49:         
50:         Returns:
51:             The best solution found through tree exploration.
52:         """
53:         logger.info(f"ToT starting: {self.branches} branches, {self.depth} depth")
54: 
55:         current_state = task
56:         best_path = []
57: 
58:         for level in range(self.depth):
59:             logger.info(f"ToT level {level + 1}/{self.depth}")
60: 
61:             # Generate branches
62:             branches = self._generate_branches(
63:                 llm_chat_fn, task, current_state, level
64:             )
65:             if not branches:
66:                 break
67: 
68:             # Evaluate branches
69:             ratings = self._evaluate_branches(
70:                 llm_chat_fn, task, branches
71:             )
72: 
73:             # Select best branch
74:             best_idx = self._select_best(ratings)
75:             best_branch = branches[best_idx]
76: 
77:             best_path.append(best_branch)
78:             current_state = best_branch
79: 
80:             logger.info(f"ToT level {level + 1}: selected branch {best_idx} "
81:                        f"(rating: {ratings[best_idx]})")
82: 
83:         return self._format_result(task, best_path)
84: 
85:     def _generate_branches(self, llm_chat_fn, task: str,
86:                            state: str, level: int) -> List[str]:
87:         """Generate branching approaches."""
88:         prompt = self.EXPLORE_PROMPT.format(
89:             task=task,
90:             state=state,
91:             branches=self.branches,
92:         )
93: 
94:         messages = [
95:             {"role": "system", "content": "You are a creative problem solver. Generate diverse approaches."},
96:             {"role": "user", "content": prompt},
97:         ]
98: 
99:         try:
100: response = llm_chat_fn(messages)
101: # Parse JSON array
102: response = response.strip()
103: if response.startswith(""): 104: # Extract from code block 105: lines = response.split("\n") 106: json_str = "" 107: in_block = False 108: for line in lines: 109: if "" in line:
110: in_block = not in_block
111: continue
112: if in_block:
113: json_str += line + "\n"
114: response = json_str.strip()
115:
116: branches = json.loads(response)
117: if isinstance(branches, list):
118: return branches[:self.branches]
119: return []
120: except Exception as e:
121: logger.warning(f"ToT branch generation failed: {e}")
122: return [f"Continue with current approach: {state}"]
123:
124: def _evaluate_branches(self, llm_chat_fn, task: str,
125: branches: List[str]) -> List[str]:
126: """Evaluate and rate branches."""
127: approaches_text = "\n".join(
128: f"{i + 1}. {b}" for i, b in enumerate(branches)
129: )
130:
131: prompt = self.EVALUATE_PROMPT.format(
132: task=task,
133: approaches=approaches_text,
134: )
135:
136: messages = [
137: {"role": "system", "content": "You are an evaluator. Rate each approach."},
138: {"role": "user", "content": prompt},
139: ]
140:
141: try:
142: response = llm_chat_fn(messages)
143: response = response.strip()
144: if response.startswith(""): 145: lines = response.split("\n") 146: json_str = "" 147: in_block = False 148: for line in lines: 149: if "" in line:
150: in_block = not in_block
151: continue
152: if in_block:
153: json_str += line + "\n"
154: response = json_str.strip()
155:
156: ratings = json.loads(response)
157: if isinstance(ratings, list):
158: # Normalize ratings
159: valid = ["GOOD", "MEDIUM", "BAD"]
160: return [r.upper() if r.upper() in valid else "MEDIUM"
161: for r in ratings[:len(branches)]]
162: except Exception as e:
163: logger.warning(f"ToT evaluation failed: {e}")
164:
165: # Default: all MEDIUM
166: return ["MEDIUM"] * len(branches)
167:
168: def _select_best(self, ratings: List[str]) -> int:
169: """Select the best branch index based on ratings."""
170: priority = {"GOOD": 3, "MEDIUM": 2, "BAD": 1}
171: scores = [priority.get(r, 0) for r in ratings]
172: max_score = max(scores)
173: return scores.index(max_score)
174:
175: def _format_result(self, task: str, path: List[str]) -> str:
176: """Format the ToT exploration result."""
177: lines = [f"Task: {task}", ""]
178: for i, step in enumerate(path):
179: lines.append(f"Step {i + 1}: {step}")
180: return "\n".join(lines)
