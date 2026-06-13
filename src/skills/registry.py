"""Skill registry — manages available skills."""

import logging

from src.config import Config
from src.skills.loader import Skill, load_skills_from_dir

logger = logging.getLogger(__name__)


class SkillRegistry:
    """Registry of available skills for the agent."""

    def __init__(self, config: Config):
        self.config = config.skills
        self._skills: dict[str, Skill] = {}
        self.load_all()

    def load_all(self):
        """Load all skills from the skills directory."""
        skills = load_skills_from_dir(self.config.dir)
        for skill in skills:
            self._skills[skill.name] = skill

    def get(self, name: str) -> Skill | None:
        """Get a skill by name."""
        return self._skills.get(name)

    def match_triggers(self, message: str) -> list[Skill]:
        """Match skills by trigger keywords in the message."""
        matches = []
        message_lower = message.lower()

        for skill in self._skills.values():
            for trigger in skill.triggers:
                if trigger.lower() in message_lower:
                    matches.append(skill)
                    break

        # Sort by usage count (most used first)
        matches.sort(key=lambda s: s.usage_count, reverse=True)
        return matches

    def increment_usage(self, name: str):
        """Increment usage count for a skill."""
        if name in self._skills:
            self._skills[name].usage_count += 1

    def list_skills(self) -> list[Skill]:
        """Return all registered skills."""
        return list(self._skills.values())

    def format_for_prompt(self) -> str:
        """Format skills as a prompt-friendly string."""
        if not self._skills:
            return "No skills available."

        lines = ["Available skills:"]
        for skill in self._skills.values():
            lines.append(
                f"  - {skill.name}: {skill.description} "
                f"(triggers: {', '.join(skill.triggers[:3])})"
            )
        return "\n".join(lines)

    def get_skill_steps(self, name: str, params: dict | None = None) -> list[dict]:
        """Get skill steps with parameters filled in.

        Returns list of step dicts ready for execution.
        """
        skill = self._skills.get(name)
        if not skill:
            return []

        params = params or {}
        steps = []
        for step in skill.steps:
            command = step.command
            for key, value in params.items():
                command = command.replace(f"{{{key}}}", str(value))
            steps.append(
                {
                    "name": step.name,
                    "tool": step.tool,
                    "command": command,
                    "on_failure": step.on_failure,
                }
            )

        return steps
