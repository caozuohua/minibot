"""Agent Core — main execution loop integrating all reasoning engines."""

import logging
import time

from src.agent.react import ReActEngine
from src.agent.reflection import ReflectionEngine
from src.agent.tot import ToTEngine
from src.config import Config

logger = logging.getLogger(__name__)


class AgentCore:
    """Main agent execution engine.

    Integrates ReAct, Reflection, and Tree of Thoughts reasoning.
    """

    def __init__(
        self,
        config: Config,
        model_router=None,
        tool_registry=None,
        memory_manager=None,
        skill_registry=None,
    ):
        self.config = config.agent
        self.model_router = model_router
        self.tool_registry = tool_registry
        self.memory_manager = memory_manager
        self.skill_registry = skill_registry

        # Initialize reasoning engines
        self.react = ReActEngine(max_iterations=config.agent.max_iterations)
        self.reflection = ReflectionEngine(
            max_rounds=config.agent.reflection_max_rounds
        )
        self.tot = ToTEngine(
            branches=config.agent.tot_branches,
            depth=config.agent.tot_depth,
        )

    def _chat_fn(self, messages: list) -> str:
        """Wrapper for model router chat."""
        if self.model_router:
            return self.model_router.chat(messages)
        raise RuntimeError("No model router configured")

    def run(self, task: str, user_id: str = "") -> dict:
        """Execute a task autonomously.

        Args:
            task: The task description.
            user_id: Optional user identifier for memory scoping.

        Returns:
            Dict with 'result', 'steps', 'mode', 'iterations'.
        """
        start_time = time.time()
        logger.info(f"Agent starting task: {task[:100]}")

        # Step 1: Retrieve relevant memories
        memories_info = ""
        if self.memory_manager:
            try:
                results = self.memory_manager.search(task, top_k=5)
                if results:
                    mem_lines = [f"- {content[:200]}" for content, _ in results]
                    memories_info = "Relevant memories:\n" + "\n".join(mem_lines)
            except Exception as e:
                logger.warning(f"Memory search failed: {e}")

        # Step 2: Match skills
        skills_info = ""
        matched_skills = []
        if self.skill_registry:
            matched_skills = self.skill_registry.match_triggers(task)
            if matched_skills:
                skills_info = self.skill_registry.format_for_prompt()

        # Step 3: Get tools info
        tools_info = ""
        if self.tool_registry:
            tools_info = self.tool_registry.format_for_prompt()

        # Step 4: Choose reasoning mode
        mode = self._choose_mode(task)
        logger.info(f"Selected reasoning mode: {mode}")

        # Step 5: Execute
        if mode == "tot":
            result = self._run_tot(task, tools_info, skills_info, memories_info)
        else:
            result = self._run_react(task, tools_info, skills_info, memories_info)

        # Step 6: Save task memory
        if self.memory_manager:
            try:
                summary = f"Task: {task}\nResult: {result.get('result', '')[:500]}"
                self.memory_manager.add_episodic(
                    content=summary,
                    category="task",
                    importance=0.7,
                )
            except Exception as e:
                logger.warning(f"Memory save failed: {e}")

        # Step 7: Increment skill usage
        for skill in matched_skills:
            if self.skill_registry:
                self.skill_registry.increment_usage(skill.name)

        elapsed = time.time() - start_time
        result["elapsed_seconds"] = round(elapsed, 1)
        result["mode"] = mode

        logger.info(
            f"Agent completed task in {elapsed:.1f}s "
            f"({result.get('iterations', 0)} iterations)"
        )
        return result

    def _choose_mode(self, task: str) -> str:
        """Choose reasoning mode based on task characteristics."""
        if self.react.should_use_tot(task):
            return "tot"
        return "react"

    def _run_react(
        self,
        task: str,
        tools_info: str,
        skills_info: str,
        memories_info: str,
    ) -> dict:
        """Run ReAct with Reflection."""
        # Patch the tool execution into ReAct engine
        original_execute = self.react._execute_tool

        def tool_executor(tool_name: str, action_input: dict, chat_fn) -> str:
            if self.tool_registry:
                try:
                    result = self.tool_registry.call(tool_name, **action_input)
                    output = result.output or ""
                    if result.error:
                        output += f"\nError: {result.error}"
                    return output
                except Exception as e:
                    return f"Tool execution error: {e}"
            return original_execute(tool_name, action_input, chat_fn)

        self.react._execute_tool = tool_executor

        result = self.react.run(
            llm_chat_fn=self._chat_fn,
            task=task,
            tools_info=tools_info,
            skills_info=skills_info,
            memories_info=memories_info,
        )

        return result

    def _run_tot(
        self,
        task: str,
        tools_info: str,
        skills_info: str,
        memories_info: str,
    ) -> dict:
        """Run Tree of Thoughts."""
        system_prompt = f"{tools_info}\n\n{skills_info}\n\n{memories_info}"

        result_text = self.tot.run(
            llm_chat_fn=self._chat_fn,
            task=task,
            tools_info=system_prompt,
            conversation_history=[],
        )

        return {
            "result": result_text,
            "steps": [],
            "iterations": self.tot.depth,
        }

    def format_result_card(self, result: dict) -> dict:
        """Format agent result as a Lark card data structure."""
        card_data = {
            "title": "Task Result",
            "status": "completed",
            "mode": result.get("mode", "react"),
            "iterations": result.get("iterations", 0),
            "elapsed": result.get("elapsed_seconds", 0),
            "result": result.get("result", ""),
        }

        if result.get("incomplete"):
            card_data["status"] = "incomplete"

        if result.get("error"):
            card_data["status"] = "error"
            card_data["error"] = result["error"]

        return card_data
