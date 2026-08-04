# RESULTADOS — Anatomy of the 3 Output Folders

## What the system is

`TrainingMGGP_LOOP.ipynb` is a **Multigene Genetic Programming (MGGP)** training loop
for NARX/MIMO models. It predicts the outputs (Vx, Vy) of a bicycle/vehicle controller.

The flow works like this:

1. Reads `controle_treinamentos.xlsx` (the "master" sheet) and grabs the first task
   where `Status = PENDENTE`.
2. Builds the MGGP params (`parametros_mggp`) using `nTerms` and `maxHeight` from the sheet.
3. Runs a "factory": trains up to 10 models per task. Only models that pass validation
   (RMSE < 100) are saved. Progress is tracked in a per-task `checklist_local.xlsx`.
4. Validates the 10 models on the Wang tracks (21, 22, 31, 81), saves PNG plots and a
   `relatorio_validacao_rmse.csv`.
5. Marks the task ID as `Concluído` in the master sheet and moves to the next one.

## The 3 folders = 3 computers

There are 3 result folders because the same loop is run on **3 different computers**.
Each computer runs the **same notebook**, but with **fixed parameters that differ** per
machine (and with its own local file paths, pointing to `C:\IC_alex\...` and a local
`RESULTADOS` folder). They all consume the same master control sheet.

| Folder | Computer |
|--------|----------|
| `RESULTADOS_1` | PC 1 |
| `RESULTADOS-2` | PC 2 |
| `RESULTADOS-3` | PC 3 |

## The `nDelays` split

The main parameter that changes between computers is `nDelays` (how many time-delay lags
are used for the input regressors).

### As planned (the idea)

| Computer | nDelays |
|----------|---------|
| PC 1 | `[1]` |
| PC 2 | `[1, 2, 5, 10]` |
| PC 3 | `[1, 2, 5, 10, 25, 50]` |

### As actually recorded (from each `parametros_utilizados.csv`)

| Folder | nDelays used | evaluationMode |
|--------|--------------|----------------|
| `RESULTADOS_1` (PC1) | `[1]` (Tasks 1-19, 49) then `[1, 2, 5, 10]` (Tasks 20-48) | RMSE |
| `RESULTADOS-2` (PC2) | `[1, 2, 5, 10, 25, 50]` (Tasks 1-10) then `[1, 2, 5, 10]` (Tasks 11-49) | MAPE at first, then RMSE |
| `RESULTADOS-3` (PC3) | `[1, 2, 5, 10]` (all tasks) | RMSE |

> Note: in practice the computers changed `nDelays` (and PC2 also started with `MAPE`)
> across batches. So the values above show how the field evolved over time, not a fixed
> value per machine.

## What is inside each `Treinamento_<ID>/` folder

| Item | Meaning |
|------|---------|
| `parametros_utilizados.csv` | The exact MGGP params used for this training task |
| `modelo_rmse_*.pkl` | Saved serialized model (best models only) |
| `modelo_rmse_*.png` | Validation plot (real vs predicted, Vx and Vy) per Wang track |
| `relatorio_validacao_rmse.csv` | RMSE results (Vx, Vy, mean) per model and track |
| `checklist_local.xlsx` | Local checkpoint of the 20 steps (10 train + 10 validate), so it can resume if the power goes out |
| `TRAINING/` | Folder that holds the saved `.pkl` models |

## Key takeaway

Each computer uses **fixed hyperparameters** (`nDelays`, and possibly `evaluationMode`).
So when comparing results, filter by the `nDelays`/`evaluationMode` in the CSV, **not by
the folder name** — because the parameter values changed during the batches (e.g. PC1 and
PC2 also produced `[1, 2, 5, 10]` runs, and PC2 used MAPE at the start).