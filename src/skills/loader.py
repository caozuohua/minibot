"""YAML skill loader."""

import logging
import os
from dataclasses import dataclass, field

import yaml

logger = logging.getLogger(__name__)


@dataclass
class SkillStep:
    """A single step in a skill."""

    name: str
    tool: str
    command: str = ""
    parameters: list[str] = field(default_factory=list)
    on_failure: str = ""


@dataclass
class Skill:
    """A skill definition loaded from YAML."""

    name: str
    description: str
    category: str = ""
    version: str = "1.0"
    steps: list[SkillStep] = field(default_factory=list)
    triggers: list[str] = field(default_factory=list)
    usage_count: int = 0


def load_skill_from_yaml(path: str) -> Skill | None:
    """Load a single skill from a YAML file."""
    try:
        with open(path, encoding="utf-8") as f:
            data = yaml.safe_load(f)

        if not data or "name" not in data:
            logger.warning(f"Invalid skill file (no 'name'): {path}")
            return None

        steps = []
        for step_data in data.get("steps", []):
            steps.append(
                SkillStep(
                    name=step_data.get("name", ""),
                    tool=step_data.get("tool", "shell"),
                    command=step_data.get("command", ""),
                    parameters=step_data.get("parameters", []),
                    on_failure=step_data.get("on_failure", ""),
                )
            )

        skill = Skill(
            name=data["name"],
            description=data.get("description", ""),
            category=data.get("category", ""),
            version=data.get("version", "1.0"),
            steps=steps,
            triggers=data.get("triggers", []),
        )

        logger.info(f"Loaded skill: {skill.name} ({len(steps)} steps)")
        return skill

    except Exception as e:
        logger.error(f"Failed to load skill from {path}: {e}")
        return None


def load_skills_from_dir(skills_dir: str) -> list[Skill]:
    """Load all skills from a directory."""
    skills = []

    if not os.path.isdir(skills_dir):
        logger.warning(f"Skills directory not found: {skills_dir}")
        return skills

    for filename in sorted(os.listdir(skills_dir)):
        if filename.endswith((".yaml", ".yml")):
            path = os.path.join(skills_dir, filename)
            skill = load_skill_from_yaml(path)
            if skill:
                skills.append(skill)

    logger.info(f"Loaded {len(skills)} skills from {skills_dir}")
    return skills
