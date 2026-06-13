"""ReAct reasoning engine — Plan, Act, Observe, Reflect loop."""

import json
import logging
import re
from typing import ClassVar

logger = logging.getLogger(__name__)


class ReActEngine:
    """ReAct (Reason + Act) loop with tool execution."""

    SYSTEM_PROMPT = """\
You are an autonomous agent that solves tasks by reasoning and using tools.

{tools_info}

{skills_info}

{memories_info}

For each step, respond in this exact JSON format:
{{
  "thought": "Your reasoning about what to do next",
  "action": "tool_name",
  "action_input": {{"param1": "value1", "param2": "value2"}},
  "done": false
}}

When the task is complete, respond with:
{{
  "thought": "Summary of what was accomplished",
  "action": null,
  "action_input": null,
  "done": true,
  "result": "Final result summary"
}}
"""

    # Keywords that suggest ToT mode
    TOT_KEYWORDS: ClassVar[list[str]] = [
        "math",
        "algorithm",
        "prove",
        "proof",
        "logic puzzle",
        "complex logic",
        "recursive",
        "dynamic programming",
        "calculate",
        "compute",
        "equation",
        "theorem",
    ]

    def __init__(self, max_iterations: int = 20):
        self.max_iterations = max_iterations

    def should_use_tot(self, task: str) -> bool:
        """Check if the task should use Tree of Thoughts."""
        task_lower = task.lower()
        return any(kw in task_lower for kw in self.TOT_KEYWORDS)

    def run(
        self,
        llm_chat_fn,
        task: str,
        tools_info: str,
        skills_info: str = "",
        memories_info: str = "",
        conversation_history: list | None = None,
    ) -> dict:
        """Execute the ReAct loop.

        Args:
            llm_chat_fn: Function that takes messages and returns LLM response.
            task: The task to accomplish.
            tools_info: Description of available tools.
            skills_info: Description of available skills.
            memories_info: Relevant memories.
            conversation_history: Previous conversation context.

        Returns:
            Dict with 'result', 'steps', 'iterations'.
        """
        system_prompt = self.SYSTEM_PROMPT.format(
            tools_info=tools_info,
            skills_info=skills_info or "No skills available.",
            memories_info=memories_info or "No relevant memories.",
        )

        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Task: {task}"},
        ]

        if conversation_history:
            messages.extend(conversation_history[-6:])

        steps = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1
            logger.info(f"ReAct iteration {iteration}/{self.max_iterations}")

            # Get LLM response
            try:
                response = llm_chat_fn(messages)
            except Exception as e:
                logger.error(f"LLM call failed: {e}")
                return {
                    "result": f"Error: LLM call failed ({e})",
                    "steps": steps,
                    "iterations": iteration,
                    "error": str(e),
                }

            # Parse response
            action_data = self._parse_response(response)
            if not action_data:
                # Try to use raw response as result
                logger.warning("Failed to parse LLM response, using as result")
                return {
                    "result": response,
                    "steps": steps,
                    "iterations": iteration,
                }

            thought = action_data.get("thought", "")
            done = action_data.get("done", False)
            action = action_data.get("action")

            if done:
                result = action_data.get("result", response)
                logger.info(f"Task completed in {iteration} iterations")
                return {
                    "result": result,
                    "steps": steps,
                    "iterations": iteration,
                }

            # Execute tool
            if action:
                action_input = action_data.get("action_input", {})
                tool_result = self._execute_tool(action, action_input, llm_chat_fn)

                step_record = {
                    "iteration": iteration,
                    "thought": thought,
                    "action": action,
                    "action_input": action_input,
                    "result": tool_result,
                }
                steps.append(step_record)

                # Add observation to conversation
                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {"role": "user", "content": f"Observation: {tool_result}"}
                )
            else:
                # No action specified, ask for clarification
                messages.append({"role": "assistant", "content": response})
                messages.append(
                    {"role": "user", "content": "Please specify an action to take."}
                )

        # Max iterations reached
        logger.warning(f"Max iterations ({self.max_iterations}) reached")
        return {
            "result": (
                f"Task incomplete after {self.max_iterations} iterations. "
                f"Last thought: {thought}"
            ),
            "steps": steps,
            "iterations": iteration,
            "incomplete": True,
        }

    def _parse_response(self, response: str) -> dict | None:
        """Parse JSON response from LLM."""
        response = response.strip()

        # Extract JSON from code block if present
        if "```" in response:
            lines = response.split("\n")
            json_str = ""
            in_block = False
            for line in lines:
                if "```" in line:
                    in_block = not in_block
                    continue
                if in_block:
                    json_str += line + "\n"
            response = json_str.strip()

        # Try to find JSON object in response
        match = re.search(r"\{.*\}", response, re.DOTALL)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass

        return None

    def _execute_tool(self, tool_name: str, action_input: dict, llm_chat_fn) -> str:
        """Execute a tool call.

        Note: This is a placeholder. In the full implementation,
        this would call the ToolRegistry.
        """
        # For now, return a placeholder
        return f"[Tool '{tool_name}' would execute with {action_input}]"
