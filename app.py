"""Rotas Flask do projeto de atrasos de voos (Pessoa 4).

Este módulo só faz a integração: recebe a requisição, chama as funções
públicas de dados.py, analise.py e modelo.py e renderiza o HTML.
Uploads, DataFrames e gráficos NÃO são guardados entre requisições.
"""
import json
from pathlib import Path

from flask import Flask, render_template, request
from sklearn.compose import ColumnTransformer
from sklearn.preprocessing import OneHotEncoder
from werkzeug.exceptions import RequestEntityTooLarge

from analise import analisar_dados
from dados import carregar_e_limpar_csv
from modelo import carregar_modelo, prever_voo

PASTA_PROJETO = Path(__file__).resolve().parent
CAMINHO_MODELO = PASTA_PROJETO / "models" / "modelo.joblib"
CAMINHO_AVALIACAO = PASTA_PROJETO / "models" / "avaliacao.json"

LIMITE_UPLOAD_BYTES = 10 * 1024 * 1024  # 10 MB, conforme o card C06
ROTULOS_CLASSES = ["Sem atraso de 15 min", "Com atraso de 15 min"]
CAMPOS_FORMULARIO = ["companhia", "mes", "dia_semana", "hora_prevista", "distancia"]
MENSAGEM_SEM_MODELO = (
    "Modelo ainda não treinado. Execute o treino no terminal "
    "(python treinar.py) e reinicie a aplicação."
)

app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = LIMITE_UPLOAD_BYTES


def carregar_artefatos():
    """Carrega uma única vez o modelo e a avaliação gerados pelo treino.

    Retorna (modelo, avaliacao, aviso). Se algum artefato faltar, o item fica
    None e o aviso explica o que fazer; a análise de CSV continua disponível.
    """
    modelo = None
    avaliacao = None
    avisos = []
    try:
        modelo = carregar_modelo(str(CAMINHO_MODELO))
    except (FileNotFoundError, ValueError):
        avisos.append(MENSAGEM_SEM_MODELO)
    if CAMINHO_AVALIACAO.exists():
        try:
            avaliacao = json.loads(CAMINHO_AVALIACAO.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            avisos.append("O arquivo models/avaliacao.json está corrompido. Execute o treino novamente.")
    elif not avisos:
        avisos.append("Arquivo models/avaliacao.json não encontrado. Execute o treino novamente.")
    return modelo, avaliacao, " ".join(avisos)


def listar_companhias(modelo):
    """Retorna as companhias vistas no treino, lidas do OneHotEncoder do pipeline."""
    if modelo is None:
        return []
    for etapa in modelo.named_steps.values():
        if isinstance(etapa, ColumnTransformer):
            for _, transformador, _ in etapa.transformers_:
                if isinstance(transformador, OneHotEncoder):
                    return sorted(str(c) for c in transformador.categories_[0])
    return []


MODELO, AVALIACAO, AVISO_ARTEFATOS = carregar_artefatos()
COMPANHIAS = listar_companhias(MODELO)


def renderizar_inicio(status=200, **extras):
    """Renderiza a página inicial com o contexto comum às três rotas."""
    contexto = {
        "avaliacao": AVALIACAO,
        "aviso_artefatos": AVISO_ARTEFATOS,
        "modelo_disponivel": MODELO is not None,
        "companhias": COMPANHIAS,
        "valores": {},
        "erro": None,
        "erro_previsao": None,
        "resultado": None,
        "aviso_companhia": None,
    }
    contexto.update(extras)
    return render_template("index.html", **contexto), status


@app.get("/")
def inicio():
    """Página inicial: upload, esquema do CSV e formulário de previsão."""
    return renderizar_inicio()


@app.post("/analisar")
def analisar():
    """Recebe o CSV, limpa, analisa e mostra a página de resultados."""
    arquivo = request.files.get("arquivo")
    if arquivo is None or arquivo.filename == "":
        return renderizar_inicio(400, erro="Selecione um arquivo CSV antes de enviar.")
    if not arquivo.filename.lower().endswith(".csv"):
        return renderizar_inicio(400, erro="Formato inválido: envie um arquivo com extensão .csv.")
    try:
        df_limpo, relatorio = carregar_e_limpar_csv(arquivo.stream)
        resultado = analisar_dados(df_limpo)
    except ValueError as erro:
        return renderizar_inicio(400, erro=str(erro))

    amostra_html = df_limpo.head(10).to_html(index=False, classes="tabela", border=0)
    return render_template(
        "analise.html",
        nome_arquivo=arquivo.filename,
        amostra_html=amostra_html,
        quantidade_registros=len(df_limpo),
        quantidade_colunas=len(df_limpo.columns),
        relatorio=relatorio,
        resultado=resultado,
        avaliacao=AVALIACAO,
        rotulos=ROTULOS_CLASSES,
    )


@app.post("/prever")
def prever():
    """Valida os cinco campos de X e mostra a previsão do modelo treinado."""
    valores = {campo: request.form.get(campo, "").strip() for campo in CAMPOS_FORMULARIO}
    if MODELO is None:
        return renderizar_inicio(400, valores=valores, erro_previsao=MENSAGEM_SEM_MODELO)
    try:
        classe = prever_voo(valores, MODELO)
    except ValueError as erro:
        return renderizar_inicio(400, valores=valores, erro_previsao=str(erro))

    aviso = None
    companhia = valores["companhia"].upper()
    if COMPANHIAS and companhia not in COMPANHIAS:
        aviso = (f"A companhia {companhia} não apareceu no treino; "
                 "a previsão ignora essa informação e é menos confiável.")
    return renderizar_inicio(valores=valores, resultado=ROTULOS_CLASSES[int(classe)],
                             aviso_companhia=aviso)


@app.errorhandler(RequestEntityTooLarge)
def arquivo_grande(_erro):
    """Mensagem amigável quando o upload passa de 10 MB."""
    return renderizar_inicio(413, erro="Arquivo maior que o limite de 10 MB. Envie um CSV menor.")


@app.errorhandler(500)
def erro_interno(_erro):
    """Evita mostrar traceback ao usuário em falhas inesperadas."""
    return renderizar_inicio(500, erro="Erro inesperado ao processar a requisição. Verifique o arquivo e tente novamente.")


if __name__ == "__main__":
    # debug=False: o modo debug exibiria tracebacks no navegador.
    app.run(host="127.0.0.1", port=5000, debug=False)
