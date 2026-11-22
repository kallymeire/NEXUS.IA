# NEXUS-AI

**The Complete AI Engineering Research Platform: From Mathematical Foundations to Production LLMOps**

Reproducible research platform covering the entire AI engineering stack: math foundations, classical ML and deep learning, LLM applications (RAG, agents, tool calling), LLMOps, fine-tuning, multi-agent systems and AI security, with interactive dashboards and automated pipelines.

## Modules (`src/nexus/`)

| Folder | Section |
|---|---|
| `foundations` | Python (async, testing), Linear Algebra, Probability & Statistics, Calculus, DSA, Git, APIs & REST, SQL, Docker |
| `ml_dl` | Scikit-learn, Neural Networks, PyTorch, Transformers & Attention, Backpropagation, Evaluation & Metrics, Karpathy Zero to Hero, Hugging Face |
| `llm_apps` | Prompt & Context Engineering, Structured Outputs, Embeddings, RAG, Tool Calling, Agents, Vector DBs (Qdrant, Chroma, Pinecone, Weaviate), LangChain/LangGraph, LlamaIndex, HF Agents |
| `llmops` | Evals, Monitoring, Cost & Latency, FastAPI, Docker, Cloud, CI/CD for AI, Guardrails, Logging & Tracing, Experiment Tracking |
| `advanced` | LoRA/QLoRA, Open Source Models, vLLM, Multimodal AI, Multi-Agent Systems, AI System Design, AI Security, Model Serving |
| `tools` | Python, PyTorch, Hugging Face, FastAPI, Docker, LangSmith/Phoenix, MLflow/W&B, Cloud Platforms |
| `portfolio` | Structured Output Parser, Production RAG App (with Evals), Tool-using Agent, Deployed AI System, Specialized Project |

## Dashboard

`docs/dashboard/index.html` is a dependency-free interactive dashboard (roadmap tracker, training curves, vector DB benchmark, LLMOps metrics, agent traces). It reads `docs/dashboard/data/metrics.json` and falls back to embedded demo data.

```bash
python scripts/generate_metrics.py      # refresh metrics (demo data; connect MLflow / W&B / LangSmith here)
python -m http.server -d docs/dashboard 8080
```

Publish it with GitHub Pages (Settings > Pages > deploy from `docs/dashboard`).

Dashboard views: Overview, Knowledge graph, Models, RAG & vector DBs, Agent traces, Live stream, Pipeline. Press `Ctrl+K` for the command palette. It re-reads `data/metrics.json` every 30 s, and `STREAM_URL` in the script connects the Live stream to your API.

## Automation

GitHub Actions (`.github/workflows/ci.yml`) regenerates metrics, runs tests and uploads the dashboard on every push.

## Run with Docker

```bash
docker compose up --build   # API on :8000, dashboard on :8080
```

## Scientific rigor

Each module documents a hypothesis, methodology, seeded runs, ablations, significance tests and a short technical report.
