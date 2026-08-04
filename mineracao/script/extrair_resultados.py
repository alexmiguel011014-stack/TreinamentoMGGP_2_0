# -*- coding: utf-8 -*-
"""Lê todos os relatórios de validação (RMSE/MAPE) de RESULTADOS_1/-2/-3
e gera uma tabela única consolidada."""
import os, glob, csv, re, sys
import pandas as pd

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DIRS = ["RESULTADOS_1", "RESULTADOS-2", "RESULTADOS-3"]
OUT = os.path.join(ROOT, "mineracao", "tabelas", "todos_resultados.csv")

def parse_nDelays(p):
    f = os.path.join(p, "parametros_utilizados.csv")
    if not os.path.exists(f): return None
    for ln in open(f, encoding="utf-8", errors="replace"):
        if ln.lower().startswith("ndelays"):
            m = re.search(r"\[([^\]]*)\]", ln)
            if m:
                nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
                return nums if nums else None
    return None

def get_param(p, key):
    f = os.path.join(p, "parametros_utilizados.csv")
    if not os.path.exists(f): return None
    for ln in open(f, encoding="utf-8", errors="replace"):
        if ln.strip().lower().startswith(key.lower() + ","):
            return ln.strip().split(",", 1)[1]
    return None

def read_relatorio(path, kind):
    rows = []
    if not os.path.exists(path): return rows
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    if not lines: return rows
    for ln in lines[1:]:
        c = ln.split(";")
        if len(c) < 5: continue
        def num(s):
            s = s.replace(",", ".").strip()
            try: return float(s)
            except: return None
        rows.append((c[0].strip(), c[1].strip(), num(c[2]), num(c[3]), num(c[4])))
    return rows

records = []
for d in DIRS:
    base = os.path.join(ROOT, d)
    for folder in sorted(glob.glob(os.path.join(base, "Treinamento_*")),
                         key=lambda x: int(x.split("_")[-1])):
        fid = int(os.path.basename(folder).split("_")[-1])
        nd = parse_nDelays(folder)
        nT = get_param(folder, "nTerms")
        mH = get_param(folder, "maxHeight")
        evMode = get_param(folder, "evaluationMode")
        r_rmse = os.path.join(folder, "relatorio_validacao_rmse.csv")
        r_mape = os.path.join(folder, "relatorio_validacao.csv")
        if os.path.exists(r_rmse):
            kind, metric, rows = "rmse", "RMSE", read_relatorio(r_rmse, "rmse")
        elif os.path.exists(r_mape):
            kind, metric, rows = "mape", "MAPE", read_relatorio(r_mape, "mape")
        else:
            records.append(dict(PC=d, ID=fid, tipo="?", metric="?",
                                nDelays=nd, nTerms=nT, maxHeight=mH,
                                modelo="?", pista="?", Vx=None, Vy=None, medio=None,
                                divergiu=False))
            continue
        for modelo, pista, vx, vy, med in rows:
            divergiu = any(v is not None and (v != v or v >= 1e10 or v == float("inf")) for v in (vx, vy))
            records.append(dict(PC=d, ID=fid, tipo=kind, metric=metric,
                                nDelays=str(nd), nTerms=nT, maxHeight=mH,
                                modelo=modelo, pista=pista,
                                Vx=vx, Vy=vy, medio=med, divergiu=bool(divergiu)))

df = pd.DataFrame(records)
df.to_csv(OUT, index=False, sep=";", decimal=",")
print("Gerado:", OUT)
print("Linhas:", len(df), "| folders com dados:", df.drop_duplicates(["PC","ID"]).shape[0])
print(df.groupby(["PC","tipo"]).size().to_string())