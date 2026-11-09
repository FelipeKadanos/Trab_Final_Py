from pathlib import Path
from zipfile import ZipFile

import pandas as pd

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

# Mostra o diagnóstico inicial, antes de remover registros.
print(dados.head().to_string(index=False))
print("Total de voos: ", len(dados))

print("\nTipos das colunas:")
print(dados.dtypes)
print("\nValores ausentes por coluna:")
print(dados.isna().sum())
print("\nVoos cancelados:")
print(dados["cancelado"].value_counts(dropna=False))
print("\nVoos desviados:")
print(dados["desviado"].value_counts(dropna=False))

sem_atraso = dados["atraso_chegada"].isna()
fora_do_recorte = (
    (dados["cancelado"] == 1) | (dados["desviado"] == 1)
)

print(
    "\nVoos sem atraso informado que não foram cancelados nem desviados:",
    (sem_atraso & ~fora_do_recorte).sum(),
)

# Remove repetições nas oito colunas.
# Limitação: voos diferentes podem ter os mesmos valores nesse recorte.
duplicatas = dados.duplicated()
print("\nRegistros dupliados nas oito colunas: ", duplicatas.sum())

antes = len(dados)
dados = dados.drop_duplicates().copy()
removidos = antes - len(dados)
print("\nDuplicatas removidas:", removidos)
print("Voos restantes:", len(dados))

invalidos = (
    ~dados["cancelado"].isin([0,1]) | ~dados["desviado"].isin([0,1])
)
print("\nRegistros com indicadores inválidos:", invalidos.sum())

# Exclui cancelados e, depois, desviados, contando cada remoção uma só vez.
antes = len(dados)
dados = dados[dados["cancelado"] == 0].copy()
removidos = antes - len(dados)
print("\nVoos cancelados removidos:", removidos)
print("Voos restantes:", len(dados))

antes = len(dados)
dados = dados[dados["desviado"] == 0 ].copy()
removidos = antes - len(dados)
print("\nVoos desviados removidos:", removidos)
print("Voos restantes:", len(dados))

ausentes = dados["atraso_chegada"].isna().sum()
print("\nVoos registrados sem atraso informado:", ausentes)

# Verifica os limites das entradas; o horário usa o formato HHMM.
horas = dados["hora_prevista"]
horarios_validos = (
    (
        horas.between(0, 2359) & (horas % 100 < 60) & (horas % 1 == 0)
    )
    | (horas == 2400)
)

print("\nHorários inválidos:", (~horarios_validos).sum())
print("Horários registrados como 2400:", (horas == 2400).sum())

mes_valido = (
    dados["mes"].between(1, 12) & (dados["mes"] % 1 == 0)
)

dia_valido = (
    dados["dia_semana"].between(1, 7) & (dados["dia_semana"] % 1 == 0)
)

distancia_valida = dados["distancia"].gt(0)

print("\nMeses inválidos:", (~mes_valido).sum())
print("\nDias da semana inválidos:", (~dia_valido).sum())
print("\nDistâncias inválidos:", (~distancia_valida).sum())

# Padroniza os códigos para evitar diferenças por espaços ou letras minúsculas.
dados["companhia"] = (
    dados["companhia"].str.strip().str.upper()
)

companhia_vazia = (
    dados["companhia"].isna() | dados["companhia"].eq("")
)

print("\nCompanhias vazias:", companhia_vazia.sum())

# Mantém apenas entradas válidas e com atraso de chegada conhecido.
# Não preencher atraso ausente com zero: isso inventaria uma resposta.
validos = (
    horarios_validos & mes_valido & dia_valido & distancia_valida & ~companhia_vazia & dados["atraso_chegada"].notna()
)

antes = len(dados)
dados = dados[validos].copy()

print("\nOutros registros inválidos removidos:", antes - len(dados))
dados.loc[dados["hora_prevista"] == 2400, "hora_prevista"] = 0

# Usa o atraso histórico para contar as classes; ele nunca deve entrar em X.
atrasou = (dados["atraso_chegada"] >= 15).astype(int)
print("\nVoos por classe de atraso:")
print(atrasou.value_counts().sort_index())

# Sorteia 20 mil registros; a semente fixa permite reproduzir a amostra.
amostra = dados.sample(n=20000, random_state=42)
print("\nVoos na amostra:", len(amostra))

atrasou_amostra = (
    amostra["atraso_chegada"] >= 15).astype(int)

if atrasou_amostra.nunique() != 2:
    raise ValueError("A amostra precisa conter voos das duas classes de atraso!")

print("Classes na amostra:")
print(atrasou_amostra.value_counts().sort_index())

# Salva as oito colunas sem incluir o índice do Pandas.
arquivo_csv = PASTA / "data" / "voos.csv"
amostra.to_csv(
    arquivo_csv,
    index=False,
    encoding="utf-8",
)
print("\nBase salva em:", arquivo_csv)

# Reabre o CSV para conferir a quantidade de linhas e os nomes das colunas.
conferencia = pd.read_csv(arquivo_csv)
print("\nLinhas no CSV salvo:", len(conferencia))
print("Colunas no CSV salvo:", conferencia.columns.tolist())