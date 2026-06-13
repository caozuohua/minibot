"""Memory Manager — high-level memory operations with embedding support."""

import logging
import os

from src.config import Config
from src.memory.sqlite_store import SQLiteStore

logger = logging.getLogger(__name__)


class MemoryManager:
    """Manages long-term memory with semantic search capabilities."""

    def __init__(self, config: Config, embed_fn=None):
        """
        Args:
            config: Application config.
            embed_fn: Function that takes text and returns embedding vector.
                      If None, memories are stored without embeddings.
        """
        self.config = config.memory
        self._embed_fn = embed_fn
        self._store = SQLiteStore(config.memory.db_path)

        # Ensure db directory exists
        db_dir = os.path.dirname(config.memory.db_path)
        if db_dir:
            os.makedirs(db_dir, exist_ok=True)

    def _get_embedding(self, text: str) -> list[float] | None:
        """Generate embedding for text, or None if embed_fn not available."""
        if self._embed_fn:
            try:
                return self._embed_fn(text)
            except Exception as e:
                logger.warning(f"Embedding failed: {e}")
        return None

    def add_episodic(
        self, content: str, category: str = "task", importance: float = 1.0
    ) -> int:
        """Add an episodic memory (task execution record)."""
        embedding = self._get_embedding(content)
        return self._store.add_memory(
            table="episodic",
            content=content,
            embedding=embedding or [],
            category=category,
            importance=importance,
        )

    def add_semantic(
        self, content: str, category: str | None = None, importance: float = 0.8
    ) -> int:
        """Add a semantic memory (user-saved knowledge)."""
        embedding = self._get_embedding(content)
        return self._store.add_memory(
            table="semantic",
            content=content,
            embedding=embedding or [],
            category=category,
            importance=importance,
        )

    def add_procedural(
        self, skill_name: str, experience: str, importance: float = 0.5
    ) -> int:
        """Add a procedural memory (skill execution experience)."""
        embedding = self._get_embedding(experience)
        return self._store.add_memory(
            table="procedural",
            content=experience,
            embedding=embedding or [],
            skill_name=skill_name,
            importance=importance,
        )

    def search(
        self,
        query: str,
        top_k: int | None = None,
        category: str | None = None,
    ) -> list[tuple[str, float]]:
        """Search memories by semantic similarity.

        Searches all memory types and returns combined results.

        Returns:
            List of (content, score) tuples sorted by relevance.
        """
        top_k = top_k or self.config.top_k
        query_embedding = self._get_embedding(query)

        if not query_embedding:
            logger.warning("No embedding available for search, returning empty results")
            return []

        all_results = []

        # Search episodic memories
        episodic = self._store.search("episodic", query_embedding, top_k)
        all_results.extend(episodic)

        # Search semantic memories
        semantic = self._store.search("semantic", query_embedding, top_k, category)
        all_results.extend(semantic)

        # Search procedural memories
        procedural = self._store.search("procedural", query_embedding, top_k)
        all_results.extend(procedural)

        # Sort by score and return top_k
        all_results.sort(key=lambda x: x[1], reverse=True)
        return all_results[:top_k]

    def decay_all(self):
        """Decay importance scores for all memory types."""
        for table in ["episodic", "semantic", "procedural"]:
            count = self._store.decay_scores(table, self.config.decay_rate)
            if count:
                logger.info(f"Decayed {count} memories in {table}")

    def archive_low_score(self) -> int:
        """Archive memories below threshold. Returns total archived count."""
        total = 0
        for table in ["episodic", "semantic", "procedural"]:
            count = self._store.archive_low_score(table, self.config.archive_threshold)
            total += count
        if total:
            logger.info(f"Archived {total} low-score memories")
        return total

    def cleanup_old(self) -> int:
        """Clean up old archived memories. Returns count deleted."""
        count = self._store.cleanup_old_archived(self.config.cleanup_days)
        if count:
            logger.info(f"Cleaned up {count} old archived memories")
        return count

    def close(self):
        """Close the database connection."""
        self._store.close()
