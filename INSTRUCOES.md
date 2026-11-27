# Como terminar os 3 itens pendentes do roadmap

Copie as pastas deste pacote para a raiz do repositório (elas só **adicionam** arquivos; nada do que já existe é alterado).

```
scripts/nexus_tracing.py            # tracing com tempos medidos (+ envio opcional ao Phoenix)
scripts/run_real_experiments.py     # experimentos reais + MLflow + JSON
scripts/generate_reports.py         # gera research/reports/*.md a partir dos resultados reais
tests/test_real_experiments.py      # testes rápidos para o CI
requirements-real.txt
```

## 1) Rodar no seu computador (PowerShell)

```powershell
pip install -r requirements.txt -r requirements-real.txt
python scripts/run_real_experiments.py
python scripts/generate_reports.py
mlflow ui --backend-store-uri sqlite:///mlflow.db   # abra http://127.0.0.1:5000
```

Saídas: `docs/dashboard/data/real_runs.json`, `docs/dashboard/data/real_traces.json`,
`research/reports/*.md` e o arquivo `mlflow.db` (coloque `mlflow.db` e `mlruns/` no `.gitignore`).

## 2) Traces no Phoenix (opcional, local, sem conta)

```powershell
pip install arize-phoenix opentelemetry-sdk opentelemetry-exporter-otlp-proto-http
phoenix serve                                   # em um terminal
$env:PHOENIX_COLLECTOR_ENDPOINT="http://localhost:6006"
python scripts/run_real_experiments.py          # em outro terminal
```

O envio ao Phoenix **não foi testado** (não havia Phoenix disponível onde o código foi escrito).
Se falhar, o JSON dos traces continua sendo gerado normalmente.

## 3) Traces de agente de verdade (AgentFlow)

O trace do roadmap é "de agentes". Para isso, envolva as chamadas do `avaliar.py` do AgentFlow:

```python
from nexus_tracing import Tracer
tracer = Tracer("agentflow")
with tracer.span("caso", id=caso_id):
    with tracer.span("agente"):
        resposta = rodar_agente(pergunta)
    with tracer.span("juiz"):
        nota = julgar(resposta)
tracer.save("docs/dashboard/data/real_traces.json")
tracer.export_otlp()
```

## 4) CI (acrescente ao seu `.github/workflows/ci.yml`)

```yaml
- name: Experimentos reais (rápido)
  run: |
    pip install -r requirements.txt -r requirements-real.txt
    python scripts/run_real_experiments.py --fast
    python scripts/generate_reports.py
```

## 5) Só marque no README depois de verificar

| Item | Marque `[x]` quando |
|---|---|
| Dados reais (MLflow / W&B) | você rodou o script, abriu o `mlflow ui` e fez commit do `real_runs.json` |
| Traces reais de agentes | os traces do **AgentFlow** estiverem em `real_traces.json` (hoje o trace é só do pipeline de experimentos) |
| Relatórios técnicos por módulo | os 7 módulos tiverem relatório. Hoje são 2 de 7; deixe `[ ]` ou escreva "(2 de 7)" |

Atualize também a seção **Limitações** do README: o painel principal ainda usa dados simulados.
Os arquivos `real_runs.json` e `real_traces.json` ficam publicados em
`/dashboard/data/`, mas **ainda não estão ligados ao `docs/index.html`**. Para isso preciso do
`docs/index.html` e do `scripts/generate_metrics.py`.
