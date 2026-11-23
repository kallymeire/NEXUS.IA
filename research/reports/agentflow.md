# Relatório: Avaliação real do AgentFlow

## Hipótese
Um agente supervisor (LangGraph) que roteia a pergunta para o especialista certo
(loja, planilha, cálculo ou geral) responde corretamente os casos de teste,
e o juiz automático concorda com a checagem por palavras-chave.

## Implementação
- Agentes: supervisor → loja / planilha / cálculo / geral (LangGraph)
- Modelo do agente: `gemini-3.1-flash-lite`
- Juiz: Gemini com saída estruturada (veredito) avaliando o significado da resposta
- Checagem simples: palavras-chave esperadas na resposta
- Script: `avaliar.py` (exporta `avaliacao.json`)

## Protocolo de avaliação
- 13 casos de teste, distribuídos entre os agentes loja, planilha, cálculo e geral
- Para cada caso: agente que respondeu, checagem por palavras-chave, veredito do juiz
- Também são contados os tokens de entrada e saída
- Execução usada neste relatório: 22/11/2026

## Resultados
| Métrica | Resultado |
|---|---|
| Casos que passaram | 13/13 |
| Erros de execução | 0 |
| Acertos por palavras-chave | 13/13 |
| Acertos pelo juiz | 13/13 |
| Divergências (palavras-chave × juiz) | 0 |
| Tokens de entrada | 7.870 |
| Tokens de saída | 959 |
| Tokens no total | 8.829 |

## Limitações
- Só 13 casos: serve para detectar regressão, não para provar qualidade geral
- O agente e o juiz são da família Gemini, então o juiz pode favorecer respostas do próprio estilo do modelo
- Casos escritos por mim, sem conjunto de teste independente
- 13/13 com 0 divergências pode indicar que os casos ainda são fáceis

## Próximos passos
- Rodar o `avaliar.py` a cada push (CI)
- Aumentar o número de casos e incluir casos difíceis e ambíguos
- Testar um juiz de outro provedor para comparar