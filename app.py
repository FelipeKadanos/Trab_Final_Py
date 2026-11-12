import os

import pandas as pd
from flask import Flask, render_template, request

from dados import criar_graficos, ler_csv, limpar_dados, resumir_dados
from modelo import prever_atraso, treinar_modelos


# Flask cria a aplicacao; __name__ permite localizar templates e arquivos estaticos.
app = Flask(__name__)
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024 # Limite de 16 MB por arquivo.

# O caminho parte deste arquivo, independentemente da pasta usada no terminal.
PASTA = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_TREINO = os.path.join(PASTA, "data", "voos_bts_2024_amostra.csv")


# Le a amostra fixa, limpa os dados e treina uma vez ao iniciar a aplicacao.
dados_treino = pd.read_csv(ARQUIVO_TREINO)
dados_treino_limpos, _ = limpar_dados(dados_treino) # O diagnostico nao e usado no treino.
MODELO = treinar_modelos(dados_treino_limpos)


# Formata os minutos estimados em horas e minutos e escolhe a cor da mensagem.
def preparar_resultado_atraso(previsao):
    minutos = max(0, round(previsao)) # Arredonda e apresenta chegadas antecipadas como zero atraso.
    if minutos > 60:
        classe = "resultado-vermelho"
    elif minutos > 30:
        classe = "resultado-laranja"
    elif minutos > 15:
        classe = "resultado-amarelo"
    else:
        classe = "resultado-verde"

    # divmod separa as horas completas dos minutos restantes.
    horas, restantes = divmod(minutos, 60)
    partes = []
    if horas:
        partes.append(f"{horas} hora" if horas == 1 else f"{horas} horas")
    if restantes:
        partes.append(f"{restantes} minuto" if restantes == 1 else f"{restantes} minutos")
    return {
        "mensagem": " e ".join(partes) or "Sem atraso estimado",
        "total_minutos": f"{minutos} minuto" if minutos == 1 else f"{minutos} minutos",
        "classe": classe,
    }


# route associa um endereco do navegador a uma funcao do Python.
@app.route("/")
def inicio():
    return render_template("index.html", modelo=MODELO)


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

        return render_template("index.html", modelo=MODELO, analise=analise)

    except ValueError as erro:
        return render_template("index.html", modelo=MODELO, erro=str(erro))


# Valida as entradas e consulta a classificacao e a estimativa de minutos.
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


        # Aceita HHMM, 13h30 e 13:30; converte para minutos desde a meia-noite.
        try:
            texto_horario = request.form.get("horario", "").strip().lower().replace("h", "").replace(":", "")
            horario_hhmm = int(float(texto_horario))
            horas, minutos = divmod(horario_hhmm, 100)
            horario = horas * 60 + minutos if 0 <= horas <= 23 and 0 <= minutos <= 59 else None
        except (TypeError, ValueError, OverflowError):
            horario = None

        # Validamos tambem no servidor, pois o navegador pode enviar dados alterados.
        if companhia not in MODELO["companhias"]:
            raise ValueError("Selecione uma companhia valida.")

        if mes < 1 or mes > 12 or dia_semana < 1 or dia_semana > 7:
            raise ValueError("Mes ou dia da semana invalido.")

        if horario is None:
            raise ValueError("Informe um horario valido no formato 13h30.")

        if distancia <= 0:
            raise ValueError("A distancia precisa ser maior que zero.")

        previsao = prever_atraso(MODELO["modelo"], companhia, mes, dia_semana, horario, distancia)
        minutos = prever_atraso(MODELO["modelo_minutos"], companhia, mes, dia_semana, horario, distancia)
        resultado = preparar_resultado_atraso(minutos)
        resultado["classificacao"] = "Com atraso de 15 minutos ou mais" if previsao == 1 else "Sem atraso de 15 minutos ou mais"
        
        return render_template("index.html", modelo=MODELO, resultado_previsao=resultado)

    except ValueError as erro:
        return render_template("index.html", modelo=MODELO, erro=str(erro))


# O Flask retorna 413 quando o envio ultrapassa o limite configurado.
@app.errorhandler(413)
def arquivo_muito_grande(_erro):
    return render_template("index.html", modelo=MODELO, erro="O arquivo ultrapassa o limite de 16 MB."), 413


# Inicia o servidor somente quando este arquivo e executado diretamente.
if __name__ == "__main__":
    app.run(debug=True)
