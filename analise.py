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