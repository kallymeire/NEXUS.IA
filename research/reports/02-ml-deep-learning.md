# Relatório técnico · ML & Deep Learning

> Gerado automaticamente em 2026-11-27T14:21:39+00:00 (UTC) a partir de uma execução real. Commit: `180e6bf`.

## Hipótese

H1: um MLP maior (camadas 128 e 64) tem acurácia de teste maior do que um MLP pequeno (32 neurônios) no mesmo conjunto de dados e com o mesmo protocolo.

## Implementação

- Dados: `sklearn.datasets.load_digits` (1797 amostras, 64 atributos, 10 classes), 25% para teste, split estratificado.
- Modelos: regressão logística (baseline), MLP (32), MLP (128, 64). Épocas = 60, taxa de aprendizado = 0,001.
- Seeds: [0, 1, 2, 3, 4]. Cada seed muda o split e a inicialização.
- Registro: MLflow ativo (15 runs).

## Resultados

| Modelo | Acurácia de teste (média ± desvio) | Perda de teste (média) | Tempo de treino (s) |
|---|---|---|---|
| `logreg` | 96,93% ± 1,27% | 0,1089 | 0,37 |
| `mlp_32` | 97,11% ± 0,75% | 0,1031 | 3,45 |
| `mlp_128_64` | 97,78% ± 0,57% | 0,0785 | 10,02 |

## Significância estatística (teste de Welch)

- Não há evidência de diferença entre `mlp_128_64` e `mlp_32` (p = 0,155, α = 0,05). t = 1,581.
- Não há evidência de diferença entre `mlp_128_64` e `logreg` (p = 0,228, α = 0,05). t = 1,357.

## Limitações

- Apenas 5 seeds por modelo: o teste tem pouco poder estatístico.
- `load_digits` é um conjunto pequeno e fácil. O resultado não vale para CNN, Transformer ou dados maiores.
- As curvas de aprendizado guardadas no JSON são só da seed 0.

## Reprodução

```bash
python scripts/run_real_experiments.py --seeds 5 --epochs 60
python scripts/generate_reports.py
```

Ambiente: Python 3.10.11, numpy 2.2.6, scikit-learn 1.7.2.
