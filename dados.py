import base64
import csv
import io
import os
import tempfile

# Guarda o cache dos graficos em uma pasta temporaria com permissao de escrita.
os.environ.setdefault("MPLCONFIGDIR", os.path.join(tempfile.gettempdir(), "matplotlib-cache"))
import matplotlib
matplotlib.use("Agg") # Permite criar os graficos sem abrir uma janela.
import matplotlib.pyplot as plt
import pandas as pd


# Estes nomes sao o contrato do CSV; a ordem das colunas no arquivo pode variar.
COLUNAS_OBRIGATORIAS = [
    "Year", "Month", "DayofWeek", "Reporting_Airline", "CRSDepTime",
    "Distance", "Cancelled", "Diverted", "ArrDelay",
]

# Le o arquivo enviado e verifica o formato antes de iniciar a analise.
def ler_csv(arquivo):
    if arquivo is None or not arquivo.filename:
        raise ValueError("Selecione um arquivo CSV.")

    if not arquivo.filename.lower().endswith(".csv"):
        raise ValueError("O arquivo precisa ter a extensao .csv.")

    # read() recebe os bytes do upload; decode transforma esses bytes em texto.
    conteudo = arquivo.read()
    if not conteudo:
        raise ValueError("O arquivo CSV esta vazio.")

    try:
        texto = conteudo.decode("utf-8-sig") # Tambem remove o BOM, se existir.
    except UnicodeDecodeError:
        raise ValueError("Salve o arquivo CSV com codificacao UTF-8.")

    try:
        # O cabecalho define o separador; os nomes oficiais nao sao traduzidos.
        separador = csv.Sniffer().sniff(texto.splitlines()[0], delimiters=",;").delimiter
        dados = pd.read_csv(io.StringIO(texto), sep=separador)
    except (csv.Error, IndexError, pd.errors.ParserError, pd.errors.EmptyDataError):
        raise ValueError("Nao foi possivel ler o CSV. Use virgula ou ponto e virgula como separador.")

    # Comparamos os nomes encontrados com a lista obrigatoria antes de limpar.
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
    # dtypes mostra os tipos; isnull().sum() conta ausencias em cada coluna.
    tipos = {coluna: str(tipo) for coluna, tipo in dados_limpos.dtypes.items()}
    ausentes = {coluna: int(valor) for coluna, valor in dados_limpos.isnull().sum().items() if valor > 0}
    duplicatas = int(dados_limpos.duplicated().sum())

    # A duplicata so e removida quando todas as colunas do registro sao iguais.
    dados_limpos = dados_limpos.drop_duplicates()

    # errors="coerce" transforma textos incompatíveis em ausentes, removidos abaixo.
    colunas_numericas = ["Year", "Month", "DayofWeek", "CRSDepTime", "Distance", "Cancelled", "Diverted", "ArrDelay"]
    for coluna in colunas_numericas:
        dados_limpos[coluna] = pd.to_numeric(dados_limpos[coluna], errors="coerce")

    dados_limpos["Reporting_Airline"] = dados_limpos["Reporting_Airline"].astype("string").str.strip()

    # Voos cancelados ou desviados nao possuem uma chegada normal para avaliar.
    dados_limpos = dados_limpos.dropna(subset=COLUNAS_OBRIGATORIAS)
    # & exige que todas as condicoes sejam verdadeiras para manter o registro.
    validos = (
        (dados_limpos["Cancelled"] == 0)
        & (dados_limpos["Diverted"] == 0)
        & (dados_limpos["Reporting_Airline"] != "")
        & (dados_limpos["Year"] >= 1987)
        & dados_limpos["Month"].between(1, 12)
        & dados_limpos["DayofWeek"].between(1, 7)
        & (dados_limpos["Distance"] > 0)
    )
    dados_limpos = dados_limpos[validos].copy()

    dados_limpos["HorarioMinutos"] = dados_limpos["CRSDepTime"].apply(horario_para_minutos)
    dados_limpos = dados_limpos.dropna(subset=["HorarioMinutos"])
    # astype(int) converte True/False em 1/0 para a classificacao.
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


# Converte a imagem para texto Base64, exibido no HTML sem salvar arquivos PNG.
def _grafico_base64():
    arquivo = io.BytesIO()
    plt.tight_layout() # Evita sobreposicao dos titulos, eixos e legendas.
    plt.savefig(arquivo, format="png", dpi=110) # Salva o grafico como PNG em memoria.
    plt.close() # Fecha a figura para nao misturar os proximos graficos.
    arquivo.seek(0)
    return base64.b64encode(arquivo.getvalue()).decode("utf-8")


# Cria os tres graficos exigidos e uma interpretacao baseada no CSV enviado.
def criar_graficos(dados):
    graficos = []

    plt.figure(figsize=(8, 4)) # Cria uma figura com 8 polegadas de largura e 4 de altura.
    # clip limita somente a exibicao dos extremos; os dados originais permanecem iguais.
    plt.hist(dados["ArrDelay"].clip(-60, 180), bins=30, color="steelblue", edgecolor="black")
    plt.title("Distribuicao do atraso na chegada") # Titulo
    plt.xlabel("Atraso em minutos (valores entre -60 e 180)") # Legenda do eixo X
    plt.ylabel("Quantidade de voos") # Legenda do eixo Y
    mediana = dados["ArrDelay"].median()
    graficos.append({
        "imagem": _grafico_base64(),
        "interpretacao": f"A mediana do atraso foi {mediana:.1f} minutos. Valores negativos representam chegadas antecipadas.",
    })

    # Como Atrasado e 0 ou 1, a media representa a proporcao de atrasos.
    por_companhia = dados.groupby("Reporting_Airline")["Atrasado"].agg(["mean", "count"])
    companhias_com_amostra = por_companhia[por_companhia["count"] >= 5]
    if not companhias_com_amostra.empty:
        por_companhia = companhias_com_amostra
    por_companhia = por_companhia.sort_values("mean", ascending=False)
    plt.figure(figsize=(8, 4))
    (por_companhia["mean"] * 100).plot(kind="bar", color="darkorange")
    plt.title("Percentual de atrasos por companhia") # Titulo
    plt.xlabel("Companhia") # Legenda do eixo X
    plt.ylabel("Voos atrasados (%)") # Legenda do eixo Y
    plt.xticks(rotation=45, ha="right") # Inclina os nomes para facilitar a leitura.
    companhia_maior = por_companhia.index[0]
    percentual_maior = por_companhia.iloc[0]["mean"] * 100
    graficos.append({
        "imagem": _grafico_base64(),
        "interpretacao": f"Entre as companhias com pelo menos 5 voos, {companhia_maior} teve o maior percentual de atrasos: {percentual_maior:.1f}%.",
    })

    # cut separa o dia em quatro periodos de seis horas. O limite direito fica fora da faixa.
    faixas = pd.cut(dados["HorarioMinutos"], bins=[0, 360, 720, 1080, 1440], right=False, labels=["Madrugada", "Manha", "Tarde", "Noite"])
    por_horario = dados.groupby(faixas, observed=False)["Atrasado"].mean() * 100
    plt.figure(figsize=(8, 4))
    por_horario.plot(kind="bar", color="seagreen")
    plt.title("Percentual de atrasos por horario previsto") # Titulo
    plt.xlabel("Periodo do dia") # Legenda do eixo X
    plt.ylabel("Voos atrasados (%)") # Legenda do eixo Y
    plt.xticks(rotation=0) # Mantem os nomes dos periodos na horizontal.
    faixa_maior = por_horario.idxmax()
    graficos.append({
        "imagem": _grafico_base64(),
        "interpretacao": f"O periodo com maior percentual de atrasos foi {faixa_maior}, com {por_horario.max():.1f}%.",
    })

    return graficos


# Calcula os indicadores exibidos acima da amostra e dos graficos.
def resumir_dados(dados):
    return {
        "voos": len(dados),
        "companhias": dados["Reporting_Airline"].nunique(),
        "atrasados": int(dados["Atrasado"].sum()),
        "percentual_atrasados": dados["Atrasado"].mean() * 100,
        "distancia_media": dados["Distance"].mean(),
        "atraso_medio": dados["ArrDelay"].mean(),
    }
