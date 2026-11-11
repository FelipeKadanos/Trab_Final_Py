import base64
from io import BytesIO

import matplotlib

# Usa o Matplotlib sem abrir janelas durante a execução do Flask.
matplotlib.use("Agg")

import matplotlib.pyplot as plt
import pandas as pd

def _figura_para_base64(figura):
    """Converte uma figura do Matplotlib para PNG em base64."""
    buffer = BytesIO()

    figura.savefig(
        buffer,
        format="png",
        bbox_inches="tight",
    )

    buffer.seek(0)

    imagem_base64 = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    buffer.close()
    plt.close(figura)

    return imagem_base64

def analisar_dados(df_limpo):
    """Recebe dados limpos e retorna estatísticas, gráficos e achados."""

    # Quantidade total e proporção de voos com atraso de pelo menos 15 minutos.
    quantidade_voos = len(df_limpo)
    quantidade_atrasados =  int(df_limpo["atrasou"].sum())
    taxa_atraso = float(df_limpo["atrasou"].mean() * 100)

    # Resume as duas variáveis numéricas principais da análise.
    resumo_distancia = {
        "media": float(df_limpo["distancia"].mean()),
        "mediana": float(df_limpo["distancia"].median()),
        "minimo": float(df_limpo["distancia"].min()),
        "maximo": float(df_limpo["distancia"].max()),
    }

    resumo_atraso = {
        "media": float(df_limpo["atraso_chegada"].mean()),
        "mediana": float(df_limpo["atraso_chegada"].median()),
        "minimo": float(df_limpo["atraso_chegada"].min()),
        "maximo": float(df_limpo["atraso_chegada"].max()),
    }

    # Agrupa os voos por companhia para comparar quantidade e taxa de atraso.
    por_companhia = (
        df_limpo.groupby("companhia", as_index=False)
        .agg(
            quantidade_voos=("atrasou", "size"),
            quantidade_atrasados=("atrasou", "sum")
        )
    )

    # Calcula a porcentagem de atrasos de cada companhia.
    por_companhia["taxa_atraso"] = (
        por_companhia["quantidade_atrasados"]
        / por_companhia["quantidade_voos"]
        * 100
    )

    # Ordena da maior para a menor taxa de atraso.
    por_companhia = por_companhia.sort_values(
        "taxa_atraso",
        ascending=False,
    ).reset_index(drop=True)

    graficos = []

    # Usa quartis para resumir a concentração dos atrasos.
    q1_atraso = float(df_limpo["atraso_chegada"].quantile(0.25))
    q3_atraso = float(df_limpo["atraso_chegada"].quantile(0.75))

    # Gráfico 1: distribuição do atraso de chegada.
    figura, eixo = plt.subplots(figsize=(8, 5))

    eixo.hist(
        df_limpo["atraso_chegada"],
        bins=30,
        edgecolor="black",
    )

    eixo.set_title("Distribuição do atraso de chegada")
    eixo.set_xlabel("Atraso de chegada (minutos)")
    eixo.set_ylabel("Quantidade de voos")

    interpretacao = (
        f"A mediana do atraso foi de {resumo_atraso['mediana']:.1f} minutos. "
        f"Metade central dos voos ficou entre {q1_atraso:.1f} e "
        f"{q3_atraso:.1f} minutos de atraso de chegada. "
        f"Os valores observados variaram de {resumo_atraso['minimo']:.1f} "
        f"a {resumo_atraso['maximo']:.1f} minutos."
    )

    graficos.append({
        "titulo": "Distribuição do atraso de chegada",
        "imagem_base64": _figura_para_base64(figura),
        "interpretacao": interpretacao,
    })

    # Gráfico 2: compara a porcentagem de atrasos por companhia.
    figura, eixo = plt.subplots(figsize=(10, 6))

    barras = eixo.bar(
        por_companhia["companhia"],
        por_companhia["taxa_atraso"],
        edgecolor="black",
    )

    eixo.set_title("Porcentagem de atrasos por companhia")
    eixo.set_xlabel("Companhia")
    eixo.set_ylabel("Voos com atraso de pelo menos 15 min (%)")

    # Mostra o tamanho de cada grupo acima da barra.
    for barra, quantidade in zip(
        barras,
        por_companhia["quantidade_voos"],
    ):
        eixo.text(
            barra.get_x() + barra.get_width() / 2,
            barra.get_height(),
            f"n={int(quantidade)}",
            ha="center",
            va="bottom",
            fontsize=8,
        )

    companhia_maior_taxa = por_companhia.iloc[0]
    companhia_menor_taxa = por_companhia.iloc[-1]

    interpretacao = (
        f"A maior taxa de atraso foi da companhia "
        f"{companhia_maior_taxa['companhia']}, com "
        f"{companhia_maior_taxa['taxa_atraso']:.1f}% em "
        f"{int(companhia_maior_taxa['quantidade_voos'])} voos. "
        f"A menor taxa foi da companhia "
        f"{companhia_menor_taxa['companhia']}, com "
        f"{companhia_menor_taxa['taxa_atraso']:.1f}% em "
        f"{int(companhia_menor_taxa['quantidade_voos'])} voos. "
        f"As quantidades devem ser consideradas ao comparar as porcentagens."
    )

    graficos.append({
        "titulo": "Porcentagem de atrasos por companhia",
        "imagem_base64": _figura_para_base64(figura),
        "interpretacao": interpretacao,
    })