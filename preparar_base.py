from pathlib import Path
from zipfile import ZipFile
from io import BytesIO

import pandas as pd
from dados import COLUNAS, carregar_e_limpar_csv

# Localiza o ZIP a partir da pasta do script, sem depender do computador.
PASTA = Path(__file__).resolve().parent
ARQUIVO_ZIP = PASTA / "data" / "brutos" / "bts_2024_01.zip"

# Lê o CSV diretamente do ZIP, preservando o arquivo original.
with ZipFile(ARQUIVO_ZIP) as zip_voos:
    nome_csv = "On_Time_Reporting_Carrier_On_Time_Performance_(1987_present)_2024_1.csv"

    with zip_voos.open(nome_csv) as csv_voos:
        dados = pd.read_csv(csv_voos, low_memory=False)

# Confere se todos os registros pertencem ao período escolhido.
periodo_correto = (
    (dados["Year"] == 2024) & (dados["Month"] == 1)
)

if not periodo_correto.all():
    raise ValueError("A base deve conter apenas voos de janeiro de 2024!")

# Seleciona as oito informações definidas no contrato do grupo.
colunas = [
    "Reporting_Airline",
    "Month",
    "DayOfWeek",
    "CRSDepTime",
    "Distance",
    "ArrDelay",
    "Cancelled",
    "Diverted",
]

dados = dados[colunas]

# Mapeia os nomes originais da BTS para os nomes usados no projeto.
nomes = {
    "Reporting_Airline": "companhia",
    "Month": "mes",
    "DayOfWeek": "dia_semana",
    "CRSDepTime": "hora_prevista",
    "Distance": "distancia",
    "ArrDelay": "atraso_chegada",
    "Cancelled": "cancelado",
    "Diverted": "desviado",
}

dados = dados.rename(columns=nomes)

csv_memoria = BytesIO(dados.to_csv(index=False).encode("utf-8"))

dados, relatorio = carregar_e_limpar_csv(csv_memoria)

print("Registros antes da limpeza:", relatorio["linhas_antes"])

for remocao in relatorio["remocoes"]:
    print(remocao["motivo"], ":", remocao["quantidade"])

print("Registros após a limpeza:", relatorio["linhas_depois"])

print("\nVoos por classe de atraso:")
print(dados["atrasou"].value_counts().sort_index())

# Sorteia 20 mil registros; a semente fixa permite reproduzir a amostra.
amostra = dados.sample(n=20000, random_state=42)
print("\nVoos na amostra:", len(amostra))

atrasou_amostra = amostra["atrasou"]

if atrasou_amostra.nunique() != 2:
    raise ValueError("A amostra precisa conter voos das duas classes de atraso!")

print("Classes na amostra:")
print(atrasou_amostra.value_counts().sort_index())

# Salva as oito colunas sem incluir o índice do Pandas.
arquivo_csv = PASTA / "data" / "voos.csv"
amostra[COLUNAS].to_csv(
    arquivo_csv,
    index=False,
    encoding="utf-8",
)
print("\nBase salva em:", arquivo_csv)

# Reabre o CSV para conferir a quantidade de linhas e os nomes das colunas.
conferencia = pd.read_csv(arquivo_csv)
print("\nLinhas no CSV salvo:", len(conferencia))
print("Colunas no CSV salvo:", conferencia.columns.tolist())