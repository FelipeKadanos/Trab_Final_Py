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