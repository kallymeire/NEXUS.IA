#!/usr/bin/env python3
"""Experimentos REAIS do Training Lab (sem dados simulados).

- Dados: sklearn.datasets.load_digits (1797 imagens 8x8, 10 classes)
- Modelos: regressão logística (baseline), MLP (32) e MLP (128, 64)
- Cada modelo roda com várias seeds; a seed muda o split treino/teste e a inicialização
- Teste de Welch (scipy) entre MLP grande e MLP pequeno, e contra o baseline
- Cada execução vai para o MLflow (se instalado) e o resumo vai para JSON
- Cada etapa vira um span medido (scripts/nexus_tracing.py)

Uso:
    python scripts/run_real_experiments.py            # completo
    python scripts/run_real_experiments.py --fast     # rápido (CI)
"""
from __future__ import annotations

import argparse
import json
import platform
import subprocess
import sys
import time
import warnings
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
from scipy import stats
from sklearn.datasets import load_digits
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import log_loss
from sklearn.model_selection import train_test_split
from sklearn.neural_network import MLPClassifier
from sklearn.preprocessing import StandardScaler

sys.path.insert(0, str(Path(__file__).resolve().parent))
from nexus_tracing import Tracer  # noqa: E402

MODELS = {
    "logreg": {"kind": "logreg", "descricao": "Regressão logística (baseline)"},
    "mlp_32": {"kind": "mlp", "hidden": (32,), "descricao": "MLP com 1 camada de 32 neurônios"},
    "mlp_128_64": {"kind": "mlp", "hidden": (128, 64), "descricao": "MLP com camadas de 128 e 64"},
}


def welch(a, b) -> dict:
    """Teste t de Welch (variâncias diferentes). Devolve t, p e graus de liberdade."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    if len(a) < 2 or len(b) < 2:
        return {"t": None, "p": None, "df": None, "observacao": "seeds insuficientes (mínimo 2)"}
    res = stats.ttest_ind(a, b, equal_var=False)
    t, p = float(res.statistic), float(res.pvalue)
    if not np.isfinite(t) or not np.isfinite(p):  # variância zero nos dois grupos
        return {"t": 0.0, "p": 1.0, "df": None, "observacao": "variância zero nos dois grupos"}
    df = getattr(res, "df", None)
    return {"t": t, "p": p, "df": float(df) if df is not None else None}


def setup_mlflow(uri: str):
    try:
        import mlflow
    except ImportError:
        print("AVISO: mlflow não instalado; o JSON será gerado, mas sem registro no MLflow.")
        return None
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment("nexus-ai-real")
    return mlflow


def train_one(name, seed, epochs, lr, X, y, tracer):
    spec = MODELS[name]
    classes = np.unique(y)
    with tracer.span("preparar", modelo=name, seed=seed):
        Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.25, stratify=y, random_state=seed)
        scaler = StandardScaler().fit(Xtr)
        Xtr, Xte = scaler.transform(Xtr), scaler.transform(Xte)

    loss_curve, acc_curve = [], []
    t0 = time.perf_counter()
    with tracer.span("treinar", modelo=name, seed=seed, epocas=epochs if spec["kind"] == "mlp" else 1):
        if spec["kind"] == "mlp":
            clf = MLPClassifier(
                hidden_layer_sizes=spec["hidden"], learning_rate_init=lr, batch_size=64, random_state=seed
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                for _ in range(epochs):
                    clf.partial_fit(Xtr, ytr, classes=classes)
                    loss_curve.append(float(clf.loss_))
                    acc_curve.append(float(clf.score(Xte, yte)))
        else:
            clf = LogisticRegression(max_iter=1000)
            clf.fit(Xtr, ytr)
    train_seconds = time.perf_counter() - t0

    with tracer.span("avaliar", modelo=name, seed=seed):
        acc = float(clf.score(Xte, yte))
        loss = float(log_loss(yte, clf.predict_proba(Xte), labels=classes))
    return {
        "seed": seed,
        "test_acc": acc,
        "test_loss": loss,
        "train_seconds": round(train_seconds, 3),
        "loss_curve": loss_curve,
        "acc_curve": acc_curve,
    }


def _git_sha():
    try:
        out = subprocess.run(["git", "rev-parse", "--short", "HEAD"], capture_output=True, text=True, timeout=5)
        return out.stdout.strip() or None
    except Exception:
        return None


def main(argv=None) -> dict:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--seeds", type=int, default=5)
    ap.add_argument("--epochs", type=int, default=60)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--fast", action="store_true", help="3 seeds e 20 épocas (para CI)")
    ap.add_argument("--out", default="docs/dashboard/data/real_runs.json")
    ap.add_argument("--traces", default="docs/dashboard/data/real_traces.json")
    ap.add_argument("--mlflow-uri", default=None, help="padrão: sqlite:///mlflow.db (o MLflow novo não aceita mais ./mlruns)")
    args = ap.parse_args(argv)
    if args.fast:
        args.seeds, args.epochs = 3, 20
    # MLflow 3.x: o backend de arquivos (./mlruns) está em modo de manutenção; use SQLite.
    args.mlflow_uri = args.mlflow_uri or "sqlite:///mlflow.db"

    tracer = Tracer("nexus-ai-experimentos")
    mlflow = setup_mlflow(args.mlflow_uri)
    run_ids: list[str] = []
    seeds = list(range(args.seeds))
    results: dict[str, dict] = {}

    with tracer.span("experimento", seeds=args.seeds, epocas=args.epochs):
        with tracer.span("carregar_dados"):
            data = load_digits()
            X, y = data.data, data.target

        for name, spec in MODELS.items():
            per_seed = []
            with tracer.span(f"modelo:{name}"):
                for seed in seeds:
                    with tracer.span(f"seed:{seed}", modelo=name):
                        r = train_one(name, seed, args.epochs, args.lr, X, y, tracer)
                    per_seed.append(r)
                    if mlflow is not None:
                        with mlflow.start_run(run_name=f"{name}-seed{seed}") as run:
                            mlflow.log_params(
                                {"modelo": name, "seed": seed, "lr": args.lr,
                                 "epocas": args.epochs, "hidden": str(spec.get("hidden", "n/a"))}
                            )
                            for step, (lo, ac) in enumerate(zip(r["loss_curve"], r["acc_curve"])):
                                mlflow.log_metrics({"train_loss": lo, "test_acc_epoca": ac}, step=step)
                            mlflow.log_metrics({"final_test_acc": r["test_acc"], "final_test_loss": r["test_loss"]})
                            run_ids.append(run.info.run_id)
            accs = [r["test_acc"] for r in per_seed]
            first = per_seed[0]
            results[name] = {
                "descricao": spec["descricao"],
                "hidden": list(spec.get("hidden", [])),
                "test_acc_por_seed": accs,
                "test_acc_media": float(np.mean(accs)),
                "test_acc_desvio": float(np.std(accs, ddof=1)) if len(accs) > 1 else None,
                "test_loss_media": float(np.mean([r["test_loss"] for r in per_seed])),
                "train_seconds_media": float(np.mean([r["train_seconds"] for r in per_seed])),
                "curvas_seed0": {"loss": first["loss_curve"], "test_acc": first["acc_curve"]},
            }

        with tracer.span("teste_welch"):
            welch_main = {"a": "mlp_128_64", "b": "mlp_32",
                          **welch(results["mlp_128_64"]["test_acc_por_seed"], results["mlp_32"]["test_acc_por_seed"])}
            welch_base = {"a": "mlp_128_64", "b": "logreg",
                          **welch(results["mlp_128_64"]["test_acc_por_seed"], results["logreg"]["test_acc_por_seed"])}

        with tracer.span("exportar"):
            payload = {
                "meta": {
                    "tipo": "execucao_real",
                    "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                    "git_sha": _git_sha(),
                    "seeds": seeds,
                    "epocas": args.epochs,
                    "lr": args.lr,
                    "dataset": {"nome": "sklearn.datasets.load_digits", "amostras": int(X.shape[0]),
                                "atributos": int(X.shape[1]), "classes": int(len(np.unique(y))), "teste": 0.25},
                    "ambiente": {
                        "python": platform.python_version(),
                        "sistema": platform.platform(),
                        "numpy": np.__version__,
                        "scikit_learn": __import__("sklearn").__version__,
                        "mlflow": getattr(mlflow, "__version__", None),
                    },
                    "mlflow": {"ativo": mlflow is not None, "uri": args.mlflow_uri if mlflow else None,
                               "run_ids": run_ids},
                },
                "modelos": results,
                "welch_principal": welch_main,
                "welch_vs_baseline": welch_base,
            }
            out = Path(args.out)
            out.parent.mkdir(parents=True, exist_ok=True)
            out.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

    tracer.save(args.traces)
    sent = tracer.export_otlp()
    print(f"OK  resultados: {args.out}")
    print(f"OK  traces:     {args.traces}  (enviado ao coletor OTLP: {'sim' if sent else 'não'})")
    for n, r in results.items():
        d = r["test_acc_desvio"]
        print(f"    {n:<11} acc teste = {r['test_acc_media']:.4f} ± {d if d is None else round(d, 4)}")
    p = welch_main.get("p")
    print(f"    Welch mlp_128_64 vs mlp_32: p = {p if p is None else round(p, 4)}")
    return payload


if __name__ == "__main__":
    main()
