# -*- coding: utf-8 -*-
"""Gera tabela consolidada, boxplots e eleição do melhor Vx / melhor Vy
(a partir de todos_resultados.csv). Modelos que divergiram (inf/1e10+) são
mantidos na tabela (sinalizados) e descartados no boxplot/eleição."""
import os
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
CSV = os.path.join(BASE, "mineracao", "tabelas", "todos_resultados.csv")
OUT_XLSX = os.path.join(BASE, "mineracao", "tabelas", "resultados_consolidados.xlsx")
OUT_BOX = os.path.join(BASE, "mineracao", "boxplots")
OS_MAP = {"RESULTADOS_1": "PC1", "RESULTADOS-2": "PC2", "RESULTADOS-3": "PC3"}

df = pd.read_csv(CSV, sep=";", decimal=",")
df["PC"] = df["PC"].map(OS_MAP).fillna(df["PC"])

# ---- Resumo por modelo (agrega as 4 pistas) ----
def fim_portable(v):
    try:
        v = float(v)
        return np.isnan(v) or np.isinf(v) or v >= 1e10
    except (TypeError, ValueError):
        return True

res = []
for (pc, tid, modelo), g in df.groupby(["PC", "ID", "modelo"]):
    vx = g["Vx"].astype(float)
    vy = g["Vy"].astype(float)
    gok = g[~g["Vx"].astype(float).apply(fim_portable) & ~g["Vy"].astype(float).apply(fim_portable)]
    res.append(dict(
        PC=pc, ID=tid, modelo=modelo, tipo=g["tipo"].iloc[0], metric=g["metric"].iloc[0],
        nDelays=g["nDelays"].iloc[0], nTerms=g["nTerms"].iloc[0], maxHeight=g["maxHeight"].iloc[0],
        n_pistas=len(g),
        Vx_media=gok["Vx"].mean() if not gok.empty else np.nan,
        Vy_media=gok["Vy"].mean() if not gok.empty else np.nan,
        Vx_max=g["Vx"].max(), Vy_max=g["Vy"].max(),
        divergente=bool(g["divergiu"].any()) or gok.empty,
    ))
res_modelo = pd.DataFrame(res)

# Para eleição usamos só RMSE e não-divergentes
eleg = res_modelo[(res_modelo["metric"] == "RMSE") & (~res_modelo["divergente"])].copy()
eleg["score"] = eleg["Vx_media"] + eleg["Vy_media"]

best_vx = eleg.loc[eleg["Vx_media"].idxmin()]
best_vy = eleg.loc[eleg["Vy_media"].idxmin()]
best_combined = eleg.loc[eleg["score"].idxmin()]

# ---- Excel ----
with pd.ExcelWriter(OUT_XLSX, engine="openpyxl") as w:
    res_modelo.to_excel(w, sheet_name="todos_modelos", index=False)
    eleg.to_excel(w, sheet_name="elegiveis_rmse", index=False)
    pd.DataFrame([dict(criterio="melhor_Vx", **{k: best_vx[k] for k in ["PC","ID","modelo","Vx_media","Vy_media","nDelays","nTerms","maxHeight"]}),
                  dict(criterio="melhor_Vy", **{k: best_vy[k] for k in ["PC","ID","modelo","Vx_media","Vy_media","nDelays","nTerms","maxHeight"]}),
                  dict(criterio="melhor_combinado_Vx+Vy", **{k: best_combined[k] for k in ["PC","ID","modelo","Vx_media","Vy_media","nDelays","nTerms","maxHeight"]})]
                ).to_excel(w, sheet_name="melhores", index=False)
print("Excel gerado:", OUT_XLSX)

# ---- Boxplots (só RMSE, descartando divergentes) ----
clean = res_modelo[(res_modelo["metric"] == "RMSE") & (~res_modelo["divergente"])].copy()
for chan, col in [("Vx", "Vx_media"), ("Vy", "Vy_media")]:
    fig, ax = plt.subplots(figsize=(10, 6))
    data = [clean[clean["PC"] == p][col].dropna().values for p in ["PC1","PC2","PC3"]]
    bp = ax.boxplot(data, labels=["PC1","PC2","PC3"], patch_artist=True)
    colors = ["#8ecae6", "#ffb703", "#90be6d"]
    for patch, c in zip(bp["boxes"], colors):
        patch.set_facecolor(c)
    ax.set_title(f"Distribuição do RMSE_{chan} médio (nas 4 pistas) — modelos RMSE, sem divergentes")
    ax.set_ylabel(f"RMSE_{chan} médio")
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    out = os.path.join(OUT_BOX, f"boxplot_RMSE_{chan}_por_PC.png")
    fig.savefig(out, dpi=120)
    plt.close(fig)
    print("Boxplot:", out)

# ---- Console: melhores ----
print("\n===== MELHORES (RMSE, média das 4 pistas, sem divergentes) =====")
def show(tag, r):
    print(f"[{tag}] PC={r['PC']} ID={r['ID']} {r['modelo']}  "
          f"Vx_media={r['Vx_media']:.4f} Vy_media={r['Vy_media']:.4f} "
          f"({r.get('nDelays')}, nT={r.get('nTerms')}, mH={r.get('maxHeight')})")
show("MELHOR Vx", best_vx)
show("MELHOR Vy", best_vy)
show("MELHOR Vx+Vy (soma)", best_combined)

# ---- Resumo de divergentes ----
nd = res_modelo[res_modelo["divergente"]]
print(f"\nModelos divergentes (inf/1e10+, sinalizados, fora do boxplot/eleição): {len(nd)}")
print(nd.groupby(["PC","tipo"]).size().to_string())