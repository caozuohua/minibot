"""SQLite storage layer for MiniBot memory."""

import math
import sqlite3
import struct
import time


class SQLiteStore:
    """SQLite-based memory storage with vector search support."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        self._conn = sqlite3.connect(db_path)
        self._conn.row_factory = sqlite3.Row
        self._init_tables()

    def _init_tables(self):
        """Create tables if they don't exist."""
        cur = self._conn.cursor()

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS episodic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                embedding BLOB,
                category TEXT DEFAULT 'task',
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                importance_score REAL DEFAULT 1.0
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS semantic_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                embedding BLOB,
                category TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                importance_score REAL DEFAULT 0.8
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS procedural_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                skill_name TEXT NOT NULL,
                experience TEXT NOT NULL,
                embedding BLOB,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                importance_score REAL DEFAULT 0.5
            )
        """
        )

        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS archived_memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                source_table TEXT,
                original_id INTEGER,
                content TEXT,
                archived_at DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

        # Create indexes for faster search
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_episodic_category "
            "ON episodic_memories(category)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_semantic_category "
            "ON semantic_memories(category)"
        )
        cur.execute(
            "CREATE INDEX IF NOT EXISTS idx_procedural_skill "
            "ON procedural_memories(skill_name)"
        )

        self._conn.commit()

    def _floats_to_blob(self, floats: list[float]) -> bytes:
        """Convert list of floats to a compact binary blob."""
        return struct.pack(f"{len(floats)}f", *floats)

    def _blob_to_floats(self, blob: bytes) -> list[float]:
        """Convert binary blob back to list of floats."""
        if not blob:
            return []
        count = len(blob) // 4
        return list(struct.unpack(f"{count}f", blob))

    def _cosine_similarity(self, a: list[float], b: list[float]) -> float:
        """Compute cosine similarity between two vectors."""
        if not a or not b:
            return 0.0
        dot = sum(x * y for x, y in zip(a, b, strict=False))
        mag_a = math.sqrt(sum(x * x for x in a))
        mag_b = math.sqrt(sum(x * x for x in b))
        if mag_a == 0 or mag_b == 0:
            return 0.0
        return dot / (mag_a * mag_b)

    def add_memory(
        self,
        table: str,
        content: str,
        embedding: list[float],
        category: str | None = None,
        importance: float = 1.0,
        skill_name: str | None = None,
    ) -> int:
        """Add a memory entry. Returns the new row id."""
        blob = self._floats_to_blob(embedding)
        cur = self._conn.cursor()

        if table == "episodic":
            cur.execute(
                "INSERT INTO episodic_memories "
                "(content, embedding, category, importance_score) "
                "VALUES (?, ?, ?, ?)",
                (content, blob, category or "task", importance),
            )
        elif table == "semantic":
            cur.execute(
                "INSERT INTO semantic_memories "
                "(content, embedding, category, importance_score) "
                "VALUES (?, ?, ?, ?)",
                (content, blob, category, importance),
            )
        elif table == "procedural":
            cur.execute(
                "INSERT INTO procedural_memories "
                "(skill_name, experience, embedding, importance_score) "
                "VALUES (?, ?, ?, ?)",
                (skill_name or "unknown", content, blob, importance),
            )
        else:
            raise ValueError(f"Unknown memory table: {table}")

        self._conn.commit()
        return cur.lastrowid

    def search(
        self,
        table: str,
        query_embedding: list[float],
        top_k: int = 5,
        category: str | None = None,
    ) -> list[tuple[str, float]]:
        """Search memories by vector similarity.

        Returns list of (content, similarity_score) tuples, sorted by relevance.
        """
        cur = self._conn.cursor()

        if table == "episodic":
            cur.execute(
                "SELECT id, content, embedding, importance_score FROM episodic_memories"
            )
        elif table == "semantic":
            if category:
                cur.execute(
                    "SELECT id, content, embedding, importance_score "
                    "FROM semantic_memories WHERE category = ?",
                    (category,),
                )
            else:
                cur.execute(
                    "SELECT id, content, embedding, importance_score "
                    "FROM semantic_memories"
                )
        elif table == "procedural":
            cur.execute(
                "SELECT id, experience, embedding, importance_score "
                "FROM procedural_memories"
            )
        else:
            raise ValueError(f"Unknown memory table: {table}")

        rows = cur.fetchall()
        results = []

        for row in rows:
            _row_id, content, blob, score = row[0], row[1], row[2], row[3]
            if table == "procedural":
                content = row[1]  # experience column

            if blob is None:
                continue

            vec = self._blob_to_floats(blob)
            similarity = self._cosine_similarity(query_embedding, vec)
            # Weight by importance score
            weighted_score = similarity * score
            results.append((content, weighted_score))

        # Sort by weighted score descending
        results.sort(key=lambda x: x[1], reverse=True)
        return results[:top_k]

    def decay_scores(self, table: str, decay_rate: float = 0.02):
        """Decay importance scores for all memories in a table."""
        table_map = {
            "episodic": "episodic_memories",
            "semantic": "semantic_memories",
            "procedural": "procedural_memories",
        }
        db_table = table_map.get(table)
        if not db_table:
            return

        cur = self._conn.cursor()
        cur.execute(
            f"UPDATE {db_table} SET importance_score = "
            f"MAX(0.0, importance_score * (1 - ?))",
            (decay_rate,),
        )
        self._conn.commit()
        return cur.rowcount

    def archive_low_score(self, table: str, threshold: float = 0.1) -> int:
        """Move low-score memories to archive. Returns count of archived."""
        table_map = {
            "episodic": ("episodic_memories", "content"),
            "semantic": ("semantic_memories", "content"),
            "procedural": ("procedural_memories", "experience"),
        }
        db_table, content_col = table_map.get(table, (None, None))
        if not db_table:
            return 0

        cur = self._conn.cursor()
        # Get low-score entries
        cur.execute(
            f"SELECT id, {content_col} FROM {db_table} WHERE importance_score < ?",
            (threshold,),
        )
        rows = cur.fetchall()

        for row in rows:
            row_id, content = row[0], row[1]
            cur.execute(
                "INSERT INTO archived_memories "
                "(source_table, original_id, content) "
                "VALUES (?, ?, ?)",
                (table, row_id, content),
            )
            cur.execute(f"DELETE FROM {db_table} WHERE id = ?", (row_id,))

        self._conn.commit()
        return len(rows)

    def cleanup_old_archived(self, days: int = 90) -> int:
        """Delete archived memories older than days. Returns count deleted."""
        cur = self._conn.cursor()
        time.time() - (days * 86400)
        cur.execute(
            "DELETE FROM archived_memories WHERE archived_at < datetime('now', ?)",
            (f"-{days} days",),
        )
        self._conn.commit()
        return cur.rowcount

    def close(self):
        """Close the database connection."""
        self._conn.close()
