# Benchmark de Vector DBs (medido)

_Gerado automaticamente por `benchmarks/vector_db_bench.py` em 2026-11-23 18:06 UTC._

## Setup
- Vetores: **50,000** · dimensão: **128** · consultas: **500** · k = 10
- Dados sintéticos gaussianos normalizados (seed 42), recall medido contra busca exata em NumPy
- Máquina: Windows AMD64 · Python 3.10.11

## Resultados

| Backend | Build (s) | p50 (ms) | p95 (ms) | QPS | Recall@10 |
|---|---:|---:|---:|---:|---:|
| numpy-exact | 0.7 | 10.128 | 30.866 | 71.3 | 1.0 |
| faiss-flat | 0.02 | 15.762 | 59.564 | 46.7 | 1.0 |
| faiss-hnsw | 111.06 | 2.304 | 3.141 | 380.5 | 0.6098 |
| chroma | 59.49 | 4.38 | 5.914 | 217.0 | 0.4302 |
| qdrant-local | 18.34 | 88.877 | 236.6 | 8.6 | 1.0 |

## Limitações
- Dados sintéticos: o recall em embeddings reais (texto) costuma diferir.
- Consultas sequenciais, uma por vez; não mede concorrência nem filtros por metadados.
- Chroma e Qdrant rodam em modo local/em memória, não em modo servidor.
- Resultados dependem da máquina; repita no seu ambiente antes de comparar.

## Como reproduzir
```bash
pip install numpy faiss-cpu chromadb qdrant-client
python benchmarks/vector_db_bench.py --n 50000 --dim 128 --queries 500
```
