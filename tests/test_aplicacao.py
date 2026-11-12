import io
import unittest

import pandas as pd
from werkzeug.datastructures import FileStorage

from app import preparar_resultado_atraso
from dados import horario_para_minutos, ler_csv, limpar_dados


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

    def test_converte_horario(self):
        self.assertEqual(horario_para_minutos(1430), 870)
        self.assertEqual(horario_para_minutos("13h30"), 810)
        self.assertEqual(horario_para_minutos("13:30"), 810)
        self.assertIsNone(horario_para_minutos(2460))

    def test_cores_do_atraso_estimado(self):
        # Conferimos os limites para evitar trocar a cor no minuto errado.
        self.assertEqual(preparar_resultado_atraso(15)["classe"], "resultado-verde")
        self.assertEqual(preparar_resultado_atraso(16)["classe"], "resultado-amarelo")
        self.assertEqual(preparar_resultado_atraso(30)["classe"], "resultado-amarelo")
        self.assertEqual(preparar_resultado_atraso(31)["classe"], "resultado-laranja")
        self.assertEqual(preparar_resultado_atraso(60)["classe"], "resultado-laranja")
        self.assertEqual(preparar_resultado_atraso(61)["classe"], "resultado-vermelho")

    def test_formata_atraso_em_horas_e_minutos(self):
        # Cobre horas exatas, minutos restantes, zero e singular/plural.
        resultado = preparar_resultado_atraso(90)
        self.assertEqual(resultado["mensagem"], "1 hora e 30 minutos")
        self.assertEqual(resultado["total_minutos"], "90 minutos")
        self.assertEqual(preparar_resultado_atraso(60)["mensagem"], "1 hora")
        self.assertEqual(preparar_resultado_atraso(121)["mensagem"], "2 horas e 1 minuto")
        self.assertEqual(preparar_resultado_atraso(0)["mensagem"], "Sem atraso estimado")
        self.assertEqual(preparar_resultado_atraso(1)["mensagem"], "1 minuto")


if __name__ == "__main__":
    unittest.main()
