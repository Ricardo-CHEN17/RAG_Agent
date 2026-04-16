# Local Agentic RAG CLI with Gemma 4 E4B – Project One-Pager

## 1. Core Value (One sentence)

Enable users to ask complex, multi-step information gathering tasks (e.g., “compare budget data from two reports and find relevant trends”) using natural language, while a local AI agent autonomously plans, calls tools (file system, RAG knowledge base), and returns integrated answers – all offline with full privacy.

## 2. Out of Scope (Version 1 Boundaries)

| Area | Explicitly excluded in v1 |
|------|----------------------------|
| **Frontend** | No GUI (web UI or desktop app). Command-line interface only (input/print). *(Web UI will be added in v2)* |
| **Network search** | No web search tool. All information comes from local files and the RAG knowledge base. |
| **Multimodal input** | No image, audio, or video input. Text only. *(Multimodal will be added in v3)* |
| **Persistent memory** | No cross-session memory. Each run is a fresh conversation. |
| **Auto-installation** | No one-click installer. User manually sets up Python, Ollama, and the model. |
| **Multi-user / concurrency** | Single process, single session only. |
| **Production-grade reliability** | No load balancing, failover, or monitoring – a functional prototype / personal tool. |

## 3. Success Criteria (Quantifiable)

| Category | Metric | Target |
|----------|--------|--------|
| **Functionality** | Number of supported tools | ≥2 (file system, RAG knowledge base) |
| **Agent correctness** | Tool call parsing success rate | ≥95% (model outputs valid JSON that can be executed) |
| **Task completion rate** | Agent autonomously completes 10 typical complex tasks (e.g., “summarise key points from all PDFs in a folder”) | ≥80% (no human intervention or extra prompting) |
| **Performance** | Single agent cycle (model inference + one tool execution) | ≤15 seconds on consumer GPU (e.g., RTX 3060 12G) |
| **Code quality** | Unit test coverage (core modules: tool parsing, agent loop) | ≥85% |
| **Documentation** | README includes: install steps, run command, tool configuration, examples | 100% |

## 4. Key Constraints

- **Model**: Gemma 4 E4B served via Ollama (must support native function calling / tool use).
- **Environment**: x86_64 Linux / Windows WSL2 / macOS (Apple Silicon); ≥16GB RAM; GPU optional but recommended.
- **Vector search**: Lightweight in‑memory or embedded vector DB (e.g., Chroma embedded mode) – no separate service.
- **No external API dependencies**: Everything (LLM, embedding, retrieval) runs locally.

## 5. Next Steps (Actionable Tasks)

1. **Environment setup** – Pull Gemma 4 E4B with Ollama, verify tool calling API works.
2. **Implement tools** – `list_files`, `read_file`, `search_knowledge` (RAG over local documents).
3. **Agent loop** – Parse model output → execute tool → feed results back → iterate until final answer.
4. **CLI interaction** – Simple REPL (Read‑Eval‑Print Loop).
5. **Testing & measurement** – Write unit tests, run the 10 benchmark tasks, measure success rate and latency.

---

*Version 1 delivers a functional command‑line agent with file system + RAG tools. Web UI follows in v2, multimodal input in v3.*