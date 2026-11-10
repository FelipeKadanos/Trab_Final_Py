import pandas as pd

# Define as colunas obrigatórias e a ordem da tabela limpa.
COLUNAS = [
    "companhia",
    "mes",
    "dia_semana",
    "hora_prevista",
    "distancia",
    "atraso_chegada",
    "cancelado",
    "desviado",
]

def carregar_e_limpar_csv(arquivo):
    """Recebe caminho ou arquivo binário; retorna dados limpos e relatório."""
    # Lê o formato combinado e traduz erros de leitura para mensagens em português.
    try:
        dados = pd.read_csv(arquivo, encoding="utf-8", sep=",")
    except pd.errors.EmptyDataError as erro:
        raise ValueError("O arquivo CSV está vazio ou não possui cabeçalho.") from erro
    except UnicodeDecodeError as erro:
        raise ValueError("Codificação inválida. Salve o CSV em UTF-8.") from erro
    except pd.errors.ParserError as erro:
        raise ValueError("CSV malformado. Confira as aspas e a organização dos campos.") from erro

    # Um arquivo pode ter cabeçalho válido, mas nenhum registro.
    if dados.empty:
        raise ValueError("O CSV tem cabeçalho, mas não contém registros.")

    # Um CSV separado por ponto e vírgula pode ser lido como uma única coluna.
    if len(dados.columns) == 1 and ";" in dados.columns[0]:
        raise ValueError("Separador incorreto. Use vírgula (,) para separar as colunas do CSV.")

    # Confere as colunas obrigatórias antes de acessar seus valores.
    faltantes = []
    for coluna in COLUNAS:
        if coluna not in dados.columns:
            faltantes.append(coluna)
    if faltantes:
        raise ValueError("Colunas obrigatórias ausentes: " + ", ".join(faltantes))

    # Registra a situação recebida, antes das conversões e remoções.
    relatorio = {
        "linhas_antes": len(dados),
        "colunas_recebidas": dados.columns.tolist(),
        "tipos_originais": dados.dtypes.astype(str).to_dict(),
        "ausentes_por_coluna": dados.isna().sum().to_dict(),
        "avisos": [],
        "remocoes": [],
    }

    # Colunas extras são permitidas, mas serão ignoradas e informadas no relatório.
    extras = []
    for coluna in dados.columns:
        if coluna not in COLUNAS:
            extras.append(coluna)
    if extras:
        relatorio["avisos"].append("Colunas extras ignoradas: " + ", ".join(extras))

    # Mantém apenas as oito colunas, na ordem combinada com o grupo.
    dados = dados[COLUNAS].copy()

    # Identifica repetições nas oito colunas, preservando a primeira ocorrência.
    # Voos diferentes podem ser indistinguíveis nesse recorte.    
    duplicatas = dados.duplicated()
    relatorio["duplicatas_encontradas"] = int(duplicatas.sum())

    dados = dados.loc[~duplicatas].copy()

    relatorio["remocoes"].append({
        "motivo": "Duplicatas exatas nas 8 colunas",
        "quantidade": int(duplicatas.sum()),
    })

    if duplicatas.any():
        relatorio["avisos"].append(
            "Duplicatas exatas no recorte podem representar "
            "voos legítimos indistinguíveis."
        )

    # Evita tratar " aa " e "AA" como companhias diferentes.
    dados["companhia"] = (dados["companhia"].astype("string").str.strip().str.upper())

    # Converte as entradas numéricas; textos incompatíveis viram valores ausentes.
    for coluna in COLUNAS[1:]:
        dados[coluna] = pd.to_numeric(
            dados[coluna],
            errors="coerce",
        )

    # Infinitos não são valores válidos e serão rejeitados como ausentes.
    dados[COLUNAS[1:]] = dados[COLUNAS[1:]].replace(
        [float("inf"), float("-inf")],
        float("nan"),
    )

    # Remove indicadores diferentes de 0 ou 1 antes de interpretar seu significado.
    invalidos = (~dados["cancelado"].isin([0, 1]) | ~dados["desviado"].isin([0, 1]))

    relatorio["remocoes"].append({
        "motivo": "Indicadores de cancelamento ou desvio inválidos.", 
        "quantidade": int(invalidos.sum())
    })

    dados = dados.loc[~invalidos].copy()

    # Conta e remove cancelados apenas entre as linhas que restaram.
    cancelados = dados["cancelado"].eq(1)
    relatorio["remocoes"].append({
        "motivo": "Voos cancelados",
        "quantidade": int(cancelados.sum()),
    })
    dados = dados.loc[~cancelados].copy()

    # Remove desviados depois dos cancelados, evitando contar a mesma linha duas vezes.
    desviados = dados["desviado"].eq(1)
    relatorio["remocoes"].append({
        "motivo": "Voos desviados",
        "quantidade": int(desviados.sum()),
    })
    dados = dados.loc[~desviados].copy()

    # Normaliza 2400 para meia-noite antes de validar o horário.
    dados.loc[
        dados["hora_prevista"].eq(2400),
        "hora_prevista",
    ] = 0

    # Verifica horários HHMM, limites e valores inteiros de mês e dia da semana.
    horas = dados["hora_prevista"]

    horario_valido = (horas.between(0, 2359) & (horas % 100 < 60) & (horas % 1 == 0))
    mes_valido = (dados["mes"].between(1, 12) & (dados["mes"] % 1 == 0))
    dia_valido = (dados["dia_semana"].between(1,7) & (dados["dia_semana"] % 1 == 0))
    distancia_valida = dados["distancia"].gt(0)
    companhia_valida = (dados["companhia"].notna() & dados["companhia"].ne(""))

    # Atrasos negativos são válidos; atraso ausente não pode ser inventado como zero.
    atraso_valido = dados["atraso_chegada"].notna()

    # Uma linha precisa passar por todas as condições.
    # Mesmo com vários problemas, ela será contabilizada uma única vez.
    validos = (
        horario_valido
        & mes_valido
        & dia_valido
        & distancia_valida
        & companhia_valida
        & atraso_valido
    )

    relatorio["remocoes"].append({
        "motivo": "Entradas ou atraso de chegada ausentes/inválidos",
        "quantidade": int((~validos).sum())
    })

    dados = dados.loc[validos].copy()

    # Impede que a aplicação tente analisar uma tabela sem registros válidos.
    if dados.empty:
        raise ValueError("Nenhuma linha válida restou após a limpeza do CSV.")

    # Converte para inteiros somente após remover valores ausentes e inválidos.
    inteiras = [
        "mes",
        "dia_semana",
        "hora_prevista",
        "cancelado",
        "desviado",
    ]

    dados[inteiras] = dados[inteiras].astype("int64")

    # O atraso histórico define o alvo: 1 para pelo menos 15 minutos, 0 nos demais casos.
    # O atraso de chegada nunca deve ser usado como variável de entrada do modelo.
    dados["atrasou"] = (dados["atraso_chegada"] >= 15).astype("int64")

    # Registra o tamanho final para conferir as contagens de remoção.
    relatorio["linhas_depois"] = len(dados)

    # Uma classe permite análise, mas o código de treinamento deverá recusar essa base.
    if dados["atrasou"].nunique() == 1:
        relatorio["avisos"].append(
            "A base contém apenas uma classe de atraso. "
            "Pode ser analisada, mas não utilizada para treinar o modelo."
        )

    # Reorganiza os índices após as remoções, sem criar uma coluna extra.
    dados = dados.reset_index(drop=True)

    # Devolve a tabela e o diagnóstico sem gravar alterações no arquivo original.
    return dados, relatorio