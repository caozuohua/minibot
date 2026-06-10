 1: """Reflection module — self-criticism and correction."""
 2: 
 3: import logging
 4: from typing import Optional, Tuple
 5: 
 6: logger = logging.getLogger(__name__)
 7: 
 8: 
 9: class ReflectionEngine:
10:     """Self-criticism engine that evaluates tool execution results."""
11: 
12:     REFLECTION_PROMPT = """\
13: You are a critical reviewer. Evaluate the following tool execution result.
14: 
15: Task: {task}
16: Tool used: {tool_name}
17: Tool result: {tool_output}
18: 
19: Please evaluate:
20: 1. Is the result correct and complete?
21: 2. Are there any errors, omissions, or issues?
22: 3. Does the result move us closer to completing the task?
23: 
24: Respond in this exact format:
25: VERDICT: CORRECT | NEEDS_CORRECTION
26: REASON: <brief explanation>
27: CORRECTION: <what to do differently, only if NEEDS_CORRECTION>
28: """
29: 
30:     def __init__(self, max_rounds: int = 3):
31:         self.max_rounds = max_rounds
32: 
33:     def reflect(self, llm_chat_fn, task: str, tool_name: str,
34:                 tool_output: str, conversation_history: list) -> Tuple[bool, str]:
35:         """Evaluate a tool execution result.
36:         
37:         Args:
38:             llm_chat_fn: Function that takes messages and returns LLM response.
39:             task: The overall task description.
40:             tool_name: Name of the tool that was executed.
41:             tool_output: Output from the tool execution.
42:             conversation_history: Previous conversation context.
43:         
44:         Returns:
45:             (should_correct, correction_text)
46:             - should_correct: True if the result needs correction
47:             - correction_text: What to do differently
48:         """
49:         prompt = self.REFLECTION_PROMPT.format(
50:             task=task,
51:             tool_name=tool_name,
52:             tool_output=tool_output[:2000],  # Truncate for context
53:         )
54: 
55:         messages = [
56:             {"role": "system", "content": "You are a critical reviewer. Be strict but fair."},
57:         ]
58:         messages.extend(conversation_history[-4:])  # Last 4 messages for context
59:         messages.append({"role": "user", "content": prompt})
60: 
61:         try:
62:             response = llm_chat_fn(messages)
63:             return self._parse_response(response)
64:         except Exception as e:
65:             logger.warning(f"Reflection failed: {e}")
66:             return False, ""
67: 
68:     def _parse_response(self, response: str) -> Tuple[bool, str]:
69:         """Parse the reflection response."""
70:         should_correct = False
71:         correction = ""
72: 
73:         for line in response.split("\n"):
74:             line = line.strip()
75:             if line.startswith("VERDICT:"):
76:                 verdict = line.replace("VERDICT:", "").strip().upper()
77:                 should_correct = verdict == "NEEDS_CORRECTION"
78:             elif line.startswith("CORRECTION:"):
79:                 correction = line.replace("CORRECTION:", "").strip()
80: 
81:         return should_correct, correction
