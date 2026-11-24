# Relatório técnico: Painel NEXUS-AI (Command Center)

Arquivo: `docs/dashboard/index.html` · Publicação: GitHub Pages (workflow `pages-build-deployment`)

## 1. Objetivo

Reunir em uma página só os indicadores do projeto: métricas de produção, progresso do roadmap, curvas de treino, comparação de bancos vetoriais, trace de agente, fluxo ao vivo e pipeline de CI. O foco é mostrar de onde cada número vem, separando o que é **medido** do que é **simulado**.

## 2. Arquitetura

- Um único arquivo HTML, sem framework e sem dependência externa. Os gráficos são SVG montados por JavaScript.
- Sete abas: Overview, Knowledge graph, Models, RAG & vector DBs, Agent traces, Live stream e Pipeline.
- Paleta de comandos (`Ctrl+K`), busca de tópicos do roadmap e filtro de período (7, 14 e 30 dias).
- Progresso do grafo de conhecimento salvo no `localStorage` do navegador.
- Respeita `prefers-reduced-motion` e tem foco visível por teclado.

## 3. Fluxo de dados

1. A página abre com dados de demonstração embutidos no próprio arquivo (variável `D`).
2. `refresh()` busca `data/metrics.json` ao abrir e a cada 30 s. Se funcionar, substitui `D` inteiro.
3. Depois, `loadDbs()` busca `data/vectordb.json` e substitui somente `D.dbs`. Por isso o benchmark medido prevalece sobre qualquer valor de `metrics.json`.
4. Se alguma busca falhar, a página continua com os dados que já tinha, sem mostrar erro.
5. O selo no topo indica a origem: `embedded demo data`, `live · updated ...` ou `live · vector DBs medidos`.

O benchmark é gerado em `benchmarks/results/vectordb.json` e copiado para `docs/dashboard/data/`, porque o GitHub Pages só serve arquivos dentro de `docs/`.

## 4. O que é medido e o que é simulado

| Aba | Origem dos dados |
|---|---|
| RAG & vector DBs | **Medido** (`vectordb.json`) |
| Overview (pass rate, latência, custo) | Simulado (`metrics.json` / demonstração) |
| Models (curvas de treino) | Simulado |
| Agent traces | Simulado |
| Live stream | Simulado (configurável via `STREAM_URL`) |
| Pipeline | Animação ilustrativa; não executa o CI de verdade |
| Knowledge graph | Progresso marcado manualmente pelo usuário |

## 5. Benchmark de vector DBs

Condições registradas no arquivo: 500 consultas, k = 10, seed 42, Windows AMD64, Python 3.10.11, execução de 2026-11-23 18:06 UTC, campo `measured: true`.

| Backend | p50 (ms) | p95 (ms) | QPS | Recall@10 | Build (s) |
|---|---|---|---|---|---|
| numpy-exact | 10,128 | 30,866 | 71,3 | 1,0 | 0,7 |
| faiss-flat | 15,762 | 59,564 | 46,7 | 1,0 | 0,02 |

Os demais backends estão no próprio `vectordb.json`.

Leitura dos resultados:

- Os dois backends exatos têm recall 1,0, como esperado para busca exaustiva.
- O `faiss-flat` ficou mais lento que o `numpy-exact` nesta máquina. Isso é o contrário do esperado e não deve ser tratado como conclusão. Hipóteses a verificar: número de threads, tamanho do corpus, dimensão dos vetores, ruído de uma única execução em Windows.
- O painel mostra o tempo de build no lugar do custo, porque o benchmark local não mede custo por consulta.

Para reproduzir: `python benchmarks/vector_db_bench.py` e copiar o JSON gerado para `docs/dashboard/data/vectordb.json`.

## 6. Limitações

- Uma única máquina e uma única execução por backend; sem intervalo de confiança.
- A cópia do `vectordb.json` para `docs/dashboard/data/` é manual. O ideal é o script gravar direto nesse caminho ou o CI fazer a cópia.
- Sem tabela de custo real, o ranking "Which one fits your priority?" usa só latência e recall.
- Várias abas ainda dependem de dados simulados (ver seção 4).

## 7. Próximos passos

- Gerar `metrics.json` a partir de execuções reais (MLflow ou Weights & Biases).
- Alimentar a aba Agent traces com traces reais (LangSmith ou Phoenix).
- Repetir o benchmark várias vezes e mostrar média e desvio.
