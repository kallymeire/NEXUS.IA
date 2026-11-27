"""Testes dos experimentos reais, do tracing e do gerador de relatórios (rápidos)."""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

import generate_reports  # noqa: E402
import run_real_experiments as rre  # noqa: E402
from nexus_tracing import Tracer  # noqa: E402


def test_tracer_hierarquia_e_erro():
    t = Tracer("teste")
    with t.span("pai"):
        with t.span("filho", chave=1):
            pass
        try:
            with t.span("falha"):
                raise ValueError("boom")
        except ValueError:
            pass
    d = t.to_dict()
    por_nome = {s["name"]: s for s in d["spans"]}
    assert por_nome["filho"]["parent_id"] == por_nome["pai"]["span_id"]
    assert por_nome["pai"]["parent_id"] is None
    assert por_nome["falha"]["status"] == "error" and "boom" in por_nome["falha"]["error"]
    assert all(s["duration_ms"] >= 0 for s in d["spans"])


def test_tracer_sem_endpoint_nao_exporta(monkeypatch=None):
    t = Tracer("teste")
    assert t.export_otlp(endpoint=None) in (False,)  # sem env/endpoint: False, sem erro


def test_welch_separado_e_igual():
    sep = rre.welch([0.97, 0.98, 0.975, 0.97], [0.90, 0.91, 0.905, 0.9])
    assert sep["p"] < 0.01
    igual = rre.welch([0.95, 0.96, 0.94], [0.95, 0.96, 0.94])
    assert igual["p"] > 0.9
    assert rre.welch([1.0], [0.9])["p"] is None


def test_pipeline_rapido_gera_json_e_relatorios(tmp_path):
    runs, traces, rep = tmp_path / "r.json", tmp_path / "t.json", tmp_path / "reports"
    rre.main(["--seeds", "2", "--epochs", "3", "--out", str(runs), "--traces", str(traces),
              "--mlflow-uri", f"sqlite:///{(tmp_path / 'mlflow.db').as_posix()}"])
    d = json.loads(runs.read_text(encoding="utf-8"))
    assert d["meta"]["tipo"] == "execucao_real"
    for nome in ("logreg", "mlp_32", "mlp_128_64"):
        accs = d["modelos"][nome]["test_acc_por_seed"]
        assert len(accs) == 2 and all(0.5 < a <= 1.0 for a in accs)
    tr = json.loads(traces.read_text(encoding="utf-8"))
    assert any(s["name"] == "experimento" for s in tr["spans"])
    feitos = generate_reports.main(["--runs", str(runs), "--traces", str(traces), "--out", str(rep)])
    assert set(feitos) == {"02", "04"}
    assert "pendente" in (rep / "README.md").read_text(encoding="utf-8")
