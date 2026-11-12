import io
import unittest

import pandas as pd
from werkzeug.datastructures import FileStorage

from dados import horario_para_minutos, ler_csv, limpar_dados


CSV_VALIDO = """Year,Month,DayofWeek,Reporting_Airline,CRSDepTime,Distance,Cancelled,Diverted,ArrDelay
2024,1,1,AA,1430,500,0,0,20
2024,1,2,DL,930,800,0,0,5
2024,1,3,UA,2500,700,0,0,10
2024,1,4,AA,1200,600,1,0,
"""


class TesteDados(unittest.TestCase):
    def criar_arquivo(self, conteudo, nome="voos.csv"):
        return FileStorage(stream=io.BytesIO(conteudo.encode("utf-8")), filename=nome)

    def test_le_csv_com_virgula(self):
        dados = ler_csv(self.criar_arquivo(CSV_VALIDO))
        self.assertEqual(len(dados), 4)

    def test_le_csv_com_ponto_e_virgula(self):
        dados = ler_csv(self.criar_arquivo(CSV_VALIDO.replace(",", ";")))
        self.assertEqual(len(dados), 4)

    def test_rejeita_coluna_ausente(self):
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

    def test_converte_horario(self):
        self.assertEqual(horario_para_minutos(1430), 870)
        self.assertEqual(horario_para_minutos("13h30"), 810)
        self.assertEqual(horario_para_minutos("13:30"), 810)
        self.assertIsNone(horario_para_minutos(2460))


if __name__ == "__main__":
    unittest.main()
