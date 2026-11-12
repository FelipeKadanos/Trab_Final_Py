import io
import os
import urllib.request
import zipfile

import pandas as pd


# Os caminhos sao relativos a este script, e nao a pasta aberta no terminal.
PASTA = os.path.dirname(os.path.abspath(__file__))
PASTA_DADOS = os.path.join(PASTA, "data")
PASTA_DOWNLOADS = os.path.join(PASTA, ".dados_bts")
COLUNAS = ["Year", "Month", "DayofWeek", "Reporting_Airline", "CRSDepTime", "Distance", "Cancelled", "Diverted", "ArrDelay"]
COLUNAS_BTS = ["Year", "Month", "DayOfWeek", "Reporting_Airline", "CRSDepTime", "Distance", "Cancelled", "Diverted", "ArrDelay"]


# Baixa os tres meses oficiais e sorteia registros com random_state fixo.
def gerar_amostra():
    partes = []

    for mes in range(1, 4): # range nao inclui o 4: usamos janeiro, fevereiro e marco.

        nome = f"On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2024_{mes}.zip"
        url = "https://www.transtats.bts.gov/PREZIP/" + nome
        caminho_download = os.path.join(PASTA_DOWNLOADS, nome)

        # Reutiliza um ZIP local quando disponivel para evitar outro download.
        if os.path.exists(caminho_download):
            print("Usando arquivo existente", nome)

            with open(caminho_download, "rb") as arquivo:
                conteudo = arquivo.read()

        else:
            print("Baixando", nome)

            with urllib.request.urlopen(url) as resposta:
                conteudo = resposta.read()


        # BytesIO permite abrir o ZIP em memoria; with fecha os arquivos ao terminar.
        with zipfile.ZipFile(io.BytesIO(conteudo)) as arquivo_zip:
            csv_nome = next(nome for nome in arquivo_zip.namelist() if nome.lower().endswith(".csv"))

            with arquivo_zip.open(csv_nome) as arquivo_csv:
                dados = pd.read_csv(arquivo_csv, usecols=COLUNAS_BTS, low_memory=False)

                # Padroniza a grafia oficial do BTS para o nome esperado pela aplicacao.
                dados = dados.rename(columns={"DayOfWeek": "DayofWeek"})


        partes.append(dados.sample(n=min(4000, len(dados)), random_state=42 + mes))

    # concat junta os meses; sample sorteia 10 mil linhas com uma semente fixa.
    amostra = pd.concat(partes, ignore_index=True).sample(n=10000, random_state=42)
    os.makedirs(PASTA_DADOS, exist_ok=True)
    
    caminho = os.path.join(PASTA_DADOS, "voos_bts_2024_amostra.csv")
    amostra.to_csv(caminho, index=False) # Nao grava o indice como uma coluna extra.

    print("Amostra salva em", caminho)


if __name__ == "__main__":
    gerar_amostra()
