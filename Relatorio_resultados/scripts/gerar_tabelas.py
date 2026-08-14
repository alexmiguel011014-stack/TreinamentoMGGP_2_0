"""
Gera tabelas resumo a partir de dados_consolidados.csv:

  1. ranking_geral.csv        -> todos os modelos ordenados por RMSE médio (melhor primeiro)
  2. resumo_por_pasta.csv     -> estatísticas de RMSE agregadas por pasta (=por nDelays)
  3. resumo_por_nterms_maxheight.csv -> estatísticas agregadas por (nTerms, maxHeight), todas as pastas juntas
  4. resumo_por_pista.csv     -> estatísticas agregadas por pista de validação (Wang 2.1/2.2/3.1/8.1)

"RMSE médio do modelo" = média das 4 pistas (Treino, Validação, Teste A, Teste B)
para aquele modelo específico. É essa métrica que usamos para ranking/comparação
geral, porque resume o desempenho do modelo num único número.

Rode depois de coletar_dados.py.
"""

import csv
import statistics as stats
from collections import defaultdict
from pathlib import Path

TAB_DIR = Path(__file__).resolve().parent.parent / "tabelas"


def carregar_dados():
    with open(TAB_DIR / "dados_consolidados.csv", encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def rmse_por_modelo(linhas):
    """Agrupa linhas (pasta,treinamento,modelo) e calcula a média das pistas.

    Se o modelo tiver menos de 4 pistas (por causa de outliers removidos),
    a média é feita só com as pistas disponíveis — e isso fica marcado.
    """
    grupos = defaultdict(list)
    meta = {}
    for l in linhas:
        chave = (l["pasta"], l["treinamento"], l["modelo"])
        grupos[chave].append(float(l["rmse_medio"]))
        meta[chave] = l  # guarda a última linha p/ pegar nTerms/maxHeight/nDelays

    resultado = []
    for chave, valores in grupos.items():
        pasta, treinamento, modelo = chave
        m = meta[chave]
        resultado.append({
            "pasta": pasta,
            "treinamento": treinamento,
            "nDelays": m["nDelays"],
            "nTerms": m["nTerms"],
            "maxHeight": m["maxHeight"],
            "modelo": modelo,
            "n_pistas_validas": len(valores),
            "rmse_medio_modelo": round(stats.mean(valores), 4),
        })
    return resultado


def salvar_csv(linhas, path, campos=None):
    if not linhas:
        print(f"[AVISO] Nenhuma linha para salvar em {path.name}")
        return
    campos = campos or list(linhas[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def gerar_ranking_geral(linhas):
    por_modelo = rmse_por_modelo(linhas)
    por_modelo.sort(key=lambda r: r["rmse_medio_modelo"])
    for i, r in enumerate(por_modelo, start=1):
        r["ranking"] = i
    campos = ["ranking", "pasta", "treinamento", "nDelays", "nTerms", "maxHeight",
              "modelo", "n_pistas_validas", "rmse_medio_modelo"]
    salvar_csv(por_modelo, TAB_DIR / "ranking_geral.csv", campos)
    return por_modelo


def gerar_resumo_por_pasta(por_modelo):
    grupos = defaultdict(list)
    for r in por_modelo:
        grupos[(r["pasta"], r["nDelays"])].append(r["rmse_medio_modelo"])

    saida = []
    for (pasta, nd), valores in sorted(grupos.items()):
        saida.append({
            "pasta": pasta,
            "nDelays": nd,
            "n_modelos": len(valores),
            "rmse_min": round(min(valores), 4),
            "rmse_max": round(max(valores), 4),
            "rmse_media": round(stats.mean(valores), 4),
            "rmse_mediana": round(stats.median(valores), 4),
            "rmse_desvio_padrao": round(stats.stdev(valores), 4) if len(valores) > 1 else 0.0,
        })
    salvar_csv(saida, TAB_DIR / "resumo_por_pasta.csv")
    return saida


def gerar_resumo_por_nterms_maxheight(por_modelo):
    grupos = defaultdict(list)
    for r in por_modelo:
        grupos[(r["nTerms"], r["maxHeight"])].append(r["rmse_medio_modelo"])

    saida = []
    for (nterms, maxh), valores in sorted(grupos.items(), key=lambda kv: (int(kv[0][0]), int(kv[0][1]))):
        saida.append({
            "nTerms": nterms,
            "maxHeight": maxh,
            "n_modelos": len(valores),
            "rmse_min": round(min(valores), 4),
            "rmse_max": round(max(valores), 4),
            "rmse_media": round(stats.mean(valores), 4),
            "rmse_mediana": round(stats.median(valores), 4),
        })
    salvar_csv(saida, TAB_DIR / "resumo_por_nterms_maxheight.csv")
    return saida


def gerar_resumo_por_pista(linhas):
    grupos = defaultdict(list)
    for l in linhas:
        grupos[l["pista"]].append(float(l["rmse_medio"]))

    saida = []
    for pista, valores in grupos.items():
        saida.append({
            "pista": pista,
            "n_registros": len(valores),
            "rmse_min": round(min(valores), 4),
            "rmse_max": round(max(valores), 4),
            "rmse_media": round(stats.mean(valores), 4),
            "rmse_mediana": round(stats.median(valores), 4),
        })
    salvar_csv(saida, TAB_DIR / "resumo_por_pista.csv")
    return saida


def main():
    linhas = carregar_dados()
    if not linhas:
        print("dados_consolidados.csv vazio ou não encontrado. Rode coletar_dados.py primeiro.")
        return

    por_modelo = gerar_ranking_geral(linhas)
    gerar_resumo_por_pasta(por_modelo)
    gerar_resumo_por_nterms_maxheight(por_modelo)
    gerar_resumo_por_pista(linhas)

    print(f"Modelos únicos avaliados: {len(por_modelo)}")
    print(f"Melhor modelo geral: {por_modelo[0]['pasta']}/Treinamento_{por_modelo[0]['treinamento']}/"
          f"{por_modelo[0]['modelo']} — RMSE médio {por_modelo[0]['rmse_medio_modelo']}")
    print(f"\nTabelas geradas em: {TAB_DIR}")
    print("  - ranking_geral.csv")
    print("  - resumo_por_pasta.csv")
    print("  - resumo_por_nterms_maxheight.csv")
    print("  - resumo_por_pista.csv")


if __name__ == "__main__":
    main()
