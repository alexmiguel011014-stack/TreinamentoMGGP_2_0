# -*- coding: utf-8 -*-
import os, glob, re
import pandas as pd
import numpy as np

BASE = r"C:\Users\beatl\OneDrive\Área de Trabalho\TreinamentoMGGP_2_0"
TAB = os.path.join(BASE, "mineracao", "tabelas")
os.makedirs(TAB, exist_ok=True)
OUT = os.path.join(TAB, "rmse_medio_por_treinamento.csv")

PCS = {"RESULTADOS-2": "PC2", "RESULTADOS-3": "PC3"}

def param(p, key):
    f = os.path.join(p, "parametros_utilizados.csv")
    if not os.path.exists(f):
        return None
    for ln in open(f, encoding="utf-8", errors="replace"):
        if ln.strip().lower().startswith(key.lower() + ","):
            return ln.strip().split(",", 1)[1]
    return None

def nDelays(p):
    f = os.path.join(p, "parametros_utilizados.csv")
    if not os.path.exists(f):
        return None
    for ln in open(f, encoding="utf-8", errors="replace"):
        if ln.strip().lower().startswith("ndelays"):
            m = re.search(r"\[([^\]]*)\]", ln)
            if m:
                nums = [int(x) for x in re.findall(r"\d+", m.group(1))]
                return nums if nums else None
    return None

def read_rows(path):
    """Retorna (metric, lista de linhas). Detecta RMSE vs MAPE pelo CABEÇALHO."""
    with open(path, encoding="utf-8", errors="replace") as fh:
        lines = fh.read().splitlines()
    if not lines:
        return None, []
    header = lines[0].upper()
    metric = "RMSE" if "RMSE" in header else ("MAPE" if "MAPE" in header else None)
    rows = []
    for ln in lines[1:]:
        c = ln.split(";")
        if len(c) < 4:
            continue
        def num(s):
            s = s.replace(",", ".").strip()
            try:
                return float(s)
            except Exception:
                return None
        rows.append((c[0].strip(), c[1].strip(), num(c[2]), num(c[3])))
    return metric, rows

def bad(v):
    if v is None:
        return False
    return v != v or v == float("inf") or v >= 1e10

def fmt(v):
    if v is None:
        return None            # célula vazia
    return "inf" if bad(v) else round(v, 6)

def cellstr(v):
    if v is None:
        return ""
    return f"{v:g}" if isinstance(v, float) and v == np.inf else str(v)

records = []
for pc, pcname in PCS.items():
    for folder in sorted(glob.glob(os.path.join(BASE, pc, "Treinamento_*")),
                         key=lambda x: int(x.split("_")[-1])):
        fid = int(os.path.basename(folder).split("_")[-1])
        r_rmse = os.path.join(folder, "relatorio_validacao_rmse.csv")
        r_mape = os.path.join(folder, "relatorio_validacao.csv")

        path = None
        if os.path.exists(r_rmse):
            path = r_rmse
        elif os.path.exists(r_mape):
            path = r_mape

        metric, rows = (None, [])
        pend = ""
        if path:
            metric, rows = read_rows(path)

        vx_all, vy_all = [], []
        divergiu = False
        if metric == "RMSE" and rows:
            for modelo, pista, vx, vy in rows:
                vx_all.append(vx)
                vy_all.append(vy)
                if bad(vx) or bad(vy):
                    divergiu = True
        elif metric == "MAPE":
            pend = "apenas MAPE (sem RMSE)"
        else:
            pend = "relatorio sem tabela / incompleto"

        def fmean(lst):
            vals = [v for v in lst if v is not None]
            return np.mean(vals) if vals else None
        vx_mean = fmean(vx_all)
        vy_mean = fmean(vy_all)

        records.append(dict(
            PC=pc, PC_nome=pcname, ID=fid,
            nDelays=nDelays(folder),
            nTerms=param(folder, "nTerms"),
            maxHeight=param(folder, "maxHeight"),
            RMSE_Vx_medio=fmt(vx_mean),
            RMSE_Vy_medio=fmt(vy_mean),
            divergiu=divergiu,
            pendencia=pend,
        ))

tab = pd.DataFrame(records)
tab = tab.sort_values(["PC", "ID"]).reset_index(drop=True)
tab.to_csv(OUT, index=False, sep=";", decimal=",")
print("Gerado:", OUT)
print("Linhas:", len(tab))

# Relatório de pendências
for pc, pcname in PCS.items():
    t = tab[tab["PC"] == pc]
    withp = t[t["pendencia"] != ""]
    nondiv = t[~t["divergiu"]]
    print(f"\n[{pcname}] total={len(t)} | sem divergência={len(nondiv)}")
    if len(withp):
        print("  com pendência:")
        for _, r in withp.iterrows():
            print(f"    ID {r['ID']:>2}: {r['pendencia']}")
    print("  Vx_medio mediana:", t['RMSE_Vx_medio'].dropna().astype(float).median()
          if t['RMSE_Vx_medio'].notna().any() and not (t['RMSE_Vx_medio'] == 'inf').any() else "tem inf")

print("\n--- amostra (primeiras 12 linhas) ---")
print(tab.head(12).to_string(show_dimensions=False))