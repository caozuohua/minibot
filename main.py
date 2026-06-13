#!/usr/bin/env python3
"""MiniBot — Lightweight autonomous agent for small VPS.

Usage:
    python main.py              # Start with default config.yaml
    python main.py --config /path/to/config.yaml
    python main.py --validate   # Validate config and exit
"""

import argparse
import asyncio
import logging
import os
import sys

from src.agent.core import AgentCore
from src.config import Config
from src.gateway.lark_gateway import LarkGateway
from src.memory.manager import MemoryManager
from src.models.router import ModelRouter
from src.skills.registry import SkillRegistry
from src.tools.registry import ToolRegistry


def setup_logging(config: Config) -> None:
    """Configure logging based on config."""
    log_file = config.logging.file
    log_dir = os.path.dirname(os.path.abspath(log_file))
    os.makedirs(log_dir, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, config.logging.level.upper(), logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler(log_file, encoding="utf-8"),
        ],
    )


def build_app(config: Config):
    """Build all application components."""
    logger = logging.getLogger("minibot")

    # 1. Model Router
    logger.info("Initializing Model Router...")
    model_router = ModelRouter(config)
    logger.info(f"Available providers: {model_router.available_providers}")

    # 2. Memory Manager (with embedding function from model router)
    logger.info("Initializing Memory Manager...")

    def embed_fn(text):
        return model_router.embed(text)

    memory_manager = MemoryManager(
        config, embed_fn=embed_fn if model_router.available_providers else None
    )

    # 3. Tool Registry
    logger.info("Initializing Tool Registry...")
    tool_registry = ToolRegistry(config)
    logger.info(f"Available tools: {tool_registry.get_tool_names()}")

    # 4. Skill Registry
    logger.info("Initializing Skill Registry...")
    skill_registry = SkillRegistry(config)
    logger.info(f"Loaded skills: {[s.name for s in skill_registry.list_skills()]}")

    # 5. Agent Core
    logger.info("Initializing Agent Core...")
    agent = AgentCore(
        config=config,
        model_router=model_router,
        tool_registry=tool_registry,
        memory_manager=memory_manager,
        skill_registry=skill_registry,
    )

    # 6. Lark Gateway
    logger.info("Initializing Lark Gateway...")
    gateway = LarkGateway(config)

    # Wire up message handler
    async def handle_message(user_id: str, text: str):
        """Handle incoming message from Lark."""
        logger.info(f"Processing message from {user_id}: {text[:100]}")

        try:
            # Send task start notification
            await gateway.send_task_start(user_id, text)

            # Run agent
            result = agent.run(task=text, user_id=user_id)

            # Send result
            if result.get("error") or result.get("incomplete"):
                await gateway.send_task_error(
                    user_id,
                    error=result.get("error", "Task incomplete"),
                    partial_result=result.get("result", ""),
                )
            else:
                await gateway.send_task_result(
                    user_id,
                    summary=result.get("result", "Task completed"),
                    mode=result.get("mode", "react"),
                    iterations=result.get("iterations", 0),
                    elapsed=result.get("elapsed_seconds", 0),
                )

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            await gateway.send_task_error(user_id, str(e))

    gateway.on_message(handle_message)

    return gateway, agent, memory_manager


def main():
    parser = argparse.ArgumentParser(description="MiniBot Agent")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")
    parser.add_argument(
        "--validate", action="store_true", help="Validate config and exit"
    )
    args = parser.parse_args()

    # Load configuration
    try:
        config = Config.load(args.config)
    except FileNotFoundError:
        print(f"Error: Config file not found: {args.config}")
        sys.exit(1)
    except Exception as e:
        print(f"Error loading config: {e}")
        sys.exit(1)

    # Validate
    issues = config.validate()
    if issues:
        print("Configuration issues found:")
        for issue in issues:
            print(f" - {issue}")
        if args.validate:
            sys.exit(1)

    if args.validate:
        print("Configuration is valid.")
        print(f" Providers: {[p.name for p in config.models.providers]}")
        print(f" Default: {config.models.default_provider}")
        print(f" Memory: {config.memory.db_path}")
        print(f" Skills dir: {config.skills.dir}")
        print(f" Work dir: {config.tools.work_dir}")
        sys.exit(0)

    # Setup logging
    setup_logging(config)
    logger = logging.getLogger("minibot")

    logger.info("=" * 60)
    logger.info("MiniBot starting up...")
    logger.info("=" * 60)

    # Build application
    gateway, _agent, memory_manager = build_app(config)

    logger.info("MiniBot ready.")
    logger.info("Press Ctrl+C to stop.")

    # Graceful shutdown
    shutdown_event = asyncio.Event()

    def signal_handler():
        logger.info("Shutdown signal received...")
        shutdown_event.set()

    # Run async gateway
    async def run():
        await gateway.start()

    try:
        asyncio.run(run())
    except KeyboardInterrupt:
        logger.info("Shutting down...")
    finally:
        gateway.stop()
        memory_manager.close()
        logger.info("MiniBot stopped.")


if __name__ == "__main__":
    main()
