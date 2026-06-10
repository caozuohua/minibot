 1: """Skill registry — manages available skills."""
 2: 
 3: import logging
 4: import re
 5: from typing import Dict, List, Optional
 6: 
 7: from src.config import Config
 8: from src.skills.loader import Skill, load_skills_from_dir
 9: 
10: logger = logging.getLogger(__name__)
11: 
12: 
13: class SkillRegistry:
14:     """Registry of available skills for the agent."""
15: 
16:     def __init__(self, config: Config):
17:         self.config = config.skills
18:         self._skills: Dict[str, Skill] = {}
19:         self.load_all()
20: 
21:     def load_all(self):
22:         """Load all skills from the skills directory."""
23:         skills = load_skills_from_dir(self.config.dir)
24:         for skill in skills:
25:             self._skills[skill.name] = skill
26: 
27:     def get(self, name: str) -> Optional[Skill]:
28:         """Get a skill by name."""
29:         return self._skills.get(name)
30: 
31:     def match_triggers(self, message: str) -> List[Skill]:
32:         """Match skills by trigger keywords in the message."""
33:         matches = []
34:         message_lower = message.lower()
35: 
36:         for skill in self._skills.values():
37:             for trigger in skill.triggers:
38:                 if trigger.lower() in message_lower:
39:                     matches.append(skill)
40:                     break
41: 
42:         # Sort by usage count (most used first)
43:         matches.sort(key=lambda s: s.usage_count, reverse=True)
44:         return matches
45: 
46:     def increment_usage(self, name: str):
47:         """Increment usage count for a skill."""
48:         if name in self._skills:
49:             self._skills[name].usage_count += 1
50: 
51:     def list_skills(self) -> List[Skill]:
52:         """Return all registered skills."""
53:         return list(self._skills.values())
54: 
55:     def format_for_prompt(self) -> str:
56:         """Format skills as a prompt-friendly string."""
57:         if not self._skills:
58:             return "No skills available."
59: 
60:         lines = ["Available skills:"]
61:         for skill in self._skills.values():
62:             lines.append(
63:                 f"  - {skill.name}: {skill.description} "
64:                 f"(triggers: {', '.join(skill.triggers[:3])})"
65:             )
66:         return "\n".join(lines)
67: 
68:     def get_skill_steps(self, name: str, params: dict = None) -> List[dict]:
69:         """Get skill steps with parameters filled in.
70:         
71:         Returns list of step dicts ready for execution.
72:         """
73:         skill = self._skills.get(name)
74:         if not skill:
75:             return []
76: 
77:         params = params or {}
78:         steps = []
79:         for step in skill.steps:
80:             command = step.command
81:             for key, value in params.items():
82:                 command = command.replace(f"{{{key}}}", str(value))
83:             steps.append({
84:                 "name": step.name,
85:                 "tool": step.tool,
86:                 "command": command,
87:                 "on_failure": step.on_failure,
88:             })
89: 
90:         return steps
