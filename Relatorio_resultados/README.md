# Relatorio_resultados

Análise comparativa dos treinamentos MGGP (preditor MIMO Vx/Vy) nas 3 pastas
`RESULTADOS-1`, `RESULTADOS-2`, `RESULTADOS-3` (3 PCs diferentes).

## Como reexecutar (depois de treinar mais e incluir novos resultados)

Sempre que novos treinamentos forem concluídos (novas pastas `Treinamento_N` com
`parametros_utilizados.csv` + `relatorio_validacao*.csv`), rode os 3 scripts em
ordem — eles varrem o disco do zero a cada execução, não há cache:

```
cd TreinamentoMGGP_2_0/Relatorio_resultados/scripts
python coletar_dados.py
python gerar_tabelas.py
python gerar_graficos.py
```

Os treinamentos novos entram automaticamente **se o nDelays deles bater com o
valor correto da pasta** (definido em `scripts/config_validos.py`). Não é
preciso editar nada manualmente, a menos que:

- Queira excluir um treinamento específico por outro motivo (edite
  `EXCLUSOES_MANUAIS` em `config_validos.py`).
- O valor correto de nDelays de alguma pasta mude (edite `NDELAYS_ESPERADO`).

## nDelays correto de cada pasta (critério de validade)

| Pasta | nDelays correto |
|---|---|
| RESULTADOS-1 | `[1]` |
| RESULTADOS-2 | `[1, 2, 5, 10, 25, 50]` |
| RESULTADOS-3 | `[1, 2, 5, 10]` |

Treinamentos com nDelays diferente do esperado da pasta são excluídos
automaticamente e ficam listados em `tabelas/log_exclusoes.csv`.

## Pendências conhecidas (situação em 2026-08-13, atualizado)

- ✅ **RESULTADOS-2, Treinamento_4 a 10**: RESOLVIDO. Estavam com relatório de
  validação em MAPE; foram revalidados com `scripts/revalidar_rmse.py`
  (rodado no VS Code) recarregando os `.pkl` já treinados — sem retreinar.
  Os modelos desses treinamentos usam o nome `modelo_mape_N.pkl` (o script
  precisou ser ajustado para procurar por esse nome de arquivo, em vez de
  `modelo_rmse_N.pkl`). Já estão no `dados_consolidados.csv` (RESULTADOS-2
  passou de 3 para 10 treinamentos válidos, 30 → 100 modelos).
- **RESULTADOS-1**: Treinamento_40, 41, 48 rodaram com nDelays errado
  (`[1,2,5,10]` em vez de `[1]`) — precisam ser refeitos.
- **RESULTADOS-1**: Treinamento_39 e 47 estão incompletos (pararam no meio,
  só 7/10 modelos, sem validação) — precisam ser retomados/concluídos.
- **RESULTADOS-2**: Treinamento_11 a 49 rodaram com nDelays errado
  (`[1,2,5,10]` em vez de `[1,2,5,10,25,50]`) — precisam ser refeitos.
- **RESULTADOS-3**: Treinamento_6 nunca existiu de fato (a pasta ficou com
  um `relatorio_validacao_rmse.csv` corrompido, contendo o conteúdo de
  `parametros_utilizados.csv`) — precisa ser refeito do zero.

## Outliers numéricos (modelos que divergiram)

20 combinações (modelo, pista) tiveram RMSE infinito ou astronomicamente alto
(ex: 1e25) — provavelmente instabilidade numérica de alguma árvore MGGP
(divisão por zero, extrapolação ruim). Essas linhas específicas foram
removidas dos cálculos de média/ranking (mas as outras pistas do mesmo modelo,
se válidas, continuam entrando). Lista completa em
`tabelas/outliers_removidos.csv`.

## Arquivos gerados

### tabelas/
- `dados_consolidados.csv` — uma linha por (pasta, treinamento, modelo, pista); dataset bruto para qualquer análise extra
- `log_exclusoes.csv` — treinamentos que ficaram de fora e por quê
- `outliers_removidos.csv` — linhas com RMSE inf/absurdo removidas dos cálculos
- `ranking_geral.csv` — todos os 950 modelos ordenados por RMSE médio (melhor primeiro)
- `resumo_por_pasta.csv` — estatísticas de RMSE por pasta/nDelays
- `resumo_por_nterms_maxheight.csv` — estatísticas por combinação nTerms x maxHeight
- `resumo_por_pista.csv` — estatísticas por pista de validação (Wang 2.1/2.2/3.1/8.1)

### graficos/
- `boxplot_por_pasta.png` — distribuição de RMSE por pasta (nDelays)
- `boxplot_por_pista.png` — distribuição de RMSE por pista de validação
- `heatmap_nterms_maxheight.png` — RMSE médio por combinação nTerms x maxHeight
- `evolucao_treinamento.png` — RMSE médio ao longo dos treinamentos, por pasta
- `comparacao_vx_vy.png` — dispersão RMSE Vx vs Vy
- `top10_modelos.png` — os 10 melhores modelos
- `COMO_FORAM_GERADAS.txt` — explicação detalhada de como cada gráfico foi avaliado e gerado

## Resumo do que já sabemos (102 treinamentos válidos, 1020 modelos)

- Melhor modelo geral: `RESULTADOS-3/Treinamento_49/modelo_rmse_9.pkl`, RMSE médio 0.2138
- `nTerms=2` e `nTerms=3` tendem a ter RMSE bem pior que os demais valores (ver heatmap)
- RESULTADOS-3 (nDelays=[1,2,5,10]) domina o top 10 dos melhores modelos
- RESULTADOS-2 (nDelays=[1,2,5,10,25,50], mais complexo) não emplacou nenhum modelo no top 10 até agora
