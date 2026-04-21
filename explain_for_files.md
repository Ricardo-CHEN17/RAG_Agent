# 项目文件功能说明

本文档详细说明 `agentic_rag` 项目中每个文件需要实现的功能、函数、依赖以及文件间的调用关系。请按此说明进行开发。

---

## 根目录文件

### `.env`
- **用途**：存储环境变量，避免硬编码敏感信息。
- **内容示例**：
OLLAMA_BASE_URL=http://localhost:11434
MYSQL_HOST=localhost
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=agentic_rag
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
CHROMA_PERSIST_DIR=./chroma_data

- **依赖包**：`python-dotenv`（用于加载）
- **被哪些文件读取**：`main.py`、`agent/model_client.py`、`db/mysql_client.py`、`knowledge/embedder.py`、`knowledge/vector_store.py`

---

### `requirements.txt`
- **用途**：列出所有 Python 依赖包，便于一次性安装。
- **内容示例**：
ollama
sentence-transformers
chromadb
mysql-connector-python
python-dotenv
requests
pytest

- **安装命令**：`pip install -r requirements.txt`

---

### `main.py`
- **用途**：命令行入口，实现 REPL（Read-Eval-Print Loop），与用户交互。
- **主要功能**：
- 加载 `.env` 环境变量。
- 初始化日志（`logs/` 目录）。
- 初始化 Agent 控制器（`agent/controller.py` 中的 `AgentController`）。
- 循环读取用户输入，调用 `controller.run(user_input)` 并打印最终答案。
- 处理退出命令（如 `exit`、`quit`、`Ctrl+C`）。
- **需要实现的函数**：
- `setup_logging()`：配置日志格式和输出文件。
- `main()`：主循环。
- **调用的包/模块**：
- `dotenv`：`load_dotenv()`
- `logging`
- `agent.controller.AgentController`
- **被谁调用**：直接运行 `python main.py`。

---

## `agent/` 目录

### `agent/__init__.py`
- **用途**：使 `agent` 成为一个 Python 包。
- **内容**：可以为空，或导出主要类如 `from .controller import AgentController`。

---

### `agent/message.py`
- **用途**：定义核心数据结构 `Message` 和工具相关的类型。
- **需要实现的类/函数**：
- `@dataclass class Message`：
  - 字段：`role: str`、`content: str`、`tool_calls: Optional[List[Dict]]`、`tool_call_id: Optional[str]`、`name: Optional[str]`
  - 方法：`to_dict()`（转换为字典，用于发送给模型 API）
- `@dataclass class ToolCall`（可选）：更严格地表示 `tool_calls` 中的每一项。
- **依赖包**：`dataclasses`、`typing`
- **被谁导入**：`agent/controller.py`、`tools/executor.py`

---

### `agent/model_client.py`
- **用途**：封装对 Ollama API 的调用，发送消息和工具定义，接收响应。
- **需要实现的函数/类**：
- `class OllamaClient`：
  - `__init__(self, base_url: str, model_name: str)`：从环境变量读取 `OLLAMA_BASE_URL` 和模型名（`gemma4:e4b`）。
  - `chat(self, messages: List[Message], tools: List[Dict]) -> Dict`：
    - 将 `messages` 转换为 Ollama API 要求的格式（注意：Ollama 兼容 OpenAI 工具调用格式，请求体需包含 `messages`、`tools`、`model`）。
    - 使用 `requests.post(f"{self.base_url}/api/chat", json=payload)` 发送请求。
    - 处理超时、重试（可选）。
    - 返回解析后的 JSON 响应（包含 `message` 字段，其中可能有 `tool_calls`）。
- **依赖包**：`requests`、`json`、`os`（读取环境变量）
- **被谁调用**：`agent/controller.py`

---

### `agent/controller.py`
- **用途**：实现 Agent 主循环（规划 → 执行 → 观察 → 迭代）。
- **需要实现的类**：
- `class AgentController`：
  - `__init__(self, model_client: OllamaClient, tool_executor: ToolExecutor, max_iterations: int = 10)`：注入依赖。
  - `run(self, user_input: str) -> str`：
    1. 初始化 `messages` 列表，包含一个 `system` 消息（定义角色、行为准则）和用户消息。
    2. 循环 `for _ in range(max_iterations)`：
       - 调用 `model_client.chat(messages, tools_definition)` 得到响应。
       - 如果响应中没有 `tool_calls`，说明任务完成，返回 `response['message']['content']`。
       - 如果有 `tool_calls`：
         - 将 assistant 消息（含 tool_calls）追加到 `messages`。
         - 遍历每个 `tool_call`，调用 `tool_executor.execute(tool_call)` 得到结果字符串。
         - 将结果包装成 `role="tool"` 的 `Message`，追加到 `messages`。
         - 继续循环。
    3. 如果超出迭代次数，返回超时提示。
- **调用的模块**：
- `agent.message.Message`
- `agent.model_client.OllamaClient`
- `tools.executor.ToolExecutor`
- **被谁调用**：`main.py`

---

## `tools/` 目录

### `tools/__init__.py`
- **用途**：包声明，可导出 `ToolExecutor`。

---

### `tools/executor.py`
- **用途**：根据工具名称路由到具体实现函数。
- **需要实现的类/函数**：
- `class ToolExecutor`：
  - `__init__(self, file_tools, rag_tool, mysql_tool)`：注入各工具模块的实例。
  - `execute(self, tool_call: Dict) -> str`：
    - 从 `tool_call` 中提取 `name` 和 `arguments`（JSON 字符串）。
    - 根据 `name` 调用对应的方法（如 `self._list_files(**args)`），捕获异常并返回错误信息。
    - 返回结果字符串（总是字符串，供模型读取）。
- 内部辅助方法：`_list_files(path)`、`_read_file(file_path)`、`_search_knowledge(query, top_k)`、`_mysql_query(sql)` 等，这些方法直接调用传入的工具模块实例。
- **依赖包**：`json`、`logging`
- **被谁调用**：`agent/controller.py`
- **被谁导入**：它导入 `tools.file_tools`、`tools.rag_tool`、`tools.mysql_tool` 中的具体类。

---

### `tools/file_tools.py`
- **用途**：实现文件系统相关的工具（列出目录、读取文件）。
- **需要实现的类**：
- `class FileTools`：
  - `list_files(self, path: str) -> str`：
    - 使用 `os.listdir(path)`，返回格式化的文件列表字符串（每行一个文件）。
    - 处理路径不存在、权限错误等异常，返回错误信息。
  - `read_file(self, file_path: str, max_chars: int = 10000) -> str`：
    - 使用 `open(file_path, 'r', encoding='utf-8')` 读取内容。
    - 如果文件过大，截断并提示。
    - 返回文件内容字符串。
- **依赖包**：`os`、`logging`
- **被谁调用**：`tools/executor.py`

---

### `tools/rag_tool.py`
- **用途**：实现知识库检索工具 `search_knowledge`。
- **需要实现的类**：
- `class RAGTool`：
  - `__init__(self, embedder, vector_store)`：接收 `knowledge/embedder.py` 中的 Embedder 实例和 `knowledge/vector_store.py` 中的 VectorStore 实例。
  - `search_knowledge(self, query: str, top_k: int = 3) -> str`：
    - 调用 `embedder.embed(query)` 获取查询向量。
    - 调用 `vector_store.similarity_search(query_vector, top_k)` 获取最相关的文档片段。
    - 将片段拼接成字符串，每个片段标注来源（文件名、页码等，如果有）。
    - 返回拼接结果；如果没有结果，返回“未找到相关信息”。
- **依赖包**：无额外（使用传入的模块）
- **被谁调用**：`tools/executor.py`
- **注意**：该工具需要提前运行 `knowledge/indexer.py` 建立索引，否则返回空。

---

### `tools/mysql_tool.py`（可选，v1 可先不做）
- **用途**：提供一个工具，让 Agent 能够执行只读 SQL 查询（如查询文档元数据）。
- **需要实现的类**：
- `class MySQLTool`：
  - `__init__(self, mysql_client)`：接收 `db/mysql_client.py` 的客户端实例。
  - `query(self, sql: str) -> str`：
    - 安全检查：禁止 `INSERT`、`UPDATE`、`DELETE`、`DROP` 等写操作（仅允许 `SELECT`）。
    - 执行查询，将结果格式化为表格或 JSON 字符串返回。
- **依赖包**：依赖 `db.mysql_client`
- **被谁调用**：`tools/executor.py`

---

## `knowledge/` 目录

### `knowledge/__init__.py`
- **用途**：包声明。

---

### `knowledge/embedder.py`
- **用途**：加载 Sentence-Transformer 模型，提供文本向量化接口。
- **需要实现的类**：
- `class Embedder`：
  - `__init__(self, model_name: str = "all-MiniLM-L6-v2")`：使用 `sentence_transformers.SentenceTransformer` 加载模型。
  - `embed(self, text: str) -> List[float]`：将单个文本转为向量列表。
  - `embed_batch(self, texts: List[str]) -> List[List[float]]`：批量转换（用于索引文档）。
- **依赖包**：`sentence_transformers`
- **被谁调用**：`knowledge/vector_store.py`（存储时）、`tools/rag_tool.py`（查询时）

---

### `knowledge/vector_store.py`
- **用途**：封装 Chroma 向量数据库，实现添加文档块和相似性检索。
- **需要实现的类**：
- `class VectorStore`：
  - `__init__(self, persist_dir: str, embedder: Embedder)`：
    - 初始化 Chroma 客户端：`chromadb.PersistentClient(path=persist_dir)`
    - 创建或获取 collection（如 `doc_chunks`）。
    - 保存 `embedder` 引用（用于查询时生成向量）。
  - `add_chunks(self, chunks: List[Dict])`：
    - 每个 chunk 应包含 `id`、`text`、`metadata`（如源文件路径、页码）。
    - 调用 `embedder.embed_batch([c['text'] for c in chunks])` 获得向量。
    - 调用 `collection.add(ids=ids, embeddings=embeddings, metadatas=metadatas, documents=texts)`。
  - `similarity_search(self, query: str, top_k: int) -> List[Dict]`：
    - 调用 `embedder.embed(query)` 获取查询向量。
    - 调用 `collection.query(query_embeddings=[query_vector], n_results=top_k)`。
    - 返回结果列表，每个结果包含 `document`、`metadata`、`distance`。
- **依赖包**：`chromadb`
- **被谁调用**：`knowledge/indexer.py`（添加）、`tools/rag_tool.py`（检索）

---

### `knowledge/indexer.py`
- **用途**：扫描本地文档，分块、向量化并存入 Chroma（离线/一次性任务，或定期更新）。
- **需要实现的函数/类**：
- `class Indexer`：
  - `__init__(self, vector_store: VectorStore, chunk_size: int = 500, chunk_overlap: int = 50)`。
  - `index_directory(self, directory_path: str, file_extensions: List[str] = ['.txt', '.md', '.pdf'])`：
    - 遍历目录，对每个支持的文件读取文本（PDF 可能需要额外库，v1 可先只支持 .txt/.md）。
    - 将文本分块（可用简单的按字符数切分，或使用 `langchain.text_splitter` 但避免引入过重依赖，手写递归分割）。
    - 为每个块生成 ID（如 `filepath_chunk_index`）和元数据。
    - 调用 `vector_store.add_chunks(chunks)`。
  - `_read_text_file(file_path)`：读取普通文本文件。
- **依赖包**：`os`、`glob`、`hashlib`（可选，用于生成 ID）
- **被谁调用**：可以单独运行脚本（如 `python -m knowledge.indexer --path ./docs`），或在 `main.py` 启动时检查是否需要更新索引。
- **注意**：索引过程可能较慢，建议单独运行。

---

## `db/` 目录

### `db/__init__.py`
- **用途**：包声明。

---

### `db/mysql_client.py`
- **用途**：封装 MySQL 连接和基本操作（用于存储会话记录、文档元数据等）。
- **需要实现的类**：
- `class MySQLClient`：
  - `__init__(self, host, user, password, database)`：使用 `mysql.connector.connect` 建立连接。
  - `execute_query(self, sql: str, params: tuple = ()) -> List[Dict]`：执行 SELECT 并返回字典列表。
  - `execute_update(self, sql: str, params: tuple = ()) -> int`：执行 INSERT/UPDATE/DELETE，返回受影响行数。
  - `close(self)`：关闭连接。
- **辅助函数**：`get_db_client_from_env()` 从 `.env` 读取配置并返回实例。
- **依赖包**：`mysql.connector`
- **被谁调用**：`tools/mysql_tool.py`（可选）、`main.py`（记录会话）

---

## `logs/` 目录
- **用途**：存放日志文件（由 `logging` 自动生成），不需要在代码中手动创建文件。

---

## `tests/` 目录

### `tests/test_controller.py`
- **用途**：单元测试 `agent/controller.py` 中的 `AgentController`。
- **需要测试的内容**：
- 模拟 `model_client` 返回无 tool_calls 的情况，验证正确返回最终答案。
- 模拟返回 tool_calls，验证 `tool_executor.execute` 被调用且结果被追加到消息列表。
- 测试超过最大迭代次数时返回超时提示。
- **依赖包**：`pytest`、`unittest.mock`

### `tests/test_tools.py`
- **用途**：测试文件工具和 RAG 工具的基本功能。
- **测试点**：
- `FileTools.list_files` 对存在的目录返回正确列表，对不存在的目录返回错误信息。
- `FileTools.read_file` 正常读取，文件过大时截断。
- `RAGTool.search_knowledge` 在空库时返回适当提示，在有数据时返回片段。

### `tests/test_rag.py`
- **用途**：测试 `knowledge/vector_store.py` 和 `knowledge/indexer.py`。
- **测试点**：
- 添加文档块后能正确检索到。
- 索引器能正确分块并生成元数据。

---

## 文件间调用关系总结
main.py
└─> agent.controller.AgentController
├─> agent.model_client.OllamaClient
└─> tools.executor.ToolExecutor
├─> tools.file_tools.FileTools
├─> tools.rag_tool.RAGTool
│ ├─> knowledge.embedder.Embedder
│ └─> knowledge.vector_store.VectorStore
└─> (可选) tools.mysql_tool.MySQLTool
└─> db.mysql_client.MySQLClient


- **数据流向**：用户输入 → `main.py` → `AgentController.run()` → 循环调用 `OllamaClient.chat()` → 解析 tool_calls → `ToolExecutor.execute()` → 工具返回结果 → 继续循环 → 最终答案返回 `main.py` 打印。
- **环境变量**：`.env` 被 `main.py`、`model_client.py`、`mysql_client.py`、`embedder.py`、`vector_store.py` 读取。
- **日志**：所有模块使用 `logging.getLogger(__name__)`，由 `main.py` 统一配置输出到 `logs/`。

---

## 建议开发顺序（覆盖所有文件）

下面顺序按“先基础配置与数据结构，再能力模块，再编排入口，最后测试与文档”的原则安排，确保每一步都能被下一步直接复用。

1. `Plan.md`：先确认范围、验收标准与 v1 边界，避免后续返工。
2. `explain_for_files.md`：作为开发执行清单，先固定接口约定与模块职责。
3. `requirements.txt`：先锁定依赖，保证本地环境可复现。
4. `.env`：准备运行参数（Ollama、MySQL、Embedding、Chroma 路径）。
5. `agent/__init__.py`：建立包结构。
6. `tools/__init__.py`：建立包结构。
7. `knowledge/__init__.py`：建立包结构。
8. `db/__init__.py`：建立包结构。
9. `agent/message.py`：先实现 `Message`/`ToolCall` 数据结构，供后续模型调用与工具回传统一使用。
10. `knowledge/embedder.py`：实现向量化能力。
11. `knowledge/vector_store.py`：实现向量存储与检索（依赖 embedder）。
12. `knowledge/indexer.py`：实现离线建库流程（依赖 vector_store）。
13. `tools/file_tools.py`：实现文件系统工具（低耦合，先完成便于联调）。
14. `tools/rag_tool.py`：实现检索工具（依赖 embedder/vector_store）。
15. `db/mysql_client.py`：实现数据库客户端（v1 可完成基础能力，供可选工具使用）。
16. `tools/mysql_tool.py`：实现只读 SQL 工具（v1 可选，放在后面）。
17. `tools/executor.py`：实现工具路由中心，串联 file/rag/mysql 三类工具。
18. `agent/model_client.py`：实现 Ollama chat + tools 调用封装。
19. `agent/controller.py`：实现 Agent 主循环（调用 model_client + tool_executor）。
20. `main.py`：实现 REPL 入口、日志初始化、依赖装配与运行流程。
21. `tests/test_tools.py`：优先验证文件工具与 RAG 工具。
22. `tests/test_rag.py`：验证向量存储与索引流程。
23. `tests/test_controller.py`：验证主循环、工具调用迭代、超时分支。
24. `logs/`：无需手写文件，运行 `main.py` 后确认日志文件自动生成。

补充建议：
- 每完成一个模块就先写对应测试再进入下一模块，问题定位成本最低。
- 在第 12 步完成后，先用一批 `.md/.txt` 小样本建立索引，再联调第 14、17、19、20 步。

---