import io
import unittest

import pandas as pd
from werkzeug.datastructures import FileStorage

from app import MODELO, app, preparar_resultado_atraso
from modelo import prever_atraso
from dados import ler_csv, limpar_dados


# Inclui voos validos, um horario impossivel e um cancelamento para testar a limpeza.
CSV_VALIDO = """Year,Month,DayofWeek,Reporting_Airline,CRSDepTime,Distance,Cancelled,Diverted,ArrDelay
2024,1,1,AA,1430,500,0,0,20
2024,1,2,DL,930,800,0,0,5
2024,1,3,UA,2500,700,0,0,10
2024,1,4,AA,1200,600,1,0,
"""


# unittest executa os metodos test_ e informa falhas nas comparacoes assert.
class TesteDados(unittest.TestCase):
    def criar_arquivo(self, conteudo, nome="voos.csv"):
        # Simula um upload do navegador sem criar um arquivo no disco.
        return FileStorage(stream=io.BytesIO(conteudo.encode("utf-8")), filename=nome)

    def test_le_csv_com_virgula(self):
        dados = ler_csv(self.criar_arquivo(CSV_VALIDO))
        self.assertEqual(len(dados), 4)

    def test_le_csv_com_ponto_e_virgula(self):
        dados = ler_csv(self.criar_arquivo(CSV_VALIDO.replace(",", ";")))
        self.assertEqual(len(dados), 4)

    def test_rejeita_tabulacao(self):
        with self.assertRaises(ValueError):
            ler_csv(self.criar_arquivo(CSV_VALIDO.replace(",", "\t")))

    def test_rejeita_cabecalho_traduzido(self):
        cabecalho = "Ano,Mes,Dia da semana,Companhia,Horario previsto,Distancia,Cancelado,Desviado,Atraso chegada"
        with self.assertRaisesRegex(ValueError, "Colunas obrigatorias"):
            ler_csv(self.criar_arquivo(CSV_VALIDO.replace(CSV_VALIDO.splitlines()[0], cabecalho)))

    def test_rejeita_coluna_ausente(self):
        # assertRaisesRegex confere tanto o tipo do erro quanto parte da mensagem.
        with self.assertRaisesRegex(ValueError, "Colunas obrigatorias"):
            ler_csv(self.criar_arquivo("Year,Month\n2024,1"))

    def test_rejeita_arquivo_vazio(self):
        with self.assertRaisesRegex(ValueError, "vazio"):
            ler_csv(self.criar_arquivo(""))

    def test_rejeita_extensao_invalida(self):
        with self.assertRaisesRegex(ValueError, "extensao"):
            ler_csv(self.criar_arquivo(CSV_VALIDO, nome="voos.txt"))

    def test_limpeza_remove_cancelado_e_horario_invalido(self):
        dados = pd.read_csv(io.StringIO(CSV_VALIDO))
        limpos, diagnostico = limpar_dados(dados)
        self.assertEqual(len(limpos), 2)
        self.assertEqual(diagnostico["quantidade_inicial"], 4)

    def test_converte_horario_na_limpeza(self):
        dados = pd.read_csv(io.StringIO(CSV_VALIDO))
        limpos, _ = limpar_dados(dados)
        self.assertEqual(limpos["HorarioMinutos"].tolist(), [870, 570])

    def test_formatos_e_limites_de_horario_no_formulario(self):
        campos = {
            "companhia": MODELO["companhias"][0], "mes": "1",
            "dia_semana": "1", "distancia": "500",
        }
        with app.test_client() as cliente:
            for horario in ("13h30", "13:30", "1330", "00h00", "23h59"):
                with self.subTest(horario=horario):
                    resposta = cliente.post("/prever", data={**campos, "horario": horario})
                    self.assertIn("Atraso estimado:", resposta.get_data(as_text=True))
            for horario in ("24h60", "25h00", "13h60", "-100", "abc", ""):
                with self.subTest(horario=horario):
                    resposta = cliente.post("/prever", data={**campos, "horario": horario})
                    self.assertIn("Informe um horario valido", resposta.get_data(as_text=True))

    def test_pagina_inicial_e_erros_renderizam(self):
        with app.test_client() as cliente:
            self.assertEqual(cliente.get("/").status_code, 200)
            resposta = cliente.post("/analisar")
            self.assertIn("Selecione um arquivo CSV.", resposta.get_data(as_text=True))
            with app.test_request_context():
                from app import arquivo_muito_grande
                pagina, status = arquivo_muito_grande(None)
                self.assertEqual(status, 413)
                self.assertIn("O arquivo ultrapassa o limite de 16 MB.", pagina)

    def test_formata_horas_minutos_e_cores(self):
        for valor, mensagem in ((90, "1 hora e 30 minutos"), (60, "1 hora"),
                                (121, "2 horas e 1 minuto"), (1, "1 minuto"),
                                (0, "Sem atraso estimado"), (-10, "Sem atraso estimado")):
            with self.subTest(valor=valor):
                self.assertEqual(preparar_resultado_atraso(valor)["mensagem"], mensagem)
        for valor, cor in ((15, "verde"), (16, "amarelo"), (30, "amarelo"),
                           (31, "laranja"), (60, "laranja"), (61, "vermelho")):
            self.assertEqual(preparar_resultado_atraso(valor)["classe"], "resultado-" + cor)
        self.assertEqual(preparar_resultado_atraso(90)["total_minutos"], "90 minutos")

    def test_formulario_usa_classificador_escolhido(self):
        companhia = MODELO["companhias"][0]
        previsao = prever_atraso(MODELO["modelo"], companhia, 1, 1, 810, 500)
        mensagem = "Com atraso de 15 minutos ou mais" if previsao == 1 else "Sem atraso de 15 minutos ou mais"
        minutos = prever_atraso(MODELO["modelo_minutos"], companhia, 1, 1, 810, 500)
        estimativa = preparar_resultado_atraso(minutos)["mensagem"]
        with app.test_client() as cliente:
            resposta = cliente.post("/prever", data={
                "companhia": companhia, "mes": "1", "dia_semana": "1",
                "horario": "13h30", "distancia": "500",
            })
        self.assertEqual(resposta.status_code, 200)
        self.assertIn(mensagem, resposta.get_data(as_text=True))
        self.assertIn("Atraso estimado: " + estimativa, resposta.get_data(as_text=True))
        self.assertGreaterEqual(MODELO["mae_minutos"], 0)


if __name__ == "__main__":
    unittest.main()
