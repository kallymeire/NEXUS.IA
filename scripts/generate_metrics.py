"""Writes docs/dashboard/data/metrics.json and inlines it into index.html.
Demo data (seeded). Replace the generators with reads from MLflow / W&B / LangSmith."""
import json, math, random, pathlib, re
root = pathlib.Path(__file__).parents[1]
r = random.Random(7)
ml = []
for n, a, b in [("MLP", 1.0, .07), ("CNN", .9, .10), ("Transformer", 1.1, .13)]:
    loss = [round(a*math.exp(-b*e) + .05 + r.random()*.02, 4) for e in range(40)]
    val = [round(l + .03 + r.random()*.03, 4) for l in loss]
    ml.append({"n": n, "loss": loss, "val": val, "acc": [round(1-v*.8, 4) for v in val]})
dbs = [{"n": "Qdrant", "lat": 18, "rec": .96, "qps": 920, "cost": .40},
       {"n": "Chroma", "lat": 26, "rec": .92, "qps": 610, "cost": .10},
       {"n": "Pinecone", "lat": 22, "rec": .95, "qps": 780, "cost": .90},
       {"n": "Weaviate", "lat": 24, "rec": .94, "qps": 700, "cost": .55}]
days = [f"D{i+1}" for i in range(30)]
ops = {"days": days,
       "cost": [round(14 - i*.18 + r.random()*1.2, 2) for i in range(30)],
       "lat": [round(900 - i*9 + r.random()*60) for i in range(30)],
       "pass": [round(.78 + i*.005 + r.random()*.03, 3) for i in range(30)]}
trace = [{"n": "plan", "k": "LLM", "t": 0, "d": 320, "i": "Decompose question into 3 sub-tasks"},
         {"n": "embed query", "k": "Embeddings", "t": 320, "d": 90, "i": "text-embedding, 1 call"},
         {"n": "vector search", "k": "Qdrant", "t": 410, "d": 140, "i": "top_k=8, recall@8 = 0.94"},
         {"n": "rerank", "k": "Tool", "t": 550, "d": 210, "i": "cross-encoder reranker"},
         {"n": "calc tool", "k": "Tool Calling", "t": 760, "d": 120, "i": "function call with structured JSON args"},
         {"n": "guardrail check", "k": "Security", "t": 880, "d": 70, "i": "PII + prompt-injection filter passed"},
         {"n": "answer", "k": "LLM", "t": 950, "d": 540, "i": "grounded answer with citations"}]
data = {"ml": ml, "dbs": dbs, "ops": ops, "trace": trace}
out = root / "docs/dashboard"
(out / "data").mkdir(parents=True, exist_ok=True)
(out / "data/metrics.json").write_text(json.dumps(data))
idx = out / "index.html"
if idx.exists():
    h = idx.read_text()
    h = re.sub(r"/\*DATA\*/.*?/\*END\*/", lambda m: "/*DATA*/" + json.dumps(data) + "/*END*/", h, flags=re.S)
    idx.write_text(h)
print("metrics.json updated")
