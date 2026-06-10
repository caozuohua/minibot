 1: """SQLite storage layer for MiniBot memory."""
 2: 
 3: import math
 4: import sqlite3
 5: import struct
 6: import time
 7: from typing import List, Optional, Tuple
 8: 
 9: 
10: class SQLiteStore:
11:     """SQLite-based memory storage with vector search support."""
12: 
13:     def __init__(self, db_path: str):
14:         self.db_path = db_path
15:         self._conn = sqlite3.connect(db_path)
16:         self._conn.row_factory = sqlite3.Row
17:         self._init_tables()
18: 
19:     def _init_tables(self):
20:         """Create tables if they don't exist."""
21:         cur = self._conn.cursor()
22: 
23:         cur.execute("""
24:             CREATE TABLE IF NOT EXISTS episodic_memories (
25:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
26:                 content TEXT NOT NULL,
27:                 embedding BLOB,
28:                 category TEXT DEFAULT 'task',
29:                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
30:                 importance_score REAL DEFAULT 1.0
31:             )
32:         """)
33: 
34:         cur.execute("""
35:             CREATE TABLE IF NOT EXISTS semantic_memories (
36:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
37:                 content TEXT NOT NULL,
38:                 embedding BLOB,
39:                 category TEXT,
40:                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
41:                 importance_score REAL DEFAULT 0.8
42:             )
43:         """)
44: 
45:         cur.execute("""
46:             CREATE TABLE IF NOT EXISTS procedural_memories (
47:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
48:                 skill_name TEXT NOT NULL,
49:                 experience TEXT NOT NULL,
50:                 embedding BLOB,
51:                 timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
52:                 importance_score REAL DEFAULT 0.5
53:             )
54:         """)
55: 
56:         cur.execute("""
57:             CREATE TABLE IF NOT EXISTS archived_memories (
58:                 id INTEGER PRIMARY KEY AUTOINCREMENT,
59:                 source_table TEXT,
60:                 original_id INTEGER,
61:                 content TEXT,
62:                 archived_at DATETIME DEFAULT CURRENT_TIMESTAMP
63:             )
64:         """)
65: 
66:         # Create indexes for faster search
67:         cur.execute("CREATE INDEX IF NOT EXISTS idx_episodic_category ON episodic_memories(category)")
68:         cur.execute("CREATE INDEX IF NOT EXISTS idx_semantic_category ON semantic_memories(category)")
69:         cur.execute("CREATE INDEX IF NOT EXISTS idx_procedural_skill ON procedural_memories(skill_name)")
70: 
71:         self._conn.commit()
72: 
73:     def _floats_to_blob(self, floats: List[float]) -> bytes:
74:         """Convert list of floats to a compact binary blob."""
75:         return struct.pack(f"{len(floats)}f", *floats)
76: 
77:     def _blob_to_floats(self, blob: bytes) -> List[float]:
78:         """Convert binary blob back to list of floats."""
79:         if not blob:
80:             return []
81:         count = len(blob) // 4
82:         return list(struct.unpack(f"{count}f", blob))
83: 
84:     def _cosine_similarity(self, a: List[float], b: List[float]) -> float:
85:         """Compute cosine similarity between two vectors."""
86:         if not a or not b:
87:             return 0.0
88:         dot = sum(x * y for x, y in zip(a, b))
89:         mag_a = math.sqrt(sum(x * x for x in a))
90:         mag_b = math.sqrt(sum(x * x for x in b))
91:         if mag_a == 0 or mag_b == 0:
92:             return 0.0
93:         return dot / (mag_a * mag_b)
94: 
95:     def add_memory(self, table: str, content: str, embedding: List[float],
96:                    category: str = None, importance: float = 1.0,
97:                    skill_name: str = None) -> int:
98:         """Add a memory entry. Returns the new row id."""
99:         blob = self._floats_to_blob(embedding)
100: cur = self._conn.cursor()
101:
102: if table == "episodic":
103: cur.execute(
104: "INSERT INTO episodic_memories (content, embedding, category, importance_score) VALUES (?, ?, ?, ?)",
105: (content, blob, category or "task", importance)
106: )
107: elif table == "semantic":
108: cur.execute(
109: "INSERT INTO semantic_memories (content, embedding, category, importance_score) VALUES (?, ?, ?, ?)",
110: (content, blob, category, importance)
111: )
112: elif table == "procedural":
113: cur.execute(
114: "INSERT INTO procedural_memories (skill_name, experience, embedding, importance_score) VALUES (?, ?, ?, ?)",
115: (skill_name or "unknown", content, blob, importance)
116: )
117: else:
118: raise ValueError(f"Unknown memory table: {table}")
119:
120: self._conn.commit()
121: return cur.lastrowid
122:
123: def search(self, table: str, query_embedding: List[float],
124: top_k: int = 5, category: str = None) -> List[Tuple[str, float]]:
125: """Search memories by vector similarity.
126:
127: Returns list of (content, similarity_score) tuples, sorted by relevance.
128: """
129: cur = self._conn.cursor()
130:
131: if table == "episodic":
132: cur.execute("SELECT id, content, embedding, importance_score FROM episodic_memories")
133: elif table == "semantic":
134: if category:
135: cur.execute("SELECT id, content, embedding, importance_score FROM semantic_memories WHERE category = ?", (category,))
136: else:
137: cur.execute("SELECT id, content, embedding, importance_score FROM semantic_memories")
138: elif table == "procedural":
139: cur.execute("SELECT id, experience, embedding, importance_score FROM procedural_memories")
140: else:
141: raise ValueError(f"Unknown memory table: {table}")
142:
143: rows = cur.fetchall()
144: results = []
145:
146: for row in rows:
147: row_id, content, blob, score = row[0], row[1], row[2], row[3]
148: if table == "procedural":
149: content = row[1] # experience column
150:
151: if blob is None:
152: continue
153:
154: vec = self._blob_to_floats(blob)
155: similarity = self._cosine_similarity(query_embedding, vec)
156: # Weight by importance score
157: weighted_score = similarity * score
158: results.append((content, weighted_score))
159:
160: # Sort by weighted score descending
161: results.sort(key=lambda x: x[1], reverse=True)
162: return results[:top_k]
163:
164: def decay_scores(self, table: str, decay_rate: float = 0.02):
165: """Decay importance scores for all memories in a table."""
166: table_map = {
167: "episodic": "episodic_memories",
168: "semantic": "semantic_memories",
169: "procedural": "procedural_memories",
170: }
171: db_table = table_map.get(table)
172: if not db_table:
173: return
174:
175: cur = self._conn.cursor()
176: cur.execute(f"UPDATE {db_table} SET importance_score = MAX(0.0, importance_score * (1 - ?))", (decay_rate,))
177: self._conn.commit()
178: return cur.rowcount
179:
180: def archive_low_score(self, table: str, threshold: float = 0.1) -> int:
181: """Move low-score memories to archive. Returns count of archived."""
182: table_map = {
183: "episodic": ("episodic_memories", "content"),
184: "semantic": ("semantic_memories", "content"),
185: "procedural": ("procedural_memories", "experience"),
186: }
187: db_table, content_col = table_map.get(table, (None, None))
188: if not db_table:
189: return 0
190:
191: cur = self._conn.cursor()
192: # Get low-score entries
193: cur.execute(f"SELECT id, {content_col} FROM {db_table} WHERE importance_score < ?", (threshold,))
194: rows = cur.fetchall()
195:
196: for row in rows:
197: row_id, content = row[0], row[1]
198: cur.execute(
199: "INSERT INTO archived_memories (source_table, original_id, content) VALUES (?, ?, ?)",
200: (table, row_id, content)
201: )
202: cur.execute(f"DELETE FROM {db_table} WHERE id = ?", (row_id,))
203:
204: self._conn.commit()
205: return len(rows)
206:
207: def cleanup_old_archived(self, days: int = 90) -> int:
208: """Delete archived memories older than days. Returns count deleted."""
209: cur = self._conn.cursor()
210: cutoff = time.time() - (days * 86400)
211: cur.execute("DELETE FROM archived_memories WHERE archived_at < datetime('now', ?)", (f"-{days} days",))
212: self._conn.commit()
213: return cur.rowcount
214:
215: def close(self):
216: """Close the database connection."""
217: self._conn.close()
