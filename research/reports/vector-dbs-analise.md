# Vector DBs: análise dos resultados medidos

Esta análise interpreta a execução de 2026-11-23 registrada em [`vector-dbs.md`](vector-dbs.md): 50.000 vetores, dimensão 128, 500 consultas, k = 10, dados sintéticos gaussianos normalizados (seed 42), Windows AMD64, Python 3.10.11. Os números abaixo vêm dessa única execução, e as explicações marcadas como "hipótese" não foram testadas.

## Resultados em uma tabela

| Backend | Build (s) | p50 (ms) | p95 (ms) | QPS | Recall@10 |
|---|---:|---:|---:|---:|---:|
| numpy-exact | 0,7 | 10,13 | 30,87 | 71,3 | 1,00 |
| faiss-flat | 0,02 | 15,76 | 59,56 | 46,7 | 1,00 |
| faiss-hnsw | 111,06 | 2,30 | 3,14 | 380,5 | 0,61 |
| chroma | 59,49 | 4,38 | 5,91 | 217,0 | 0,43 |
| qdrant-local | 18,34 | 88,88 | 236,60 | 8,6 | 1,00 |

## O que os números mostram

1. **Velocidade contra precisão é o eixo principal.** Os dois índices aproximados (FAISS HNSW e Chroma) respondem de 2 a 4 vezes mais rápido que a busca exata em NumPy, mas perdem recall: 0,61 e 0,43. Os três backends com recall 1,00 (NumPy, FAISS Flat e Qdrant local) fazem busca exata.
2. **FAISS HNSW foi o mais rápido nas consultas** (p50 de 2,3 ms e p95 de 3,1 ms, com cauda muito curta), mas o mais caro para construir: 111 s contra 0,02 s do índice Flat. Compensa quando o índice é construído uma vez e consultado muitas vezes.
3. **O Qdrant local foi o mais lento** (8,6 QPS) com recall perfeito. No modo local em memória, o Qdrant avisa que não é recomendado acima de 20 mil pontos, e o resultado é coerente com isso. Este número não representa o Qdrant em modo servidor com índice HNSW.
4. **O FAISS Flat perdeu para o NumPy** (15,8 ms contra 10,1 ms de p50). Hipótese: com uma consulta por vez, o custo de chamada e de paralelismo do FAISS pesa mais que o ganho. Não foi isolado aqui.
5. **A cauda (p95) importa tanto quanto a mediana.** Em NumPy, FAISS Flat e Qdrant, o p95 é de 3 a 4 vezes o p50. Isso pode refletir ruído da máquina durante a execução, então vale repetir antes de tirar conclusões finas.

## Por que o recall do HNSW e do Chroma ficou baixo

Recall de 0,61 (FAISS HNSW) e 0,43 (Chroma) é baixo para este tipo de índice. Hipóteses, nenhuma testada:

- **Dados gaussianos sem estrutura** são um caso difícil para índices baseados em grafo. Embeddings reais de texto têm agrupamentos, e o recall costuma ser maior.
- **Parâmetros de busca conservadores.** O FAISS HNSW foi rodado com `efSearch = 64`, e o Chroma com seus padrões. Aumentar o `efSearch` normalmente sobe o recall e o custo por consulta.

Portanto, estes números não dizem que o HNSW é ruim. Dizem que, com estes parâmetros e estes dados, ele troca precisão por velocidade.

## Limitações

- Dados sintéticos, uma única execução e uma única máquina.
- Consultas sequenciais; não há medição de concorrência, filtros por metadados nem atualização do índice.
- Chroma e Qdrant em modo local/em memória, não em modo servidor.
- Os parâmetros dos índices não foram variados.

## Próximos passos

1. **Varrer o `efSearch`** do FAISS HNSW (por exemplo 16, 64, 128, 256) e plotar recall contra latência. É o gráfico mais informativo para este benchmark.
2. **Repetir com embeddings reais** (um corpus de texto pequeno e um modelo de embeddings aberto) e comparar o recall com o sintético.
3. **Rodar o Qdrant em modo servidor** (Docker) para uma comparação justa com os outros.
4. Repetir cada configuração algumas vezes e reportar a média e o desvio.
