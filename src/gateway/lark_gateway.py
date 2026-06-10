 1: """Lark (Feishu) WebSocket gateway.
 2: 
 3: Handles WebSocket connection to Lark for event subscription,
 4: message receiving, and card pushing.
 5: """
 6: 
 7: import asyncio
 8: import hashlib
 9: import hmac
10: import json
11: import logging
12: import time
13: from typing import Callable, Optional
14: 
15: import aiohttp
16: import requests
17: 
18: from src.config import Config
19: from src.gateway.card_templates import (
20:     task_start_card,
21:     task_progress_card,
22:     task_result_card,
23:     task_error_card,
24: )
25: 
26: logger = logging.getLogger(__name__)
27: 
28: 
29: class LarkGateway:
30:     """Lark WebSocket gateway for event subscription and message handling."""
31: 
32:     # Lark API endpoints
33:     EVENT_URL = "https://open.feishu.cn/open-apis/event/v2/"
34:     TENANT_ACCESS_TOKEN_URL = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
35:     SEND_MSG_URL = "https://open.feishu.cn/open-apis/im/v1/messages"
36: 
37:     def __init__(self, config: Config):
38:         self.config = config.lark
39:         self.app_id = config.lark.app_id
40:         self.app_secret = config.lark.app_secret
41:         self._tenant_token: Optional[str] = None
42:         self._token_expires: float = 0
43:         self._message_callback: Optional[Callable] = None
44:         self._running = False
45:         self._ws_session: Optional[aiohttp.ClientSession] = None
46: 
47:     def on_message(self, callback: Callable):
48:         """Register a callback for incoming messages.
49:         
50:         Args:
51:             callback: Function(user_id, message_text) -> None
52:         """
53:         self._message_callback = callback
54:         logger.info("Message callback registered")
55: 
56:     async def start(self):
57:         """Start the WebSocket connection to Lark."""
58:         if not self.app_id or not self.app_secret:
59:             logger.warning("Lark credentials not configured, gateway disabled")
60:             return
61: 
62:         logger.info("Starting Lark gateway...")
63:         self._running = True
64: 
65:         # Get tenant access token
66:         await self._refresh_token()
67: 
68:         # Start WebSocket connection
69:         await self._connect_websocket()
70: 
71:     async def _refresh_token(self):
72:         """Refresh tenant access token."""
73:         try:
74:             response = requests.post(
75:                 self.TENANT_ACCESS_TOKEN_URL,
76:                 json={
77:                     "app_id": self.app_id,
78:                     "app_secret": self.app_secret,
79:                 },
80:                 timeout=10,
81:             )
82:             response.raise_for_status()
83:             data = response.json()
84: 
85:             self._tenant_token = data["tenant_access_token"]
86:             self._token_expires = time.time() + data.get("expire", 7200)
87:             logger.info("Lark tenant token refreshed")
88: 
89:         except Exception as e:
90:             logger.error(f"Failed to refresh Lark token: {e}")
91: 
92:     async def _connect_websocket(self):
93:         """Establish WebSocket connection to Lark event subscription."""
94:         url = f"{self.EVENT_URL}sub?app_id={self.app_id}"
95: 
96:         # Calculate WebSocket signature
97:         timestamp = str(int(time.time()))
98:         sign_str = f"{timestamp}\n{self.app_secret}"
99:         sign = hashlib.sha256(sign_str.encode()).hexdigest()
100:
101: ws_url = f"{url}&timestamp={timestamp}&sign={sign}"
102:
103: try:
104: async with aiohttp.ClientSession() as session:
105: self._ws_session = session
106: async with session.ws_connect(ws_url) as ws:
107: logger.info("Lark WebSocket connected")
108:
109: async for msg in ws:
110: if msg.type == aiohttp.WSMsgType.TEXT:
111: await self._handle_ws_message(msg.data)
112: elif msg.type == aiohttp.WSMsgType.ERROR:
113: logger.error("Lark WebSocket error")
114: break
115:
116: except Exception as e:
117: logger.error(f"Lark WebSocket connection failed: {e}")
118:
119: if self._running:
120: logger.info("Reconnecting in 5s...")
121: await asyncio.sleep(5)
122: await self._connect_websocket()
123:
124: async def _handle_ws_message(self, data: str):
125: """Handle incoming WebSocket message."""
126: try:
127: event = json.loads(data)
128:
129: # Handle challenge (connection verification)
130: if event.get("challenge"):
131: logger.info("Lark challenge received, responding")
132: return
133:
134: # Handle token refresh
135: if event.get("subscribe_to_resource") == "v1.im.message.receive":
136: logger.info("Event subscription confirmed")
137: return
138:
139: # Handle message events
140: header = event.get("header", {})
141: event_type = header.get("event_type", "")
142:
143: if event_type == "message.receive_v1":
144: await self._handle_message_event(event)
145:
146: except json.JSONDecodeError:
147: logger.warning(f"Invalid JSON from Lark: {data[:100]}")
148: except Exception as e:
149: logger.error(f"Error handling Lark message: {e}")
150:
151: async def _handle_message_event(self, event: dict):
152: """Process incoming message event."""
153: try:
154: event_data = event.get("event", {})
155: message = event_data.get("message", {})
156: sender = event_data.get("sender", {})
157:
158: message_type = message.get("message_type", "")
159: if message_type != "text":
160: logger.debug(f"Non-text message type: {message_type}")
161: return
162:
163: content = json.loads(message.get("content", "{}"))
164: text = content.get("text", "")
165:
166: sender_id = sender.get("sender_id", {}).get("open_id", "")
167: chat_id = message.get("chat_id", "")
168:
169: logger.info(f"Message from {sender_id}: {text[:100]}")
170:
171: # Send to callback
172: if self._message_callback:
173: # Run callback in executor to avoid blocking
174: loop = asyncio.get_event_loop()
175: await loop.run_in_executor(
176: None,
177: self._message_callback,
178: sender_id,
179: text,
180: )
181:
182: except Exception as e:
183: logger.error(f"Error processing message event: {e}")
184:
185: async def send_card(self, user_id: str, card: dict):
186: """Send a message card to a user."""
187: if not self._tenant_token:
188: logger.warning("No tenant token, cannot send card")
189: return
190:
191: # Create a single chat with the user and send card
192: card_json = json.dumps({"card": card})
193:
194: url = f"{self.SEND_MSG_URL}?receive_id_type=open_id"
195: headers = {
196: "Authorization": f"Bearer {self._tenant_token}",
197: "Content-Type": "application/json; charset=utf-8",
198: }
199: payload = {
200: "receive_id": user_id,
201: "msg_type": "interactive",
202: "content": card_json,
203: }
204:
205: try:
206: response = requests.post(url, json=payload, headers=headers, timeout=10)
207: response.raise_for_status()
208: logger.info(f"Card sent to {user_id}")
209: except Exception as e:
210: logger.error(f"Failed to send card: {e}")
211:
212: async def send_task_start(self, user_id: str, goal: str, plan: str = ""):
213: """Send task start card."""
214: card = task_start_card(goal, plan)
215: await self.send_card(user_id, card)
216:
217: async def send_task_progress(self, user_id: str, step: int,
218: total: int, detail: str):
219: """Send task progress card."""
220: card = task_progress_card(step, total, detail)
221: await self.send_card(user_id, card)
222:
223: async def send_task_result(self, user_id: str, summary: str,
224: details: str = "", mode: str = "react",
225: iterations: int = 0, elapsed: float = 0):
226: """Send task result card."""
227: card = task_result_card(summary, details, mode, iterations, elapsed)
228: await self.send_card(user_id, card)
229:
230: async def send_task_error(self, user_id: str, error: str,
231: partial_result: str = ""):
232: """Send task error card."""
233: card = task_error_card(error, partial_result)
234: await self.send_card(user_id, card)
235:
236: def stop(self):
237: """Stop the gateway."""
238: self._running = False
239: logger.info("Lark gateway stopping")
