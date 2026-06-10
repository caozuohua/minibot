 1: """YAML skill loader."""
 2: 
 3: import logging
 4: import os
 5: from dataclasses import dataclass, field
 6: from typing import List, Optional
 7: 
 8: import yaml
 9: 
10: logger = logging.getLogger(__name__)
11: 
12: 
13: @dataclass
14: class SkillStep:
15:     """A single step in a skill."""
16:     name: str
17:     tool: str
18:     command: str = ""
19:     parameters: List[str] = field(default_factory=list)
20:     on_failure: str = ""
21: 
22: 
23: @dataclass
24: class Skill:
25:     """A skill definition loaded from YAML."""
26:     name: str
27:     description: str
28:     category: str = ""
29:     version: str = "1.0"
30:     steps: List[SkillStep] = field(default_factory=list)
31:     triggers: List[str] = field(default_factory=list)
32:     usage_count: int = 0
33: 
34: 
35: def load_skill_from_yaml(path: str) -> Optional[Skill]:
36:     """Load a single skill from a YAML file."""
37:     try:
38:         with open(path, "r", encoding="utf-8") as f:
39:             data = yaml.safe_load(f)
40: 
41:         if not data or "name" not in data:
42:             logger.warning(f"Invalid skill file (no 'name'): {path}")
43:             return None
44: 
45:         steps = []
46:         for step_data in data.get("steps", []):
47:             steps.append(SkillStep(
48:                 name=step_data.get("name", ""),
49:                 tool=step_data.get("tool", "shell"),
50:                 command=step_data.get("command", ""),
51:                 parameters=step_data.get("parameters", []),
52:                 on_failure=step_data.get("on_failure", ""),
53:             ))
54: 
55:         skill = Skill(
56:             name=data["name"],
57:             description=data.get("description", ""),
58:             category=data.get("category", ""),
59:             version=data.get("version", "1.0"),
60:             steps=steps,
61:             triggers=data.get("triggers", []),
62:         )
63: 
64:         logger.info(f"Loaded skill: {skill.name} ({len(steps)} steps)")
65:         return skill
66: 
67:     except Exception as e:
68:         logger.error(f"Failed to load skill from {path}: {e}")
69:         return None
70: 
71: 
72: def load_skills_from_dir(skills_dir: str) -> List[Skill]:
73:     """Load all skills from a directory."""
74:     skills = []
75: 
76:     if not os.path.isdir(skills_dir):
77:         logger.warning(f"Skills directory not found: {skills_dir}")
78:         return skills
79: 
80:     for filename in sorted(os.listdir(skills_dir)):
81:         if filename.endswith((".yaml", ".yml")):
82:             path = os.path.join(skills_dir, filename)
83:             skill = load_skill_from_yaml(path)
84:             if skill:
85:                 skills.append(skill)
86: 
87:     logger.info(f"Loaded {len(skills)} skills from {skills_dir}")
88:     return skills
