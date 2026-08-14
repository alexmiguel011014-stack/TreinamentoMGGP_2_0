"""
Configuração central: quais treinamentos são válidos em cada pasta RESULTADOS-N.

Regra de validade: cada pasta (= 1 PC) deveria ter usado UM único nDelays fixo em
todos os seus treinamentos. Alguns treinamentos desviaram do valor correto por
erro de configuração na máquina; esses ficam marcados como inválidos e são
excluídos da análise.

Quando você rodar mais treinamentos e quiser incluí-los na próxima atualização do
relatório, edite apenas este arquivo:
  - Se um novo treinamento aparecer com o nDelays correto da pasta, ele entra
    automaticamente (o parser detecta pelo valor de nDelays, não por número fixo).
  - Se quiser reclassificar algum treinamento específico (ex: um que rodou com
    nDelays certo mas teve outro problema), adicione o número dele em
    EXCLUSOES_MANUAIS.

Última atualização: 2026-08-13
"""

# nDelays correto (esperado) de cada pasta/PC.
NDELAYS_ESPERADO = {
    "RESULTADOS-1": "[1]",
    "RESULTADOS-2": "[1, 2, 5, 10, 25, 50]",
    "RESULTADOS-3": "[1, 2, 5, 10]",
}

# Treinamentos excluídos manualmente por outros motivos além do nDelays
# (ex: falha de execução, arquivo corrompido, etc). Formato: {"RESULTADOS-1": [40, 41]}
EXCLUSOES_MANUAIS = {}

# Treinamentos conhecidos como ausentes (não é erro, só não existem no disco)
AUSENTES_CONHECIDOS = {
    "RESULTADOS-3": [6],
}
