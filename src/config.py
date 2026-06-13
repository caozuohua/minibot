"""Configuration loader for MiniBot."""

import os
from dataclasses import dataclass, field
from typing import Any

import yaml

from src.utils.env import load_env, resolve_dict


@dataclass
class ProviderConfig:
    name: str
    api_key: str
    base_url: str | None = None
    models: dict[str, str] = field(default_factory=dict)


@dataclass
class ModelConfig:
    providers: list[ProviderConfig] = field(default_factory=list)
    default_provider: str = "openai"


@dataclass
class LarkConfig:
    app_id: str = ""
    app_secret: str = ""


@dataclass
class MemoryConfig:
    db_path: str = "./data/memory.db"
    top_k: int = 5
    decay_rate: float = 0.02
    archive_threshold: float = 0.1
    cleanup_days: int = 90


@dataclass
class AgentConfig:
    max_iterations: int = 20
    timeout_minutes: int = 30
    reflection_max_rounds: int = 3
    tot_branches: int = 3
    tot_depth: int = 3


@dataclass
class ToolConfig:
    shell_timeout: int = 30
    output_max_bytes: int = 10240
    work_dir: str = "./workspace"
    search_backend: str = "tavily"
    search_api_key: str = ""


@dataclass
class SkillConfig:
    dir: str = "./skills"


@dataclass
class LoggingConfig:
    level: str = "INFO"
    file: str = "./data/minibot.log"


@dataclass
class Config:
    """Root configuration object."""

    lark: LarkConfig = field(default_factory=LarkConfig)
    models: ModelConfig = field(default_factory=ModelConfig)
    memory: MemoryConfig = field(default_factory=MemoryConfig)
    agent: AgentConfig = field(default_factory=AgentConfig)
    tools: ToolConfig = field(default_factory=ToolConfig)
    skills: SkillConfig = field(default_factory=SkillConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)

    @classmethod
    def load(cls, config_path: str = "config.yaml", env_path: str = ".env") -> "Config":
        """Load configuration from YAML file with environment variable resolution."""
        # Resolve to absolute path
        base_dir = os.path.dirname(os.path.abspath(config_path))
        config_path = os.path.abspath(config_path)
        env_path = (
            os.path.abspath(env_path)
            if os.path.isabs(env_path)
            else os.path.join(base_dir, env_path)
        )

        # Load environment variables
        load_env(env_path)

        # Read YAML
        with open(config_path) as f:
            raw = yaml.safe_load(f) or {}

        # Resolve ${VAR} placeholders
        resolved = resolve_dict(raw)

        return cls._from_dict(resolved)

    @classmethod
    def _from_dict(cls, data: dict[str, Any]) -> "Config":
        """Build Config from resolved dictionary."""
        # Lark
        lark_data = data.get("lark", {})
        lark = LarkConfig(
            app_id=lark_data.get("app_id", ""),
            app_secret=lark_data.get("app_secret", ""),
        )

        # Models
        models_data = data.get("models", {})
        providers = []
        for p in models_data.get("providers", []):
            providers.append(
                ProviderConfig(
                    name=p["name"],
                    api_key=p.get("api_key", ""),
                    base_url=p.get("base_url"),
                    models=p.get("models", {}),
                )
            )
        models = ModelConfig(
            providers=providers,
            default_provider=models_data.get("default_provider", "openai"),
        )

        # Memory
        mem_data = data.get("memory", {})
        memory = MemoryConfig(
            db_path=mem_data.get("db_path", "./data/memory.db"),
            top_k=mem_data.get("top_k", 5),
            decay_rate=mem_data.get("decay_rate", 0.02),
            archive_threshold=mem_data.get("archive_threshold", 0.1),
            cleanup_days=mem_data.get("cleanup_days", 90),
        )

        # Agent
        agent_data = data.get("agent", {})
        agent = AgentConfig(
            max_iterations=agent_data.get("max_iterations", 20),
            timeout_minutes=agent_data.get("timeout_minutes", 30),
            reflection_max_rounds=agent_data.get("reflection_max_rounds", 3),
            tot_branches=agent_data.get("tot_branches", 3),
            tot_depth=agent_data.get("tot_depth", 3),
        )

        # Tools
        tools_data = data.get("tools", {})
        tools = ToolConfig(
            shell_timeout=tools_data.get("shell_timeout", 30),
            output_max_bytes=tools_data.get("output_max_bytes", 10240),
            work_dir=tools_data.get("work_dir", "./workspace"),
            search_backend=tools_data.get("search_backend", "tavily"),
            search_api_key=tools_data.get("search_api_key", ""),
        )

        # Skills
        skills_data = data.get("skills", {})
        skills = SkillConfig(dir=skills_data.get("dir", "./skills"))

        # Logging
        log_data = data.get("logging", {})
        logging_cfg = LoggingConfig(
            level=log_data.get("level", "INFO"),
            file=log_data.get("file", "./data/minibot.log"),
        )

        return cls(
            lark=lark,
            models=models,
            memory=memory,
            agent=agent,
            tools=tools,
            skills=skills,
            logging=logging_cfg,
        )

    def validate(self) -> list[str]:
        """Validate configuration, return list of issues."""
        issues = []

        if not self.lark.app_id or not self.lark.app_secret:
            issues.append(
                "Lark app_id and app_secret are required "
                "(set LARK_APP_ID and LARK_APP_SECRET)"
            )

        active_providers = [p for p in self.models.providers if p.api_key]
        if not active_providers:
            issues.append(
                "At least one model provider with a valid API key is required"
            )

        if self.models.default_provider not in [p.name for p in self.models.providers]:
            issues.append(
                f"Default provider '{self.models.default_provider}' "
                "not found in providers list"
            )

        return issues
