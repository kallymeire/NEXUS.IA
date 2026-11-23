#!/usr/bin/env python3
"""
Benchmark MEDIDO de bancos vetoriais para o NEXUS.IA.

Mede, em dados sintéticos reproduzíveis (seed fixa):
  - tempo de build do índice
  - latência por consulta (p50 / p95)
  - QPS
  - recall@10 contra busca exata (brute-force NumPy)

Backends (cada um é opcional; os que não estiverem instalados são pulados):
  - numpy-exact   (referência, sempre roda)
  - faiss-flat    (pip install faiss-cpu)
  - faiss-hnsw    (pip install faiss-cpu)
  - chroma        (pip install chromadb)
  - qdrant-local  (pip install qdrant-client)

Uso:
  python benchmarks/vector_db_bench.py --n 50000 --dim 128 --queries 500
Saídas:
  benchmarks/results/vectordb.json
  research/reports/vector-dbs.md   (relatório gerado SOMENTE com números medidos)
"""
import argparse
import json
import platform
import statistics
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np

K = 10


def make_data(n, dim, n_queries, seed):
    rng = np.random.default_rng(seed)
    base = rng.standard_normal((n, dim)).astype("float32")
    queries = rng.standard_normal((n_queries, dim)).astype("float32")
    # normaliza: distância euclidiana ~ ordenação por cosseno
    base /= np.linalg.norm(base, axis=1, keepdims=True)
    queries /= np.linalg.norm(queries, axis=1, keepdims=True)
    return base, queries


def exact_topk(base, queries, k):
    sims = queries @ base.T
    idx = np.argpartition(-sims, k, axis=1)[:, :k]
    order = np.argsort(-np.take_along_axis(sims, idx, axis=1), axis=1)
    return np.take_along_axis(idx, order, axis=1)


def recall(found, truth):
    hits = sum(len(set(f) & set(t)) for f, t in zip(found, truth))
    return hits / (truth.shape[0] * truth.shape[1])


def timed_queries(search_fn, queries):
    lat = []
    results = []
    for q in queries:
        t0 = time.perf_counter()
        results.append(search_fn(q))
        lat.append((time.perf_counter() - t0) * 1000)
    lat_sorted = sorted(lat)
    p95 = lat_sorted[int(0.95 * (len(lat_sorted) - 1))]
    total_s = sum(lat) / 1000
    return {
        "p50_ms": round(statistics.median(lat), 3),
        "p95_ms": round(p95, 3),
        "qps": round(len(queries) / total_s, 1),
    }, np.array(results)


# ---------- backends ----------
def bench_numpy(base, queries, truth):
    t0 = time.perf_counter()
    mat = base.copy()
    build = time.perf_counter() - t0

    def search(q):
        s = mat @ q
        idx = np.argpartition(-s, K)[:K]
        return idx[np.argsort(-s[idx])]

    stats, res = timed_queries(search, queries)
    return build, stats, res


def bench_faiss(base, queries, truth, kind):
    import faiss

    dim = base.shape[1]
    t0 = time.perf_counter()
    if kind == "flat":
        index = faiss.IndexFlatIP(dim)
    else:
        index = faiss.IndexHNSWFlat(dim, 32, faiss.METRIC_INNER_PRODUCT)
        index.hnsw.efConstruction = 200
        index.hnsw.efSearch = 64
    index.add(base)
    build = time.perf_counter() - t0

    def search(q):
        _, ids = index.search(q.reshape(1, -1), K)
        return ids[0]

    stats, res = timed_queries(search, queries)
    return build, stats, res


def bench_chroma(base, queries, truth):
    import chromadb

    client = chromadb.EphemeralClient()
    col = client.create_collection(
        "bench", metadata={"hnsw:space": "cosine"}
    )
    ids = [str(i) for i in range(len(base))]
    t0 = time.perf_counter()
    step = 5000
    for i in range(0, len(base), step):
        col.add(ids=ids[i:i + step], embeddings=base[i:i + step].tolist())
    build = time.perf_counter() - t0

    def search(q):
        r = col.query(query_embeddings=[q.tolist()], n_results=K)
        return np.array([int(x) for x in r["ids"][0]])

    stats, res = timed_queries(search, queries)
    return build, stats, res


def bench_qdrant(base, queries, truth):
    from qdrant_client import QdrantClient, models

    client = QdrantClient(":memory:")
    client.create_collection(
        "bench",
        vectors_config=models.VectorParams(
            size=base.shape[1], distance=models.Distance.COSINE
        ),
    )
    t0 = time.perf_counter()
    step = 5000
    for i in range(0, len(base), step):
        chunk = base[i:i + step]
        client.upload_collection(
            "bench",
            vectors=chunk,
            ids=list(range(i, i + len(chunk))),
        )
    build = time.perf_counter() - t0

    def search(q):
        hits = client.query_points("bench", query=q.tolist(), limit=K).points
        return np.array([h.id for h in hits])

    stats, res = timed_queries(search, queries)
    return build, stats, res


BACKENDS = {
    "numpy-exact": lambda b, q, t: bench_numpy(b, q, t),
    "faiss-flat": lambda b, q, t: bench_faiss(b, q, t, "flat"),
    "faiss-hnsw": lambda b, q, t: bench_faiss(b, q, t, "hnsw"),
    "chroma": bench_chroma,
    "qdrant-local": bench_qdrant,
}


def write_report(payload, path):
    meta = payload["meta"]
    lines = [
        "# Benchmark de Vector DBs (medido)",
        "",
        f"_Gerado automaticamente por `benchmarks/vector_db_bench.py` em {meta['timestamp']}._",
        "",
        "## Setup",
        f"- Vetores: **{meta['n']:,}** · dimensão: **{meta['dim']}** · consultas: **{meta['queries']}** · k = {K}",
        f"- Dados sintéticos gaussianos normalizados (seed {meta['seed']}), recall medido contra busca exata em NumPy",
        f"- Máquina: {meta['machine']} · Python {meta['python']}",
        "",
        "## Resultados",
        "",
        "| Backend | Build (s) | p50 (ms) | p95 (ms) | QPS | Recall@10 |",
        "|---|---:|---:|---:|---:|---:|",
    ]
    for r in payload["results"]:
        lines.append(
            f"| {r['backend']} | {r['build_s']} | {r['p50_ms']} | {r['p95_ms']} | {r['qps']} | {r['recall_at_10']} |"
        )
    if payload["skipped"]:
        lines += ["", "Backends pulados (não instalados ou com erro): "
                  + ", ".join(f"`{s}`" for s in payload["skipped"])]
    lines += [
        "",
        "## Limitações",
        "- Dados sintéticos: o recall em embeddings reais (texto) costuma diferir.",
        "- Consultas sequenciais, uma por vez; não mede concorrência nem filtros por metadados.",
        "- Chroma e Qdrant rodam em modo local/em memória, não em modo servidor.",
        "- Resultados dependem da máquina; repita no seu ambiente antes de comparar.",
        "",
        "## Como reproduzir",
        "```bash",
        "pip install numpy faiss-cpu chromadb qdrant-client",
        f"python benchmarks/vector_db_bench.py --n {meta['n']} --dim {meta['dim']} --queries {meta['queries']}",
        "```",
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=50000)
    ap.add_argument("--dim", type=int, default=128)
    ap.add_argument("--queries", type=int, default=500)
    ap.add_argument("--seed", type=int, default=42)
    ap.add_argument("--json-out", default="benchmarks/results/vectordb.json")
    ap.add_argument("--report-out", default="research/reports/vector-dbs.md")
    args = ap.parse_args()

    base, queries = make_data(args.n, args.dim, args.queries, args.seed)
    print("Calculando verdade exata...")
    truth = exact_topk(base, queries, K)

    results, skipped = [], []
    for name, fn in BACKENDS.items():
        try:
            print(f"-> {name}")
            build, stats, found = fn(base, queries, truth)
            results.append({
                "backend": name,
                "build_s": round(build, 2),
                **stats,
                "recall_at_10": round(recall(found, truth), 4),
            })
        except ImportError:
            skipped.append(name)
            print(f"   pulado (dependência ausente)")
        except Exception as e:  # noqa: BLE001
            skipped.append(f"{name} ({type(e).__name__})")
            print(f"   erro: {e}")

    payload = {
        "meta": {
            "n": args.n, "dim": args.dim, "queries": args.queries,
            "seed": args.seed, "k": K,
            "timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "machine": f"{platform.system()} {platform.machine()}",
            "python": platform.python_version(),
            "measured": True,
        },
        "results": results,
        "skipped": skipped,
    }
    out = Path(args.json_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(payload, indent=2, ensure_ascii=False), encoding="utf-8")
    write_report(payload, Path(args.report_out))
    print(f"\nOK: {out} e {args.report_out}")


if __name__ == "__main__":
    main()