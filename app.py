import os

import pandas as pd
from flask import Flask, render_template, request

from dados import criar_graficos, horario_para_minutos, ler_csv, limpar_dados, resumir_dados
from modelo import prever_atraso, treinar_modelos


# Flask cria a aplicacao; __name__ permite localizar templates e arquivos estaticos.
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 # Limite de 16 MB por arquivo.

# O caminho parte deste arquivo, independentemente da pasta usada no terminal.
PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_TREINO = os.path.join(PASTA, "data", "voos_bts_2024_amostra.csv")


# Le a amostra fixa, aplica a limpeza e treina os modelos ao iniciar a aplicacao.
def carregar_modelo():
    dados = pd.read_csv(ARQUIVO_TREINO)
    dados_limpos, _ = limpar_dados(dados)
    return treinar_modelos(dados_limpos)


# Reutilizamos os modelos nas requisicoes; o upload nao altera o treinamento.
MODELO = carregar_modelo()


# Define o texto e a cor de acordo com os minutos estimados de atraso.
def preparar_resultado_atraso(previsao):
    # round arredonda para minutos inteiros; max evita exibir atraso negativo.
    minutos = max(0, round(previsao))

    if minutos > 60:
        classe = "resultado-vermelho"
    elif minutos > 30:
        classe = "resultado-laranja"
    elif minutos > 15:
        classe = "resultado-amarelo"
    else:
        classe = "resultado-verde"

    # divmod retorna o quociente (horas) e o resto (minutos).
    horas, minutos_restantes = divmod(minutos, 60)
    partes = []
    if horas:
        partes.append(f"{horas} hora" if horas == 1 else f"{horas} horas")
    if minutos_restantes:
        partes.append(f"{minutos_restantes} minuto" if minutos_restantes == 1 else f"{minutos_restantes} minutos")
    # join une apenas as partes preenchidas, respeitando singular e plural.
    mensagem = " e ".join(partes) or "Sem atraso estimado"

    return {
        "mensagem": mensagem,
        "classe": classe,
        "minutos": minutos,
        "total_minutos": f"{minutos} minuto" if minutos == 1 else f"{minutos} minutos",
    }


# Envia os dados ao mesmo template, inclusive quando existe uma mensagem de erro.
def dados_pagina(erro=None, resultado_previsao=None, analise=None):
    return render_template("index.html", erro=erro, resultado_previsao=resultado_previsao,
                           analise=analise, modelo=MODELO)


# route associa um endereco do navegador a uma funcao do Python.
@app.route("/")
def inicio():
    return dados_pagina()


# POST recebe o arquivo enviado pelo formulario de upload.
@app.route("/analisar", methods=["POST"])
def analisar():
    try:
        dados_originais = ler_csv(request.files.get("arquivo"))
        dados_limpos, diagnostico = limpar_dados(dados_originais)
        # head(10) limita a amostra; to_html transforma a tabela em HTML.
        analise = {
            "diagnostico": diagnostico,
            "resumo": resumir_dados(dados_limpos),
            "amostra": dados_limpos[["Year", "Month", "DayofWeek", "Reporting_Airline", "CRSDepTime", "Distance", "ArrDelay", "Atrasado"]].head(10).to_html(index=False, classes="tabela"),
            "graficos": criar_graficos(dados_limpos),
        }
        return dados_pagina(analise=analise)
    except ValueError as erro:
        return dados_pagina(erro=str(erro))


# Recebe as entradas, valida os valores e chama o modelo de minutos.
@app.route("/prever", methods=["POST"])
def prever():
    try:
        companhia = request.form.get("companhia", "").strip()
        try:
            mes = int(request.form.get("mes", ""))
            dia_semana = int(request.form.get("dia_semana", ""))
            distancia = float(request.form.get("distancia", ""))
        except (TypeError, ValueError):
            raise ValueError("Preencha todos os campos da previsao com valores validos.")
        horario = horario_para_minutos(request.form.get("horario"))

        # Validamos tambem no servidor, pois o navegador pode enviar dados alterados.
        if companhia not in MODELO["companhias"]:
            raise ValueError("Selecione uma companhia valida.")
        if mes < 1 or mes > 12 or dia_semana < 1 or dia_semana > 7:
            raise ValueError("Mes ou dia da semana invalido.")
        if horario is None:
            raise ValueError("Informe um horario valido no formato 13h30.")
        if distancia <= 0:
            raise ValueError("A distancia precisa ser maior que zero.")

        previsao = prever_atraso(MODELO["modelo_minutos"], companhia, mes, dia_semana, horario, distancia)
        resultado = preparar_resultado_atraso(previsao)
        return dados_pagina(resultado_previsao=resultado)
    except ValueError as erro:
        return dados_pagina(erro=str(erro))


# O Flask retorna 413 quando o envio ultrapassa o limite configurado.
@app.errorhandler(413)
def arquivo_muito_grande(_erro):
    return dados_pagina(erro="O arquivo ultrapassa o limite de 16 MB."), 413


# Inicia o servidor somente quando este arquivo e executado diretamente.
if __name__ == "__main__":
    app.run(debug=True)
