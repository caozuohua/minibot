 1: """Lark message card templates."""
 2: 
 3: 
 4: def task_start_card(goal: str, plan: str = "") -> dict:
 5:     """Task start card showing the goal and plan."""
 6:     elements = [
 7:         {
 8:             "tag": "div",
 9:             "text": {
10:                 "tag": "lark_md",
11:                 "content": f"🎯 **Task Started**\n\n**Goal:** {goal}",
12:             },
13:         }
14:     ]
15: 
16:     if plan:
17:         elements.append({
18:             "tag": "div",
19:             "text": {
20:                 "tag": "lark_md",
21:                 "content": f"\n📋 **Plan:**\n{plan}",
22:             },
23:         })
24: 
25:     return {
26:         "header": {
27:             "title": {"tag": "plain_text", "content": "MiniBot — Task Started"},
28:             "template": "blue",
29:         },
30:         "elements": elements,
31:     }
32: 
33: 
34: def task_progress_card(step: int, total: int, detail: str) -> dict:
35:     """Progress update card."""
36:     percentage = int((step / total) * 100) if total > 0 else 0
37: 
38:     return {
39:         "header": {
40:             "title": {"tag": "plain_text", "content": f"MiniBot — Progress ({step}/{total})"},
41:             "template": "cyan",
42:         },
43:         "elements": [
44:             {
45:                 "tag": "div",
46:                 "text": {
47:                     "tag": "lark_md",
48:                     "content": f"**Step {step}/{total}** ({percentage}%)\n\n{detail}",
49:                 },
50:             },
51:             {
52:                 "tag": "progress",
53:                 "percentage": percentage,
54:                 "color": "blue",
55:             },
56:         ],
57:     }
58: 
59: 
60: def task_result_card(summary: str, details: str = "", mode: str = "react",
61:                      iterations: int = 0, elapsed: float = 0) -> dict:
62:     """Task completion result card."""
63:     elements = [
64:         {
65:             "tag": "div",
66:             "text": {
67:                 "tag": "lark_md",
68:                 "content": f"✅ **Task Completed**\n\n{summary}",
69:             },
70:         },
71:     ]
72: 
73:     if details:
74:         elements.append({
75:             "tag": "div",
76:             "text": {
77:                 "tag": "lark_md",
78:                 "content": f"\n📝 **Details:**\n{details}",
79:             },
80:         })
81: 
82:     elements.append({
83:         "tag": "note",
84:         "elements": [
85:             {
86:                 "tag": "plain_text",
87:                 "content": f"Mode: {mode} | Iterations: {iterations} | Time: {elapsed:.1f}s",
88:             },
89:         ],
90:     })
91: 
92:     return {
93:         "header": {
94:             "title": {"tag": "plain_text", "content": "MiniBot — Result"},
95:             "template": "green",
96:         },
97:         "elements": elements,
98:     }
99: 
100:
101: def task_error_card(error: str, partial_result: str = "") -> dict:
102: """Error notification card."""
103: elements = [
104: {
105: "tag": "div",
106: "text": {
107: "tag": "lark_md",
108: "content": f"❌ Error\n\n{error}",
109: },
110: },
111: ]
112:
113: if partial_result:
114: elements.append({
115: "tag": "div",
116: "text": {
117: "tag": "lark_md",
118: "content": f"\n📋 Partial Result:\n{partial_result}",
119: },
120: })
121:
122: return {
123: "header": {
124: "title": {"tag": "plain_text", "content": "MiniBot — Error"},
125: "template": "red",
126: },
127: "elements": elements,
128: }
