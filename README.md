<div align="center">

# 🧬 NEXUS·AI

**Laboratório de pesquisa em engenharia de IA: dos fundamentos matemáticos a sistemas em produção, com um centro de comando interativo.**

[![CI](https://github.com/kallymeire/NEXUS.IA/actions/workflows/ci.yml/badge.svg)](https://github.com/kallymeire/NEXUS.IA/actions)
![Python](https://img.shields.io/badge/python-3.10%2B-8b5cf6)
![Licença](https://img.shields.io/badge/licença-MIT-22d3ee)
![Dashboard](https://img.shields.io/badge/dashboard-HTML_puro-3ef2b0)

[**▶ Ver o painel ao vivo**](https://kallymeire.github.io/NEXUS.IA/) · [Como funciona](#-como-funciona) · [Começar](#-começar-em-1-minuto) · [Roadmap](#-roadmap)

<a href="https://kallymeire.github.io/NEXUS.IA/">
  <img src="docs/demo.gif" alt="Painel NEXUS·AI em execução: grafo de conhecimento, Training Lab, RAG, agent trace, embeddings 3D e Live Ops" width="900">
</a>

</div>

---

## 💡 Por que isto existe

Estudar IA costuma virar uma pilha de notebooks soltos. Fica difícil responder: *o que eu já cobri? como um tópico depende de outro? o experimento é reproduzível?*

O NEXUS·AI organiza **58 tópicos em 7 módulos** (fundamentos, ML/DL, aplicações com LLMs, LLMOps, avançado, ferramentas e portfólio) e trata cada um como um experimento:

- **hipótese → implementação → testes → protocolo de avaliação → métricas**
- seeds controlados, ablação e teste de significância quando aplicável
- tudo visível em um painel que você abre no navegador, sem instalar nada

O resultado é um mapa navegável do que foi estudado, medido e publicado.

## 🖥️ O painel

Um centro de comando em HTML puro (sem build, sem framework) com nove laboratórios interativos.

| | |
|---|---|
| **Overview** | Cards de KPI que giram, com sparkline ao vivo. Universo de 30 dias de LLMOps em bolhas (timeline, radial, dispersão). Mapa orbital do protocolo de pesquisa por módulo. |
| **Knowledge Graph** | 58 tópicos, 7 módulos e dependências. Arraste, passe o mouse e clique para ver relações e marcar etapas do protocolo. |
| **Training Lab** | MLP, CNN e Transformer com learning rate e seed ajustáveis. Curvas de loss e acurácia, ablação com 5 seeds (média ± desvio) e teste de Welch. |
| **RAG Lab** | Benchmark de Vector DBs (Qdrant, Chroma, Pinecone, Weaviate) na fronteira de Pareto recall × latência. Busca híbrida com fusão BM25 + densa. |
| **Agents & Security** | Waterfall de spans de um agente, com replay. Ative o ataque de prompt injection e veja o guardrail bloquear. Evals com IC 95%. |
| **Embedding Space** | 420 chunks em 3D. Gire, dê zoom, clique em um ponto para rodar k-NN e ver a precisão da vizinhança. |
| **Live Ops** | Produção simulada em tempo real: injete falhas nos estágios, gere pico de tráfego e acompanhe p95 contra o SLO com autoscaling. |
| **Attention Lab** | Matriz de atenção por cabeça (prev token, self, lexical, causal) com temperatura ajustável. |
| **Architecture** | Pipeline de dados e automação e a estrutura proposta do repositório. |

**Paleta de comandos** com `Ctrl/⌘ + K` para saltar entre laboratórios, reproduzir o agent trace ou injetar um ataque. Tema claro e escuro, e funciona no celular.

## ⚙️ Como funciona

```mermaid
flowchart LR
    A[experimentos<br/>MLflow · W&B] --> B[scripts/generate_metrics.py]
    B --> C[metrics.json<br/>versionado]
    C --> D[API FastAPI<br/>/metrics /health]
    C --> E[🖥️ painel<br/>GitHub Pages]
    D --> E
    F[GitHub Actions] -->|testes + métricas| B
```

### Protocolo de pesquisa

Cada módulo segue a mesma metodologia:

```text
HIPÓTESE → IMPLEMENTAÇÃO → EXPERIMENTOS COM SEED → AVALIAÇÃO
        → ABLAÇÃO → SIGNIFICÂNCIA ESTATÍSTICA → RELATÓRIO TÉCNICO
```

### Módulos

| Módulo | Foco |
|---|---|
| 🧮 Foundations | Python, álgebra linear, probabilidade, cálculo, estruturas de dados, Git, APIs, SQL, Docker |
| 🧠 ML & Deep Learning | Scikit-learn, redes neurais, PyTorch, Transformers, backpropagation, Hugging Face |
| 🤖 LLM Applications | Prompt e context engineering, embeddings, RAG, tool calling, agentes, vector DBs, LangChain/LangGraph, LlamaIndex |
| ⚙️ Production & LLMOps | Evals, monitoramento, custo e latência, FastAPI, CI/CD para IA, guardrails, tracing |
| 🚀 Advanced | LoRA/QLoRA, modelos open source, vLLM, multimodal, multiagente, segurança de IA |
| 🛠️ Core Tools | Toolchain Python, stack PyTorch, ecossistema HF, LangSmith/Phoenix, MLflow/W&B |
| 🧪 Portfolio | Structured Output Parser, Production RAG App, Tool-using Agent, sistema com deploy |

## 🚀 Começar em 1 minuto

```bash
git clone https://github.com/kallymeire/NEXUS.IA.git
cd NEXUS.IA

python -m http.server 8080 -d docs
```

Abra `http://localhost:8080` e navegue pelo painel. Não há build nem dependências.

Outras formas de rodar:

```bash
# métricas do painel secundário
python scripts/generate_metrics.py
python -m http.server 8081 -d docs/dashboard

# API + painel
docker compose up --build
```

| Serviço | Endereço |
|---|---|
| Painel | `http://localhost:8080` |
| API | `http://localhost:8000` |

### Publicando o seu progresso real

No `docs/index.html`, a constante `DONE` define o que está concluído. Edite e publique:

```js
const DONE = { 'rag': ['Hipótese', 'Implementação'] };
```

As etapas válidas são `Hipótese`, `Implementação`, `Testes`, `Eval protocol` e `Métricas`. O anel de progresso do Overview, o grafo e o card **Protocolo concluído** passam a refletir esse valor.

## 🗂️ Estrutura

```
NEXUS.IA/
├── src/nexus/
│   ├── foundations/ ml_dl/ llm_apps/
│   └── llmops/ advanced/ tools/ portfolio/
├── docs/                    # painel (publicado via GitHub Pages)
│   ├── index.html           # painel principal
│   ├── demo.gif · dashboard.png
│   ├── .nojekyll
│   └── dashboard/           # painel secundário
│       ├── index.html
│       └── data/metrics.json
├── scripts/generate_metrics.py
├── .github/workflows/ci.yml # CI: métricas, testes e artefato do painel
└── docker-compose.yml
```

## 🧭 Roadmap

- [x] Painel interativo com nove laboratórios e paleta de comandos
- [x] Grafo de conhecimento com 58 tópicos e dependências
- [x] Training Lab com seeds, ablação e teste de Welch
- [x] RAG Lab com fronteira de Pareto e busca híbrida
- [x] Agent trace com simulação de prompt injection e evals com IC 95%
- [x] Embedding Space 3D, Live Ops e Attention Lab
- [x] CI com geração de métricas e testes
- [x] Card de avaliação real do AgentFlow (13 casos, agente + palavras-chave + juiz por significado)
- [x] Trocar os dados simulados por execuções reais (MLflow / W&B)
- [ ] Traces reais de agentes via LangSmith / Phoenix
- [x] Benchmark de Vector DBs medido, não modelado
- [ ] Relatórios técnicos por módulo (`research/reports/`)
- [x] Comentário automático no Pull Request com as métricas

## ⚠️ Limitações

- **A maior parte dos números do painel é simulada** (dados sintéticos com seed fixo): treino, RAG, latência, custo e os evals de segurança. A exceção é o card **Avaliação real · AgentFlow**, na aba Agents & Security, que mostra o resultado real do `avaliar.py` do [AgentFlow](https://github.com/kallymeire/agentflow), com 13 casos.
- O **retriever híbrido** é um modelo de brinquedo, feito para ilustrar a fusão lexical + densa.
- O **Embedding Space** é uma projeção sintética, não vem de um modelo de embeddings real.
- O progresso por tópico reflete só o que está marcado em `DONE` no `docs/index.html`; o restante aparece como 0%.
- A pilha tecnológica (LangChain, LangGraph, Qdrant, MLflow etc.) descreve o alvo de estudo, e nem todas as peças já têm implementação no repositório.

## 👩‍💻 Autora

**Kallymeire Coelho** · [GitHub](https://github.com/kallymeire)

## 📄 Licença

MIT. Veja [LICENSE](LICENSE).
