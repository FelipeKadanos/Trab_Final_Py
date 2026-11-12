import base64
import csv
import io
import os
import tempfile
import unicodedata

os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib-cache"))
import matplotlib
matplotlib.use("Agg") # Permite criar os graficos sem abrir uma janela.
import matplotlib.pyplot as plt
import pandas as pd


COLUNAS_OBRIGATORIAS = [
    "Year", "Month", "DayofWeek", "Reporting_Airline", "CRSDepTime",
    "Distance", "Cancelled", "Diverted", "ArrDelay",
]

NOMES_COLUNAS = {
    "year": "Year", "ano": "Year",
    "month": "Month", "mes": "Month",
    "dayofweek": "DayofWeek", "diadasemana": "DayofWeek",
    "reportingairline": "Reporting_Airline", "companhia": "Reporting_Airline", "companhiaaerea": "Reporting_Airline",
    "crsdeptime": "CRSDepTime", "horarioprevisto": "CRSDepTime", "horariopartida": "CRSDepTime",
    "distance": "Distance", "distancia": "Distance",
    "cancelled": "Cancelled", "cancelado": "Cancelled",
    "diverted": "Diverted", "desviado": "Diverted",
    "arrdelay": "ArrDelay", "atraso": "ArrDelay", "atrasochegada": "ArrDelay",
}


def _normalizar_nome_coluna(nome):
    texto = unicodedata.normalize("NFKD", str(nome)).encode("ascii", "ignore").decode("ascii")
    texto = "".join(caractere for caractere in texto.lower() if caractere.isalnum())
    return NOMES_COLUNAS.get(texto, str(nome).strip())


# Le o arquivo enviado e verifica o formato antes de iniciar a analise.
def ler_csv(arquivo):
    if arquivo is None or not arquivo.filename:
        raise ValueError("Selecione um arquivo CSV.")

    if not arquivo.filename.lower().endswith(".csv"):
        raise ValueError("O arquivo precisa ter a extensao .csv.")

    conteudo = arquivo.read()
    if not conteudo:
        raise ValueError("O arquivo CSV esta vazio.")

    try:
        texto = conteudo.decode("utf-8-sig")
    except UnicodeDecodeError:
        # Alguns arquivos salvos pelo Excel no Windows utilizam esta codificacao.
        texto = conteudo.decode("latin-1")

    try:
        linhas = texto.splitlines()
        if linhas and linhas[0].strip().lower() in ["sep=,", "sep=;", "sep=\\t"]:
            texto = "\n".join(linhas[1:])

        # Testamos os separadores aceitos e usamos aquele que encontrou mais colunas.
        tentativas = []
        for separador in [",", ";", "\t"]:
            try:
                tentativas.append(pd.read_csv(io.StringIO(texto), sep=separador))
            except (pd.errors.ParserError, pd.errors.EmptyDataError):
                pass
        if not tentativas:
            raise ValueError
        dados = max(tentativas, key=lambda tentativa: len(tentativa.columns))
        dados = dados.rename(columns={coluna: _normalizar_nome_coluna(coluna) for coluna in dados.columns})
    except ValueError:
        raise ValueError("Nao foi possivel ler o CSV. Use virgula, ponto e virgula ou tabulacao como separador.")

    colunas_ausentes = [coluna for coluna in COLUNAS_OBRIGATORIAS if coluna not in dados.columns]
    if colunas_ausentes:
        encontradas = ", ".join(str(coluna) for coluna in dados.columns)
        raise ValueError(
            "Colunas obrigatorias ausentes: " + ", ".join(colunas_ausentes)
            + ". Colunas encontradas no arquivo: " + encontradas
        )

    return dados


# Converte um horario HHMM para minutos desde a meia-noite.
def horario_para_minutos(horario):
    try:
        # O formulario envia no formato 13h30 e o CSV utiliza 1330.
        if isinstance(horario, str):
            horario = horario.strip().lower().replace("h", "").replace(":", "")
        horario = int(float(horario))
    except (TypeError, ValueError):
        return None

    horas = horario // 100
    minutos = horario % 100
    if horas < 0 or horas > 23 or minutos < 0 or minutos > 59:
        return None

    return horas * 60 + minutos


# Limpa uma copia dos dados. O arquivo original enviado nunca e alterado.
def limpar_dados(dados):
    dados_limpos = dados.copy()
    quantidade_inicial = len(dados_limpos)
    tipos = {coluna: str(tipo) for coluna, tipo in dados_limpos.dtypes.items()}
    ausentes = {coluna: int(valor) for coluna, valor in dados_limpos.isnull().sum().items() if valor > 0}
    duplicatas = int(dados_limpos.duplicated().sum())

    # A duplicata so e removida quando todas as colunas do registro sao iguais.
    dados_limpos = dados_limpos.drop_duplicates()

    colunas_numericas = ["Year", "Month", "DayofWeek", "CRSDepTime", "Distance", "Cancelled", "Diverted", "ArrDelay"]
    for coluna in colunas_numericas:
        dados_limpos[coluna] = pd.to_numeric(dados_limpos[coluna], errors="coerce")

    dados_limpos["Reporting_Airline"] = dados_limpos["Reporting_Airline"].astype("string").str.strip()

    # Voos cancelados ou desviados nao possuem uma chegada normal para avaliar.
    dados_limpos = dados_limpos[(dados_limpos["Cancelled"] == 0) & (dados_limpos["Diverted"] == 0)]
    dados_limpos = dados_limpos.dropna(subset=COLUNAS_OBRIGATORIAS)
    dados_limpos = dados_limpos[dados_limpos["Reporting_Airline"] != ""]
    dados_limpos = dados_limpos[dados_limpos["Year"] >= 1987]
    dados_limpos = dados_limpos[dados_limpos["Month"].between(1, 12)]
    dados_limpos = dados_limpos[dados_limpos["DayofWeek"].between(1, 7)]
    dados_limpos = dados_limpos[dados_limpos["Distance"] > 0]

    dados_limpos["HorarioMinutos"] = dados_limpos["CRSDepTime"].apply(horario_para_minutos)
    dados_limpos = dados_limpos.dropna(subset=["HorarioMinutos"])
    dados_limpos["Atrasado"] = (dados_limpos["ArrDelay"] >= 15).astype(int)

    if dados_limpos.empty:
        raise ValueError("Nenhum voo valido permaneceu depois da limpeza dos dados.")

    diagnostico = {
        "quantidade_inicial": quantidade_inicial,
        "quantidade_final": len(dados_limpos),
        "colunas": len(dados.columns),
        "duplicatas": duplicatas,
        "ausentes": ausentes,
        "tipos": tipos,
        "removidos": quantidade_inicial - len(dados_limpos),
    }
    return dados_limpos, diagnostico


def _grafico_base64():
    arquivo = io.BytesIO()
    plt.tight_layout()
    plt.savefig(arquivo, format="png", dpi=110)
    plt.close()
    arquivo.seek(0)
    return base64.b64encode(arquivo.getvalue()).decode("utf-8")


# Cria os tres graficos exigidos e uma interpretacao baseada no CSV enviado.
def criar_graficos(dados):
    graficos = []

    plt.figure(figsize=(8, 4))
    plt.hist(dados["ArrDelay"].clip(-60, 180), bins=30, color="steelblue", edgecolor="black")
    plt.title("Distribuicao do atraso na chegada")
    plt.xlabel("Atraso em minutos (valores entre -60 e 180)")
    plt.ylabel("Quantidade de voos")
    mediana = dados["ArrDelay"].median()
    graficos.append({
        "imagem": _grafico_base64(),
        "interpretacao": f"A mediana do atraso foi {mediana:.1f} minutos. Valores negativos representam chegadas antecipadas.",
    })

    por_companhia = dados.groupby("Reporting_Airline")["Atrasado"].agg(["mean", "count"])
    companhias_com_amostra = por_companhia[por_companhia["count"] >= 5]
    if not companhias_com_amostra.empty:
        por_companhia = companhias_com_amostra
    por_companhia = por_companhia.sort_values("mean", ascending=False)
    plt.figure(figsize=(8, 4))
    (por_companhia["mean"] * 100).plot(kind="bar", color="darkorange")
    plt.title("Percentual de atrasos por companhia")
    plt.xlabel("Companhia")
    plt.ylabel("Voos atrasados (%)")
    plt.xticks(rotation=45, ha="right")
    companhia_maior = por_companhia.index[0]
    percentual_maior = por_companhia.iloc[0]["mean"] * 100
    graficos.append({
        "imagem": _grafico_base64(),
        "interpretacao": f"Entre as companhias com pelo menos 5 voos, {companhia_maior} teve o maior percentual de atrasos: {percentual_maior:.1f}%.",
    })

    faixas = pd.cut(dados["HorarioMinutos"], bins=[0, 360, 720, 1080, 1440], right=False, labels=["Madrugada", "Manha", "Tarde", "Noite"])
    por_horario = dados.groupby(faixas, observed=False)["Atrasado"].mean() * 100
    plt.figure(figsize=(8, 4))
    por_horario.plot(kind="bar", color="seagreen")
    plt.title("Percentual de atrasos por horario previsto")
    plt.xlabel("Periodo do dia")
    plt.ylabel("Voos atrasados (%)")
    plt.xticks(rotation=0)
    faixa_maior = por_horario.idxmax()
    graficos.append({
        "imagem": _grafico_base64(),
        "interpretacao": f"O periodo com maior percentual de atrasos foi {faixa_maior}, com {por_horario.max():.1f}%.",
    })

    return graficos


def resumir_dados(dados):
    return {
        "voos": len(dados),
        "companhias": dados["Reporting_Airline"].nunique(),
        "atrasados": int(dados["Atrasado"].sum()),
        "percentual_atrasados": dados["Atrasado"].mean() * 100,
        "distancia_media": dados["Distance"].mean(),
        "atraso_medio": dados["ArrDelay"].mean(),
    }
