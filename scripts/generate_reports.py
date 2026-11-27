#!/usr/bin/env python3
"""Gera relatórios técnicos em Markdown a partir de resultados REAIS.

Lê  docs/dashboard/data/real_runs.json   (scripts/run_real_experiments.py)
    docs/dashboard/data/real_traces.json (scripts/nexus_tracing.py)
Escreve research/reports/*.md. Só gera relatório para módulo que tem dado real;
os demais aparecem como pendentes no índice (research/reports/README.md).
"""
from __future__ import annotations

import argparse
import json
from collections import defaultdict
from pathlib import Path

MODULOS = [
    ("01", "Foundations", None),
    ("02", "ML & Deep Learning", "02-ml-deep-learning.md"),
    ("03", "LLM Applications", None),
    ("04", "Production & LLMOps", "04-production-llmops.md"),
    ("05", "Advanced", None),
    ("06", "Core Tools", None),
    ("07", "Portfolio", None),
]

ALPHA = 0.05


def br(x, nd=2):
    """Número com vírgula decimal (padrão brasileiro)."""
    return f"{x:.{nd}f}".replace(".", ",")


def pct(x):
    return br(100 * x, 2) + "%"


def fmt_p(p):
    if p is None:
        return "n/d"
    return "< 0,001" if p < 0.001 else f"{p:.3f}".replace(".", ",")


def veredito(w, a, b):
    p = w.get("p")
    if p is None:
        return f"Não foi possível testar {a} contra {b}: seeds insuficientes."
    if p < ALPHA:
        return (f"A diferença entre `{a}` e `{b}` é estatisticamente significativa "
                f"(p = {fmt_p(p)}, α = {br(ALPHA, 2)}).")
    return (f"Não há evidência de diferença entre `{a}` e `{b}` "
            f"(p = {fmt_p(p)}, α = {br(ALPHA, 2)}).")


def relatorio_ml(runs: dict) -> str:
    m, mod = runs["meta"], runs["modelos"]
    wp, wb = runs["welch_principal"], runs["welch_vs_baseline"]
    n = len(m["seeds"])
    linhas = [
        "# Relatório técnico · ML & Deep Learning",
        "",
        f"> Gerado automaticamente em {m['gerado_em_utc']} (UTC) a partir de uma execução real. "
        f"Commit: `{m.get('git_sha') or 'n/d'}`.",
        "",
        "## Hipótese",
        "",
        "H1: um MLP maior (camadas 128 e 64) tem acurácia de teste maior do que um MLP pequeno "
        "(32 neurônios) no mesmo conjunto de dados e com o mesmo protocolo.",
        "",
        "## Implementação",
        "",
        f"- Dados: `{m['dataset']['nome']}` ({m['dataset']['amostras']} amostras, "
        f"{m['dataset']['atributos']} atributos, {m['dataset']['classes']} classes), "
        f"{int(m['dataset']['teste'] * 100)}% para teste, split estratificado.",
        f"- Modelos: regressão logística (baseline), MLP (32), MLP (128, 64). "
        f"Épocas = {m['epocas']}, taxa de aprendizado = {str(m['lr']).replace('.', ',')}.",
        f"- Seeds: {m['seeds']}. Cada seed muda o split e a inicialização.",
        f"- Registro: MLflow {'ativo (' + str(len(m['mlflow']['run_ids'])) + ' runs)' if m['mlflow']['ativo'] else 'não estava instalado nesta execução'}.",
        "",
        "## Resultados",
        "",
        "| Modelo | Acurácia de teste (média ± desvio) | Perda de teste (média) | Tempo de treino (s) |",
        "|---|---|---|---|",
    ]
    for nome, r in mod.items():
        d = r["test_acc_desvio"]
        dtxt = "n/d" if d is None else pct(d)
        linhas.append(f"| `{nome}` | {pct(r['test_acc_media'])} ± {dtxt} | "
                      f"{br(r['test_loss_media'], 4)} | {br(r['train_seconds_media'], 2)} |")
    linhas += [
        "",
        "## Significância estatística (teste de Welch)",
        "",
        f"- {veredito(wp, wp['a'], wp['b'])} t = "
        f"{'n/d' if wp['t'] is None else br(wp['t'], 3)}.",
        f"- {veredito(wb, wb['a'], wb['b'])} t = "
        f"{'n/d' if wb['t'] is None else br(wb['t'], 3)}.",
        "",
        "## Limitações",
        "",
        f"- Apenas {n} seeds por modelo: o teste tem pouco poder estatístico.",
        "- `load_digits` é um conjunto pequeno e fácil. O resultado não vale para CNN, "
        "Transformer ou dados maiores.",
        "- As curvas de aprendizado guardadas no JSON são só da seed 0.",
        "",
        "## Reprodução",
        "",
        "```bash",
        f"python scripts/run_real_experiments.py --seeds {n} --epochs {m['epocas']}",
        "python scripts/generate_reports.py",
        "```",
        "",
        f"Ambiente: Python {m['ambiente']['python']}, numpy {m['ambiente']['numpy']}, "
        f"scikit-learn {m['ambiente']['scikit_learn']}.",
        "",
    ]
    return "\n".join(linhas)


def relatorio_llmops(tr: dict) -> str:
    spans = tr["spans"]
    agg = defaultdict(list)
    erros = 0
    for s in spans:
        nome = s["name"].split(":")[0] if s["name"].startswith(("seed", "modelo")) else s["name"]
        agg[nome].append(s["duration_ms"])
        erros += s["status"] == "error"
    linhas = [
        "# Relatório técnico · Production & LLMOps (observabilidade)",
        "",
        f"> Trace `{tr['trace_id']}` · serviço `{tr['service']}` · {tr['started_at_utc']} (UTC).",
        "",
        "## Escopo",
        "",
        "Este relatório mostra o tracing do **pipeline de experimentos** do projeto, com tempos "
        "medidos por span. Não é um trace de agente LLM. Para isso, a mesma camada "
        "(`scripts/nexus_tracing.py`) precisa envolver as chamadas de um agente real.",
        "",
        "## Resultados",
        "",
        f"- Duração total: {br(tr['total_ms'] / 1000, 2)} s.",
        f"- Spans registrados: {len(spans)}. Spans com erro: {erros}.",
        "",
        "| Etapa | Ocorrências | Média (ms) | Máximo (ms) |",
        "|---|---|---|---|",
    ]
    for nome, ds in sorted(agg.items(), key=lambda kv: -sum(kv[1])):
        linhas.append(f"| `{nome}` | {len(ds)} | {br(sum(ds) / len(ds), 1)} | {br(max(ds), 1)} |")
    mais_lento = max(spans, key=lambda s: s["duration_ms"] if s["parent_id"] else -1, default=None)
    if mais_lento:
        linhas += ["", f"Maior span que não é a raiz: `{mais_lento['name']}` "
                       f"({br(mais_lento['duration_ms'], 1)} ms)."]
    linhas += ["", "## Reprodução", "", "```bash",
               "python scripts/run_real_experiments.py",
               "python scripts/generate_reports.py", "```", ""]
    return "\n".join(linhas)


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--runs", default="docs/dashboard/data/real_runs.json")
    ap.add_argument("--traces", default="docs/dashboard/data/real_traces.json")
    ap.add_argument("--out", default="research/reports")
    args = ap.parse_args(argv)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    feitos = {}
    if Path(args.runs).exists():
        runs = json.loads(Path(args.runs).read_text(encoding="utf-8"))
        (out / "02-ml-deep-learning.md").write_text(relatorio_ml(runs), encoding="utf-8")
        feitos["02"] = "02-ml-deep-learning.md"
    if Path(args.traces).exists():
        tr = json.loads(Path(args.traces).read_text(encoding="utf-8"))
        (out / "04-production-llmops.md").write_text(relatorio_llmops(tr), encoding="utf-8")
        feitos["04"] = "04-production-llmops.md"

    idx = ["# Relatórios técnicos por módulo", "",
           "Só existe relatório onde há experimento real. Os demais módulos estão pendentes.", "",
           "| Módulo | Situação |", "|---|---|"]
    for num, nome, _ in MODULOS:
        if num in feitos:
            idx.append(f"| {num} · {nome} | ✅ [{feitos[num]}]({feitos[num]}) |")
        else:
            idx.append(f"| {num} · {nome} | ⏳ pendente (sem experimento real ainda) |")
    idx += ["", f"**{len(feitos)} de {len(MODULOS)} módulos com relatório.**", ""]
    (out / "README.md").write_text("\n".join(idx), encoding="utf-8")
    print(f"OK  {len(feitos)} relatório(s) em {out}/ (de {len(MODULOS)} módulos)")
    return feitos


if __name__ == "__main__":
    main()
