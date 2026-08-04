import os
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

BASE = r"C:\Users\beatl\OneDrive\Área de Trabalho\TreinamentoMGGP_2_0"
CSV = os.path.join(BASE, "mineracao", "tabelas", "todos_resultados.csv")
TAB = os.path.join(BASE, "mineracao", "tabelas")
BOX = os.path.join(BASE, "mineracao", "boxplots")
os.makedirs(BOX, exist_ok=True)

PCS = {"RESULTADOS-2": "PC2", "RESULTADOS-3": "PC3"}

df = pd.read_csv(CSV, sep=";", decimal=",")
df = df[df["metric"] == "RMSE"].copy()

def bad(v):
    try:
        v = float(v)
        return np.isnan(v) or np.isinf(v) or abs(v) >= 1e10
    except Exception:
        return True

df["Vx"] = df["Vx"].astype(float)
df["Vy"] = df["Vy"].astype(float)

rows = []
for pc, pcname in PCS.items():
    sub = df[df["PC"] == pc]
    for (tid,), g in sub.groupby(["ID"]):
        ok = ~g["divergiu"].astype(bool)
        vx = g.loc[ok, "Vx"]
        vy = g.loc[ok, "Vy"]
        rows.append({
            "PC": pc, "PC_nome": pcname, "ID": tid,
            "nDelays": g["nDelays"].iloc[0],
            "nTerms": g["nTerms"].iloc[0],
            "maxHeight": g["maxHeight"].iloc[0],
            "n_pistas": len(g),
            "RMSE_Vx_medio": vx.mean() if len(vx) else np.nan,
            "RMSE_Vy_medio": vy.mean() if len(vy) else np.nan,
            "divergiu": bool(g["divergiu"].any()),
        })

tab = pd.DataFrame(rows)
tab.to_csv(os.path.join(TAB, "rmse_medio_por_treinamento.csv"), sep=";", index=False,
           encoding="utf-8-sig")

print("Tabela gerada:", len(tab), "linhas")

for pc, pcname in PCS.items():
    t = tab[tab["PC"] == pc]
    t_ok = t[~t["divergiu"]]
    vx = t_ok["RMSE_Vx_medio"].dropna()
    vy = t_ok["RMSE_Vy_medio"].dropna()
    print(f"\n[{pcname}] treinamentos: {len(t)}  | sem divergência: {len(t_ok)}")
    print(f"  Vx médio: mediana={vx.median():.4f} | n={len(vx)}")
    print(f"  Vy médio: mediana={vy.median():.4f} | n={len(vy)}")

    fig, axes = plt.subplots(1, 2, figsize=(20, 12))
    for ax, col, title in zip(axes, ["RMSE_Vx_medio", "RMSE_Vy_medio"], ["RMSE Vx médio", "RMSE Vy médio"]):
        vals = t_ok[col].dropna()
        bp = ax.boxplot(vals, vert=True, widths=0.45,
                        patch_artist=True, showfliers=True,
                        flierprops=dict(marker="o", markersize=6, markerfacecolor="none", markeredgecolor="tomato"))
        for patch in bp["boxes"]:
            patch.set_facecolor("#9ecae1" if col.endswith("medio") else "#fdcc8a")
        ax.set_title(f"{pcname} · {title} ({len(vals)} treinamentos)", fontsize=18)
        ax.set_ylabel("RMSE", fontsize=16)
        ax.set_xticks([1]); ax.set_xticklabels([title], fontsize=14)
        ax.grid(axis="y", ls="--", alpha=0.4)
        ax.tick_params(labelsize=12)
    fig.suptitle(f"Boxplot RMSE médio — {pcname} (sem divergentes)", fontsize=22)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    out = os.path.join(BOX, f"boxplot_RMSE_{pcname}.png")
    fig.savefig(out, dpi=300, bbox_inches="tight")
    plt.close(fig)
    print("  salvo:", out)