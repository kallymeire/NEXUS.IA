# Relatório técnico · Production & LLMOps (observabilidade)

> Trace `5d0a4ca697e64a279874e9f00225e2e6` · serviço `nexus-ai-experimentos` · 2026-11-27T14:18:59+00:00 (UTC).

## Escopo

Este relatório mostra o tracing do **pipeline de experimentos** do projeto, com tempos medidos por span. Não é um trace de agente LLM. Para isso, a mesma camada (`scripts/nexus_tracing.py`) precisa envolver as chamadas de um agente real.

## Resultados

- Duração total: 159,88 s.
- Spans registrados: 67. Spans com erro: 0.

| Etapa | Ocorrências | Média (ms) | Máximo (ms) |
|---|---|---|---|
| `experimento` | 1 | 143469,1 | 143469,1 |
| `modelo` | 3 | 47604,6 | 85184,8 |
| `seed` | 15 | 4669,8 | 12687,8 |
| `treinar` | 15 | 4611,1 | 12628,7 |
| `preparar` | 15 | 40,9 | 93,6 |
| `exportar` | 1 | 314,4 | 314,4 |
| `carregar_dados` | 1 | 291,7 | 291,7 |
| `avaliar` | 15 | 16,4 | 32,3 |
| `teste_welch` | 1 | 45,0 | 45,0 |

Maior span que não é a raiz: `modelo:mlp_128_64` (85184,8 ms).

## Reprodução

```bash
python scripts/run_real_experiments.py
python scripts/generate_reports.py
```
