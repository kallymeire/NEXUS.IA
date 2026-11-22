import json, pathlib
from fastapi import FastAPI
app = FastAPI(title="NEXUS-AI API")
M = pathlib.Path(__file__).parents[2] / "docs/dashboard/data/metrics.json"

@app.get("/health")
def health(): return {"status": "ok"}

@app.get("/metrics")
def metrics(): return json.loads(M.read_text())
