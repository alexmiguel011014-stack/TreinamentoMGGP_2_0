"""
Revalida em RMSE os modelos .pkl já treinados, gerando/sobrescrevendo o
relatorio_validacao_rmse.csv de cada Treinamento_N indicado.

Por que existe: RESULTADOS-2/Treinamento_4 a Treinamento_10 têm um
relatorio_validacao.csv com colunas MAPE_Vx/MAPE_Vy (versão antiga do pipeline),
em vez de RMSE_Vx/RMSE_Vy. Os modelos .pkl (TRAINING/modelo_rmse_*.pkl) já
existem e já estão treinados — não é preciso re-treinar, só rerodar a etapa de
validação em massa (carrega o modelo + roda predict() nas 4 pistas Wang),
usando exatamente a mesma lógica do TrainingMGGP_LOOP.ipynb, célula "MOTOR
PRINCIPAL", passo 4.

Uso:
    cd TreinamentoMGGP_2_0
    python Relatorio_resultados/scripts/revalidar_rmse.py

Ajuste TREINAMENTOS_PARA_REVALIDAR abaixo se quiser rodar em outras pastas/IDs.
"""

import gc
import os
import sys
from pathlib import Path

import dill
import numpy as np
import pandas as pd

# Garante que "from src.mggp import MGGP" funcione rodando de qualquer lugar
PROJ_DIR = Path(__file__).resolve().parent.parent.parent  # TreinamentoMGGP_2_0/
sys.path.insert(0, str(PROJ_DIR))

from src.mggp import MGGP  # noqa: E402  (necessário para o unpickle do dill)
from src.base import Element  # noqa: E402

# Registra as classes dinâmicas do DEAP (creator.Individual, creator.FitnessMin,
# creator.Program) antes de desserializar os .pkl. No notebook original isso já
# existia na sessão por causa do treinamento; aqui precisa ser feito manualmente.
_ = Element(weights=(-1,), nDelays=[1], nInputs=5, nOutputs=2, nTerms=1,
            maxHeight=4, mode="MIMO", operators=['add', 'subtraction', 'mul'])

# =============================================================================
# CONFIGURAÇÃO
# =============================================================================

# Pasta com as planilhas de pista (Wang). Ajuste se necessário.
DATABASE_DIR = PROJ_DIR.parent / "Database"

PISTAS_VALIDACAO_MASSA = {
    "Wang 2.1 (Treino)": DATABASE_DIR / "wang21dv_bic_MGGP.xlsx",
    "Wang 2.2 (Validação)": DATABASE_DIR / "wang22dv_bic_MGGP.xlsx",
    "Wang 3.1 (Teste A)": DATABASE_DIR / "wang31dv_bic_MGGP.xlsx",
    "Wang 8.1 (Teste B)": DATABASE_DIR / "wang81dv_bic_MGGP.xlsx",
}

EVALUATION_TYPE_TEST = "MShooting"  # igual ao usado no treino original
K = 300

# Quais Treinamento_N revalidar. Edite esta lista conforme necessário.
TREINAMENTOS_PARA_REVALIDAR = [
    ("RESULTADOS-2", n) for n in range(4, 11)  # Treinamento_4 a Treinamento_10
]


# =============================================================================
# FUNÇÕES
# =============================================================================

def carregar_dados_bicicleta(caminho_arquivo):
    df = pd.read_excel(caminho_arquivo, header=None)
    u = df.iloc[:, [14, 2, 22, 23, 11]].values
    y_raw = df.iloc[:, [18, 17]].values
    return u, y_raw


def calcular_rmse(y_true, y_pred):
    return np.sqrt(np.mean((y_true - y_pred) ** 2))


def revalidar_treinamento(pasta, t_id):
    pasta_treino = PROJ_DIR / pasta / f"Treinamento_{t_id}"
    pasta_training = pasta_treino / "TRAINING"

    if not pasta_training.exists():
        print(f"[PULAR] {pasta}/Treinamento_{t_id}: pasta TRAINING não existe")
        return None

    resultados = []

    for i in range(1, 11):
        nome_arquivo = f"modelo_mape_{i}.pkl"
        caminho_modelo = pasta_training / nome_arquivo
        if not caminho_modelo.exists():
            continue

        try:
            with open(caminho_modelo, "rb") as f:
                modelo = dill.load(f)
        except Exception as e:
            print(f"  [ERRO] {nome_arquivo}: falha ao carregar ({e})")
            continue

        for nome_pista, caminho_pista in PISTAS_VALIDACAO_MASSA.items():
            if not Path(caminho_pista).exists():
                print(f"  [ERRO] planilha não encontrada: {caminho_pista}")
                continue

            u_raw, y_raw = carregar_dados_bicicleta(caminho_pista)
            try:
                args_val = (K, y_raw, u_raw) if EVALUATION_TYPE_TEST == "MShooting" else (y_raw, u_raw)
                yp_raw, yd_raw = modelo.predict(EVALUATION_TYPE_TEST, *args_val)
                min_len = min(len(yd_raw), len(yp_raw))
                yd_raw, yp_raw = yd_raw[:min_len], yp_raw[:min_len]

                rmse_vx = calcular_rmse(yd_raw[:, 0], yp_raw[:, 0])
                rmse_vy = calcular_rmse(yd_raw[:, 1], yp_raw[:, 1])
                rmse_medio = (rmse_vx + rmse_vy) / 2
            except Exception as e:
                print(f"  [ERRO] {nome_arquivo} / {nome_pista}: {e}")
                rmse_vx, rmse_vy, rmse_medio = 999.9, 999.9, 999.9

            resultados.append({
                "Modelo": nome_arquivo,
                "Pista": nome_pista,
                "RMSE_Vx": round(rmse_vx, 4),
                "RMSE_Vy": round(rmse_vy, 4),
                "RMSE_Médio": round(rmse_medio, 4),
            })

        del modelo
        gc.collect()

    if not resultados:
        print(f"[VAZIO] {pasta}/Treinamento_{t_id}: nenhum modelo revalidado")
        return None

    df_novo = pd.DataFrame(resultados)
    caminho_csv_saida = pasta_treino / "relatorio_validacao_rmse.csv"
    df_novo.to_csv(caminho_csv_saida, index=False, sep=";", decimal=",")
    print(f"[OK] {pasta}/Treinamento_{t_id}: {len(resultados)} linhas salvas em {caminho_csv_saida.name}")
    return caminho_csv_saida


def main():
    if not DATABASE_DIR.exists():
        print(f"ERRO: pasta de dados não encontrada: {DATABASE_DIR}")
        print("Ajuste DATABASE_DIR no topo do script.")
        return

    print(f"Base de dados: {DATABASE_DIR}")
    print(f"Revalidando {len(TREINAMENTOS_PARA_REVALIDAR)} treinamentos...\n")

    for pasta, t_id in TREINAMENTOS_PARA_REVALIDAR:
        revalidar_treinamento(pasta, t_id)

    print("\nConcluído. Rode coletar_dados.py de novo para atualizar o dataset consolidado.")


if __name__ == "__main__":
    main()
