"""
Gera gráficos e boxplots a partir de dados_consolidados.csv e ranking_geral.csv.

Saídas em Relatorio_resultados/graficos/:
  1. boxplot_por_pasta.png          -> RMSE médio do modelo, por pasta (=por nDelays)
  2. boxplot_por_pista.png          -> RMSE médio, por pista de validação
  3. heatmap_nterms_maxheight.png   -> RMSE médio (heatmap) por combinação nTerms x maxHeight
  4. evolucao_treinamento.png       -> RMSE médio do modelo ao longo dos treinamentos (ordem de execução), por pasta
  5. comparacao_vx_vy.png           -> dispersão RMSE_Vx vs RMSE_Vy, colorido por pasta (todos os modelos)
  6. comparacao_vx_vy_top10.png     -> dispersão RMSE_Vx vs RMSE_Vy, só dos 10 melhores modelos
  7. top10_modelos.png              -> barras horizontais dos 10 melhores modelos

Rode depois de coletar_dados.py e gerar_tabelas.py.
"""

import csv
from collections import defaultdict
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np

TAB_DIR = Path(__file__).resolve().parent.parent / "tabelas"
FIG_DIR = Path(__file__).resolve().parent.parent / "graficos"

CORES_PASTA = {
    "RESULTADOS-1": "#4C72B0",
    "RESULTADOS-2": "#DD8452",
    "RESULTADOS-3": "#55A868",
}


def carregar_csv(nome):
    with open(TAB_DIR / nome, encoding="utf-8") as fh:
        return list(csv.DictReader(fh))


def boxplot_por_pasta(ranking):
    grupos = defaultdict(list)
    for r in ranking:
        grupos[r["pasta"]].append(float(r["rmse_medio_modelo"]))

    pastas = sorted(grupos.keys())
    dados = [grupos[p] for p in pastas]
    labels = [f"{p}\n(n={len(grupos[p])})" for p in pastas]

    fig, ax = plt.subplots(figsize=(8, 6))
    bp = ax.boxplot(dados, labels=labels, patch_artist=True, showmeans=True)
    for patch, pasta in zip(bp["boxes"], pastas):
        patch.set_facecolor(CORES_PASTA.get(pasta, "#888888"))
        patch.set_alpha(0.7)
    ax.set_ylabel("RMSE médio do modelo (4 pistas)")
    ax.set_title("Distribuição de RMSE por pasta (nDelays)")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "boxplot_por_pasta.png", dpi=150)
    plt.close(fig)


def boxplot_por_pista(dados_consolidados):
    grupos = defaultdict(list)
    for l in dados_consolidados:
        grupos[l["pista"]].append(float(l["rmse_medio"]))

    ordem = ["Wang 2.1 (Treino)", "Wang 2.2 (Validação)", "Wang 3.1 (Teste A)", "Wang 8.1 (Teste B)"]
    pistas = [p for p in ordem if p in grupos]
    dados = [grupos[p] for p in pistas]

    fig, ax = plt.subplots(figsize=(9, 6))
    bp = ax.boxplot(dados, labels=pistas, patch_artist=True, showmeans=True)
    for patch in bp["boxes"]:
        patch.set_facecolor("#8172B3")
        patch.set_alpha(0.7)
    ax.set_ylabel("RMSE médio (Vx, Vy)")
    ax.set_title("Distribuição de RMSE por pista de validação")
    ax.grid(axis="y", linestyle=":", alpha=0.5)
    plt.xticks(rotation=15, ha="right")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "boxplot_por_pista.png", dpi=150)
    plt.close(fig)


def heatmap_nterms_maxheight(resumo):
    nterms_vals = sorted({int(r["nTerms"]) for r in resumo})
    maxh_vals = sorted({int(r["maxHeight"]) for r in resumo})

    grade = np.full((len(nterms_vals), len(maxh_vals)), np.nan)
    for r in resumo:
        i = nterms_vals.index(int(r["nTerms"]))
        j = maxh_vals.index(int(r["maxHeight"]))
        grade[i, j] = float(r["rmse_media"])

    fig, ax = plt.subplots(figsize=(8, 7))
    im = ax.imshow(grade, cmap="RdYlGn_r", aspect="auto")
    ax.set_xticks(range(len(maxh_vals)))
    ax.set_xticklabels(maxh_vals)
    ax.set_yticks(range(len(nterms_vals)))
    ax.set_yticklabels(nterms_vals)
    ax.set_xlabel("maxHeight")
    ax.set_ylabel("nTerms")
    ax.set_title("RMSE médio por combinação nTerms x maxHeight\n(todas as pastas juntas)")

    for i in range(len(nterms_vals)):
        for j in range(len(maxh_vals)):
            if not np.isnan(grade[i, j]):
                ax.text(j, i, f"{grade[i, j]:.2f}", ha="center", va="center",
                         color="black", fontsize=8)

    fig.colorbar(im, ax=ax, label="RMSE médio")
    fig.tight_layout()
    fig.savefig(FIG_DIR / "heatmap_nterms_maxheight.png", dpi=150)
    plt.close(fig)


def evolucao_treinamento(ranking):
    grupos = defaultdict(lambda: defaultdict(list))
    for r in ranking:
        grupos[r["pasta"]][int(r["treinamento"])].append(float(r["rmse_medio_modelo"]))

    fig, ax = plt.subplots(figsize=(12, 6))
    for pasta in sorted(grupos.keys()):
        treinos = sorted(grupos[pasta].keys())
        medias = [np.mean(grupos[pasta][t]) for t in treinos]
        ax.plot(treinos, medias, marker="o", markersize=3, label=pasta,
                color=CORES_PASTA.get(pasta, "#888888"), alpha=0.8)

    ax.set_xlabel("Treinamento (ID, ordem de execução = nTerms/maxHeight crescente)")
    ax.set_ylabel("RMSE médio dos 10 modelos")
    ax.set_title("Evolução do RMSE ao longo dos treinamentos, por pasta")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "evolucao_treinamento.png", dpi=150)
    plt.close(fig)


def comparacao_vx_vy(dados_consolidados):
    fig, ax = plt.subplots(figsize=(8, 8))
    for pasta in sorted(CORES_PASTA.keys()):
        xs = [float(l["rmse_vx"]) for l in dados_consolidados
              if l["pasta"] == pasta and float(l["rmse_vx"]) < 50 and float(l["rmse_vy"]) < 50]
        ys = [float(l["rmse_vy"]) for l in dados_consolidados
              if l["pasta"] == pasta and float(l["rmse_vx"]) < 50 and float(l["rmse_vy"]) < 50]
        ax.scatter(xs, ys, s=10, alpha=0.4, label=pasta, color=CORES_PASTA.get(pasta))

    lim = max(ax.get_xlim()[1], ax.get_ylim()[1])
    ax.plot([0, lim], [0, lim], linestyle="--", color="gray", linewidth=1, label="Vx = Vy")
    ax.set_xlabel("RMSE Vx")
    ax.set_ylabel("RMSE Vy")
    ax.set_title("RMSE Vx vs Vy, por pasta (pontos com RMSE < 50 em ambos eixos)")
    ax.legend()
    ax.grid(True, linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "comparacao_vx_vy.png", dpi=150)
    plt.close(fig)


def comparacao_vx_vy_top10(dados_consolidados, ranking):
    """Mesmo gráfico de RMSE Vx vs Vy, mas só com os pontos dos 10 melhores
    modelos do ranking (em vez de todos os ~1000 modelos). Cada modelo aparece
    com até 4 pontos (um por pista), marcados com símbolos diferentes."""
    top10 = ranking[:10]
    chaves_top10 = {(r["pasta"], r["treinamento"], r["modelo"]) for r in top10}

    def rotulo_curto(r):
        # "RESULTADOS-3" -> "R3", modelo_rmse_9.pkl -> "m9"
        pasta_curta = r["pasta"].replace("RESULTADOS-", "R")
        num_modelo = r["modelo"].replace(".pkl", "").rsplit("_", 1)[-1]
        return f"{pasta_curta}/T{r['treinamento']}/m{num_modelo} (RMSE {float(r['rmse_medio_modelo']):.4f})"

    rotulo_por_chave = {
        (r["pasta"], r["treinamento"], r["modelo"]): rotulo_curto(r)
        for r in top10
    }

    marcador_por_pista = {
        "Wang 2.1 (Treino)": "o",
        "Wang 2.2 (Validação)": "s",
        "Wang 3.1 (Teste A)": "^",
        "Wang 8.1 (Teste B)": "D",
    }

    linhas_top10 = [
        l for l in dados_consolidados
        if (l["pasta"], l["treinamento"], l["modelo"]) in chaves_top10
    ]

    # Uma cor por modelo (não por pasta, já que aqui queremos distinguir os 10)
    cmap = plt.get_cmap("tab10")
    cor_por_chave = {
        chave: cmap(i % 10)
        for i, chave in enumerate(rotulo_por_chave.keys())
    }

    fig, ax = plt.subplots(figsize=(9, 8))

    # Plota ponto a ponto para poder variar cor (por modelo) e marcador (por pista)
    for l in linhas_top10:
        chave = (l["pasta"], l["treinamento"], l["modelo"])
        pista = l["pista"]
        ax.scatter(
            float(l["rmse_vx"]), float(l["rmse_vy"]),
            s=70, alpha=0.85,
            color=cor_por_chave[chave],
            marker=marcador_por_pista.get(pista, "o"),
            edgecolors="black", linewidths=0.5,
        )

    # Legenda de cores (modelo) — um marcador "o" neutro só para identificar a cor
    handles_modelo = [
        plt.Line2D([0], [0], marker="o", linestyle="", color=cor_por_chave[chave],
                   markeredgecolor="black", markeredgewidth=0.5, markersize=8,
                   label=rotulo_por_chave[chave])
        for chave in rotulo_por_chave.keys()
    ]
    # Legenda de marcadores (pista) — em preto/cinza, só para indicar o formato
    handles_pista = [
        plt.Line2D([0], [0], marker=m, linestyle="", color="gray",
                   markeredgecolor="black", markeredgewidth=0.5, markersize=8,
                   label=pista)
        for pista, m in marcador_por_pista.items()
    ]

    xs_all = [float(l["rmse_vx"]) for l in linhas_top10]
    ys_all = [float(l["rmse_vy"]) for l in linhas_top10]
    lim = max(max(xs_all, default=1), max(ys_all, default=1)) * 1.15
    ax.plot([0, lim], [0, lim], linestyle="--", color="gray", linewidth=1)

    ax.set_xlabel("RMSE Vx")
    ax.set_ylabel("RMSE Vy")
    ax.set_title("RMSE Vx vs Vy — Top 10 melhores modelos\n(cor = modelo, forma = pista de validação)")
    ax.grid(True, linestyle=":", alpha=0.5)

    legend1 = ax.legend(handles=handles_modelo, loc="upper left", fontsize=7,
                          title="Modelo (top 10)", bbox_to_anchor=(1.02, 1.0))
    ax.add_artist(legend1)
    ax.legend(handles=handles_pista, loc="lower left", fontsize=8,
              title="Pista", bbox_to_anchor=(1.02, 0.0))

    fig.tight_layout()
    fig.savefig(FIG_DIR / "comparacao_vx_vy_top10.png", dpi=150, bbox_inches="tight")
    plt.close(fig)


def top10_modelos(ranking):
    top10 = ranking[:10]
    labels = [f"{r['pasta']}/T{r['treinamento']}/{r['modelo'].replace('.pkl','')}" for r in top10]
    valores = [float(r["rmse_medio_modelo"]) for r in top10]
    cores = [CORES_PASTA.get(r["pasta"], "#888888") for r in top10]

    fig, ax = plt.subplots(figsize=(10, 6))
    y_pos = range(len(top10))
    ax.barh(y_pos, valores, color=cores)
    ax.set_yticks(y_pos)
    ax.set_yticklabels(labels, fontsize=8)
    ax.invert_yaxis()
    ax.set_xlabel("RMSE médio do modelo")
    ax.set_title("Top 10 melhores modelos (menor RMSE)")
    for i, v in enumerate(valores):
        ax.text(v, i, f" {v:.4f}", va="center", fontsize=8)
    ax.grid(axis="x", linestyle=":", alpha=0.5)
    fig.tight_layout()
    fig.savefig(FIG_DIR / "top10_modelos.png", dpi=150)
    plt.close(fig)


def main():
    FIG_DIR.mkdir(parents=True, exist_ok=True)

    ranking = carregar_csv("ranking_geral.csv")
    resumo_nh = carregar_csv("resumo_por_nterms_maxheight.csv")
    dados = carregar_csv("dados_consolidados.csv")

    if not ranking:
        print("ranking_geral.csv vazio. Rode gerar_tabelas.py primeiro.")
        return

    boxplot_por_pasta(ranking)
    boxplot_por_pista(dados)
    heatmap_nterms_maxheight(resumo_nh)
    evolucao_treinamento(ranking)
    comparacao_vx_vy(dados)
    comparacao_vx_vy_top10(dados, ranking)
    top10_modelos(ranking)

    print(f"Gráficos gerados em: {FIG_DIR}")
    for f in sorted(FIG_DIR.glob("*.png")):
        print(f"  - {f.name}")


if __name__ == "__main__":
    main()
