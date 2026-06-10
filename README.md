# miniAgent

完整文件清单
根目录
文件	行数	说明
main.py	189 行	入口，组装所有模块，启动 gateway
config.yaml	59 行	配置文件（Lark/模型/记忆/Agent/工具/Skill/日志）
.env.example	22 行	环境变量模板（API Key 占位）
.gitignore	9 行	忽略 .env、数据库、日志、缓存
requirements.txt	7 行	依赖包列表
src/ 源码
文件	行数	说明
src/config.py	190 行	配置加载器，YAML → dataclass，${VAR} 解析
src/utils/env.py	42 行	.env 加载 + ${VAR} 占位符递归替换
src/gateway/lark_gateway.py	239 行	飞书 WebSocket 网关，消息接收 + 卡片推送
src/gateway/card_templates.py	121 行	4 种消息卡片模板（开始/进度/结果/错误）
src/agent/core.py	192 行	Agent 核心，模式选择 + 记忆检索 + 技能匹配
src/agent/react.py	209 行	ReAct 推理引擎，JSON 响应解析 + ToT 关键词检测
src/agent/reflection.py	80 行	反思批判引擎，VERDICT 解析
src/agent/tot.py	180 行	Tree of Thoughts，3 分支 × 3 层探索
src/memory/sqlite_store.py	217 行	SQLite 存储，向量序列化 + cosine similarity
src/memory/manager.py	137 行	记忆管理器，3 类记忆 + 搜索 + 衰减 + 归档
src/models/base_provider.py	46 行	模型 Provider 抽象基类
src/models/router.py	115 行	模型路由器，多 provider fallback
src/models/openai_provider.py	45 行	OpenAI 兼容 provider（chat + embed）
src/models/gemini_provider.py	69 行	Google Gemini provider
src/models/nvidia_provider.py	46 行	NVIDIA NIM provider（仅 embed）
src/tools/base_tool.py	39 行	工具抽象基类 + ToolResult
src/tools/registry.py	77 行	工具注册中心，6 个内置工具
src/tools/shell.py	97 行	Shell 执行，黑名单 + 超时 + 截断
src/tools/search.py	141 行	搜索工具（Tavily/SearXNG/Google）
src/tools/file_ops.py	171 行	文件读写编辑，工作目录沙箱
src/tools/browser.py	72 行	网页抓取（curl + HTML 转文本）
src/skills/loader.py	88 行	YAML skill 加载器
src/skills/registry.py	90 行	Skill 注册中心，触发词匹配
示例 Skill
文件	行数	说明
skills/check_system.yaml	19 行	示例 skill：系统状态检查
