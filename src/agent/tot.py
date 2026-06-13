"""Tree of Thoughts (ToT) reasoning engine."""

import json
import logging

logger = logging.getLogger(__name__)


class ToTEngine:
    """Tree of Thoughts — branching exploration with self-evaluation."""

    EXPLORE_PROMPT = """\
You are solving: {task}

Current state: {state}

Generate {branches} different approaches/thinking directions for the next step.
Each direction should be a distinct way to proceed.

Respond as a JSON array of exactly {branches} strings:
["approach 1", "approach 2", "approach 3"]
"""

    EVALUATE_PROMPT = """\
You are solving: {task}

Evaluate these approaches and rate each as GOOD, MEDIUM, or BAD:

{approaches}

Respond as a JSON array of ratings:
["GOOD", "MEDIUM", "BAD"]
"""

    def __init__(self, branches: int = 3, depth: int = 3):
        self.branches = branches
        self.depth = depth

    def run(
        self,
        llm_chat_fn,
        task: str,
        tools_info: str,
        conversation_history: list,
    ) -> str:
        """Execute Tree of Thoughts reasoning.

        Args:
            llm_chat_fn: Function that takes messages and returns LLM response.
            task: The task to solve.
            tools_info: Description of available tools.
            conversation_history: Previous conversation context.

        Returns:
            The best solution found through tree exploration.
        """
        logger.info(f"ToT starting: {self.branches} branches, {self.depth} depth")

        current_state = task
        best_path = []

        for level in range(self.depth):
            logger.info(f"ToT level {level + 1}/{self.depth}")

            # Generate branches
            branches = self._generate_branches(llm_chat_fn, task, current_state, level)
            if not branches:
                break

            # Evaluate branches
            ratings = self._evaluate_branches(llm_chat_fn, task, branches)

            # Select best branch
            best_idx = self._select_best(ratings)
            best_branch = branches[best_idx]

            best_path.append(best_branch)
            current_state = best_branch

            logger.info(
                f"ToT level {level + 1}: selected branch {best_idx} "
                f"(rating: {ratings[best_idx]})"
            )

        return self._format_result(task, best_path)

    def _generate_branches(
        self, llm_chat_fn, task: str, state: str, level: int
    ) -> list[str]:
        """Generate branching approaches."""
        prompt = self.EXPLORE_PROMPT.format(
            task=task,
            state=state,
            branches=self.branches,
        )

        messages = [
            {
                "role": "system",
                "content": "You are a creative problem solver. Generate diverse approaches.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = llm_chat_fn(messages)
            # Parse JSON array
            response = response.strip()
            if response.startswith("```"):
                # Extract from code block
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

            branches = json.loads(response)
            if isinstance(branches, list):
                return branches[: self.branches]
            return []
        except Exception as e:
            logger.warning(f"ToT branch generation failed: {e}")
            return [f"Continue with current approach: {state}"]

    def _evaluate_branches(
        self, llm_chat_fn, task: str, branches: list[str]
    ) -> list[str]:
        """Evaluate and rate branches."""
        approaches_text = "\n".join(f"{i + 1}. {b}" for i, b in enumerate(branches))

        prompt = self.EVALUATE_PROMPT.format(
            task=task,
            approaches=approaches_text,
        )

        messages = [
            {
                "role": "system",
                "content": "You are an evaluator. Rate each approach.",
            },
            {"role": "user", "content": prompt},
        ]

        try:
            response = llm_chat_fn(messages)
            response = response.strip()
            if response.startswith("```"):
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

            ratings = json.loads(response)
            if isinstance(ratings, list):
                # Normalize ratings
                valid = ["GOOD", "MEDIUM", "BAD"]
                return [
                    r.upper() if r.upper() in valid else "MEDIUM"
                    for r in ratings[: len(branches)]
                ]
        except Exception as e:
            logger.warning(f"ToT evaluation failed: {e}")

        # Default: all MEDIUM
        return ["MEDIUM"] * len(branches)

    def _select_best(self, ratings: list[str]) -> int:
        """Select the best branch index based on ratings."""
        priority = {"GOOD": 3, "MEDIUM": 2, "BAD": 1}
        scores = [priority.get(r, 0) for r in ratings]
        max_score = max(scores)
        return scores.index(max_score)

    def _format_result(self, task: str, path: list[str]) -> str:
        """Format the ToT exploration result."""
        lines = [f"Task: {task}", ""]
        for i, step in enumerate(path):
            lines.append(f"Step {i + 1}: {step}")
        return "\n".join(lines)
