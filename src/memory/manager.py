 1: """Memory Manager — high-level memory operations with embedding support."""
 2: 
 3: import logging
 4: import os
 5: from typing import List, Optional, Tuple
 6: 
 7: from src.config import Config
 8: from src.memory.sqlite_store import SQLiteStore
 9: 
10: logger = logging.getLogger(__name__)
11: 
12: 
13: class MemoryManager:
14:     """Manages long-term memory with semantic search capabilities."""
15: 
16:     def __init__(self, config: Config, embed_fn=None):
17:         """
18:         Args:
19:             config: Application config.
20:             embed_fn: Function that takes text and returns embedding vector.
21:                       If None, memories are stored without embeddings.
22:         """
23:         self.config = config.memory
24:         self._embed_fn = embed_fn
25:         self._store = SQLiteStore(config.memory.db_path)
26: 
27:         # Ensure db directory exists
28:         db_dir = os.path.dirname(config.memory.db_path)
29:         if db_dir:
30:             os.makedirs(db_dir, exist_ok=True)
31: 
32:     def _get_embedding(self, text: str) -> Optional[List[float]]:
33:         """Generate embedding for text, or None if embed_fn not available."""
34:         if self._embed_fn:
35:             try:
36:                 return self._embed_fn(text)
37:             except Exception as e:
38:                 logger.warning(f"Embedding failed: {e}")
39:         return None
40: 
41:     def add_episodic(self, content: str, category: str = "task",
42:                      importance: float = 1.0) -> int:
43:         """Add an episodic memory (task execution record)."""
44:         embedding = self._get_embedding(content)
45:         return self._store.add_memory(
46:             table="episodic",
47:             content=content,
48:             embedding=embedding or [],
49:             category=category,
50:             importance=importance,
51:         )
52: 
53:     def add_semantic(self, content: str, category: str = None,
54:                      importance: float = 0.8) -> int:
55:         """Add a semantic memory (user-saved knowledge)."""
56:         embedding = self._get_embedding(content)
57:         return self._store.add_memory(
58:             table="semantic",
59:             content=content,
60:             embedding=embedding or [],
61:             category=category,
62:             importance=importance,
63:         )
64: 
65:     def add_procedural(self, skill_name: str, experience: str,
66:                        importance: float = 0.5) -> int:
67:         """Add a procedural memory (skill execution experience)."""
68:         embedding = self._get_embedding(experience)
69:         return self._store.add_memory(
70:             table="procedural",
71:             content=experience,
72:             embedding=embedding or [],
73:             skill_name=skill_name,
74:             importance=importance,
75:         )
76: 
77:     def search(self, query: str, top_k: int = None,
78:                category: str = None) -> List[Tuple[str, float]]:
79:         """Search memories by semantic similarity.
80:         
81:         Searches all memory types and returns combined results.
82:         
83:         Returns:
84:             List of (content, score) tuples sorted by relevance.
85:         """
86:         top_k = top_k or self.config.top_k
87:         query_embedding = self._get_embedding(query)
88: 
89:         if not query_embedding:
90:             logger.warning("No embedding available for search, returning empty results")
91:             return []
92: 
93:         all_results = []
94: 
95:         # Search episodic memories
96:         episodic = self._store.search("episodic", query_embedding, top_k)
97:         all_results.extend(episodic)
98: 
99:         # Search semantic memories
100: semantic = self._store.search("semantic", query_embedding, top_k, category)
101: all_results.extend(semantic)
102:
103: # Search procedural memories
104: procedural = self._store.search("procedural", query_embedding, top_k)
105: all_results.extend(procedural)
106:
107: # Sort by score and return top_k
108: all_results.sort(key=lambda x: x[1], reverse=True)
109: return all_results[:top_k]
110:
111: def decay_all(self):
112: """Decay importance scores for all memory types."""
113: for table in ["episodic", "semantic", "procedural"]:
114: count = self._store.decay_scores(table, self.config.decay_rate)
115: if count:
116: logger.info(f"Decayed {count} memories in {table}")
117:
118: def archive_low_score(self) -> int:
119: """Archive memories below threshold. Returns total archived count."""
120: total = 0
121: for table in ["episodic", "semantic", "procedural"]:
122: count = self._store.archive_low_score(table, self.config.archive_threshold)
123: total += count
124: if total:
125: logger.info(f"Archived {total} low-score memories")
126: return total
127:
128: def cleanup_old(self) -> int:
129: """Clean up old archived memories. Returns count deleted."""
130: count = self._store.cleanup_old_archived(self.config.cleanup_days)
131: if count:
132: logger.info(f"Cleaned up {count} old archived memories")
133: return count
134:
135: def close(self):
136: """Close the database connection."""
137: self._store.close()
