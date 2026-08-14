"""
Coleta e consolida os resultados de treinamento MGGP das pastas RESULTADOS-1/2/3.

Lê, para cada Treinamento_N válido (conforme config_validos.py):
  - parametros_utilizados.csv  -> hiperparâmetros usados (nDelays, nTerms, maxHeight, ...)
  - relatorio_validacao*.csv   -> RMSE de cada modelo (1-10) em cada pista Wang

Gera um único CSV consolidado (dados_consolidados.csv) com uma linha por
(pasta, treinamento, modelo, pista), pronto para tabelas e gráficos.

Reexecutável: rode este script de novo depois de adicionar novos treinamentos
válidos (ele varre o disco a cada execução, não há cache).
"""

import csv
import glob
import math
import re
from pathlib import Path

from config_validos import NDELAYS_ESPERADO, EXCLUSOES_MANUAIS

BASE_DIR = Path(__file__).resolve().parent.parent.parent  # TreinamentoMGGP_2_0/
OUT_DIR = Path(__file__).resolve().parent.parent / "tabelas"
PASTAS = ["RESULTADOS-1", "RESULTADOS-2", "RESULTADOS-3"]

# Modelos MGGP que divergiram numericamente (RMSE inf ou absurdamente alto,
# ex: 1e25) em alguma pista são removidos apenas naquela linha específica —
# não descartam o modelo inteiro, já que as outras pistas podem estar boas.
# Ficam registrados em outliers_removidos.csv para auditoria.
RMSE_LIMITE_OUTLIER = 100.0


def tnum(path):
    return int(re.search(r"Treinamento_(\d+)", str(path)).group(1))


def ler_parametros(csv_path):
    params = {}
    with open(csv_path, encoding="utf-8") as fh:
        reader = csv.reader(fh)
        next(reader, None)
        for row in reader:
            if len(row) >= 2:
                params[row[0]] = row[1]
    return params


def ler_validacao(csv_path):
    """Lê relatorio_validacao*.csv (separador ; decimal ,). Retorna lista de dicts.

    Se o arquivo não tiver colunas RMSE_Vx/RMSE_Vy (ex: versão antiga em MAPE),
    retorna lista vazia — quem chamar deve tratar isso como "sem dado válido".
    """
    linhas = []
    with open(csv_path, encoding="utf-8") as fh:
        reader = csv.DictReader(fh, delimiter=";")
        if reader.fieldnames is None or "RMSE_Vx" not in reader.fieldnames:
            return linhas  # formato incompatível (ex: MAPE_Vx) — ignora
        for row in reader:
            linhas.append({
                "modelo": row["Modelo"],
                "pista": row["Pista"],
                "rmse_vx": float(row["RMSE_Vx"].replace(",", ".")),
                "rmse_vy": float(row["RMSE_Vy"].replace(",", ".")),
                "rmse_medio": float(row["RMSE_Médio"].replace(",", ".")),
            })
    return linhas


def encontrar_relatorio_validacao(pasta_treinamento):
    """Aceita tanto relatorio_validacao_rmse.csv quanto relatorio_validacao.csv."""
    candidatos = [
        pasta_treinamento / "relatorio_validacao_rmse.csv",
        pasta_treinamento / "relatorio_validacao.csv",
    ]
    for c in candidatos:
        if c.exists():
            return c
    return None


def coletar():
    linhas_saida = []
    resumo_exclusao = []
    outliers_removidos = []

    for pasta in PASTAS:
        pasta_path = BASE_DIR / pasta
        esperado = NDELAYS_ESPERADO[pasta]
        excluidos_manual = set(EXCLUSOES_MANUAIS.get(pasta, []))

        treinamentos = sorted(
            pasta_path.glob("Treinamento_*/parametros_utilizados.csv"), key=tnum
        )

        for param_csv in treinamentos:
            t = tnum(param_csv)
            pasta_treino = param_csv.parent
            params = ler_parametros(param_csv)
            nd = params.get("nDelays")

            valido = (nd == esperado) and (t not in excluidos_manual)

            if not valido:
                motivo = "nDelays divergente" if nd != esperado else "exclusão manual"
                resumo_exclusao.append((pasta, t, nd, motivo))
                continue

            val_csv = encontrar_relatorio_validacao(pasta_treino)
            if val_csv is None:
                resumo_exclusao.append((pasta, t, nd, "sem relatorio_validacao"))
                continue

            registros = ler_validacao(val_csv)
            if not registros:
                resumo_exclusao.append((pasta, t, nd, "relatorio_validacao sem colunas RMSE (formato incompatível/corrompido)"))
                continue

            for r in registros:
                if not math.isfinite(r["rmse_medio"]) or r["rmse_medio"] > RMSE_LIMITE_OUTLIER:
                    outliers_removidos.append({
                        "pasta": pasta, "treinamento": t, "modelo": r["modelo"],
                        "pista": r["pista"], "rmse_vx": r["rmse_vx"],
                        "rmse_vy": r["rmse_vy"], "rmse_medio": r["rmse_medio"],
                    })
                    continue

                linhas_saida.append({
                    "pasta": pasta,
                    "treinamento": t,
                    "nDelays": nd,
                    "nTerms": params.get("nTerms"),
                    "maxHeight": params.get("maxHeight"),
                    "evaluationMode": params.get("evaluationMode"),
                    "modelo": r["modelo"],
                    "pista": r["pista"],
                    "rmse_vx": r["rmse_vx"],
                    "rmse_vy": r["rmse_vy"],
                    "rmse_medio": r["rmse_medio"],
                })

    return linhas_saida, resumo_exclusao, outliers_removidos


def salvar_csv(linhas, path):
    if not linhas:
        return
    campos = list(linhas[0].keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=campos)
        writer.writeheader()
        writer.writerows(linhas)


def main():
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    linhas, exclusoes, outliers = coletar()

    salvar_csv(linhas, OUT_DIR / "dados_consolidados.csv")

    with open(OUT_DIR / "log_exclusoes.csv", "w", newline="", encoding="utf-8") as fh:
        writer = csv.writer(fh)
        writer.writerow(["pasta", "treinamento", "nDelays_encontrado", "motivo"])
        writer.writerows(exclusoes)

    salvar_csv(outliers, OUT_DIR / "outliers_removidos.csv")

    treinamentos_validos = {(l["pasta"], l["treinamento"]) for l in linhas}
    print(f"Registros consolidados (linha = modelo x pista): {len(linhas)}")
    print(f"Treinamentos válidos incluídos: {len(treinamentos_validos)}")
    for pasta in PASTAS:
        n = len({t for p, t in treinamentos_validos if p == pasta})
        print(f"  {pasta}: {n} treinamentos válidos")
    print(f"Treinamentos excluídos/ignorados: {len(exclusoes)}")
    print(f"Linhas outlier removidas (RMSE inf/absurdo, só a linha): {len(outliers)}")
    print(f"\nArquivos gerados em: {OUT_DIR}")
    print("  - dados_consolidados.csv")
    print("  - log_exclusoes.csv")
    print("  - outliers_removidos.csv")


if __name__ == "__main__":
    main()
