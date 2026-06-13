"""Reflection module — self-criticism and correction."""

import logging

logger = logging.getLogger(__name__)


class ReflectionEngine:
    """Self-criticism engine that evaluates tool execution results."""

    REFLECTION_PROMPT = """\
You are a critical reviewer. Evaluate the following tool execution result.

Task: {task}
Tool used: {tool_name}
Tool result: {tool_output}

Please evaluate:
1. Is the result correct and complete?
2. Are there any errors, omissions, or issues?
3. Does the result move us closer to completing the task?

Respond in this exact format:
VERDICT: CORRECT | NEEDS_CORRECTION
REASON: <brief explanation>
CORRECTION: <what to do differently, only if NEEDS_CORRECTION>
"""

    def __init__(self, max_rounds: int = 3):
        self.max_rounds = max_rounds

    def reflect(
        self,
        llm_chat_fn,
        task: str,
        tool_name: str,
        tool_output: str,
        conversation_history: list,
    ) -> tuple[bool, str]:
        """Evaluate a tool execution result.

        Args:
            llm_chat_fn: Function that takes messages and returns LLM response.
            task: The overall task description.
            tool_name: Name of the tool that was executed.
            tool_output: Output from the tool execution.
            conversation_history: Previous conversation context.

        Returns:
            (should_correct, correction_text)
            - should_correct: True if the result needs correction
            - correction_text: What to do differently
        """
        prompt = self.REFLECTION_PROMPT.format(
            task=task,
            tool_name=tool_name,
            tool_output=tool_output[:2000],  # Truncate for context
        )

        messages = [
            {
                "role": "system",
                "content": "You are a critical reviewer. Be strict but fair.",
            },
        ]
        messages.extend(conversation_history[-4:])  # Last 4 messages for context
        messages.append({"role": "user", "content": prompt})

        try:
            response = llm_chat_fn(messages)
            return self._parse_response(response)
        except Exception as e:
            logger.warning(f"Reflection failed: {e}")
            return False, ""

    def _parse_response(self, response: str) -> tuple[bool, str]:
        """Parse the reflection response."""
        should_correct = False
        correction = ""

        for line in response.split("\n"):
            line = line.strip()
            if line.startswith("VERDICT:"):
                verdict = line.replace("VERDICT:", "").strip().upper()
                should_correct = verdict == "NEEDS_CORRECTION"
            elif line.startswith("CORRECTION:"):
                correction = line.replace("CORRECTION:", "").strip()

        return should_correct, correction
