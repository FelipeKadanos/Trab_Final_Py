# Trabalho final - Atraso de voos

Aplicacao Flask que analisa dados de voos e preve se uma chegada tera atraso de 15 minutos ou mais. O trabalho usa dados reais do **Bureau of Transportation Statistics (BTS)** dos Estados Unidos.

## Integrantes e responsabilidades

Preencha esta parte antes da entrega:

- Integrante 1: nome - responsabilidade
- Integrante 2: nome - responsabilidade
- Integrante 3: nome - responsabilidade
- Integrante 4: nome - responsabilidade, se houver

## Como executar

O projeto foi desenvolvido e testado com Python 3.11.

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Depois, abra `http://127.0.0.1:5000` no navegador. O modelo e treinado uma vez quando a aplicacao inicia. O CSV enviado pelo usuario atualiza somente a analise e os graficos.

Para executar os testes:

```powershell
python -m unittest discover -s tests -v
```

## Fonte e recorte dos dados

A amostra incluida em `data/voos_bts_2024_amostra.csv` possui 10.000 registros sorteados de janeiro, fevereiro e marco de 2024. A fonte e a base [Reporting Carrier On-Time Performance do BTS](https://www.transtats.bts.gov/DL_SelectFields.aspx?QO_fu146_anzr=b0-gvzr&gnoyr_VQ=FGJ), disponibilizada em arquivos mensais no [diretorio de downloads do BTS](https://www.transtats.bts.gov/PREZIP/).

O sorteio e reproduzivel: cada mes usa um `random_state` fixo e o sorteio final usa `random_state=42`. Para obter os arquivos novamente e recriar a amostra, execute:

```powershell
python gerar_amostra.py
```

Esse comando requer acesso a internet. Os arquivos mensais completos sao grandes e nao fazem parte da entrega.

## Formato do CSV

A aplicacao aceita separador por virgula ou ponto e virgula e exige estas colunas:

| Coluna | Descricao |
| --- | --- |
| `Year` | Ano do voo |
| `Month` | Mes, de 1 a 12 |
| `DayofWeek` | Dia da semana: 1 para segunda e 7 para domingo |
| `Reporting_Airline` | Codigo da companhia aerea |
| `CRSDepTime` | Horario previsto de partida no formato HHMM |
| `Distance` | Distancia do voo em milhas |
| `Cancelled` | 1 para voo cancelado e 0 para nao cancelado |
| `Diverted` | 1 para voo desviado e 0 para nao desviado |
| `ArrDelay` | Diferenca entre chegada real e prevista, em minutos |

O arquivo precisa estar em UTF-8 e pode ter outras colunas. O limite de upload e 16 MB.

## Limpeza e analise

O programa preserva o arquivo original e trabalha em uma copia do DataFrame. Ele registra tipos, valores ausentes, duplicatas e as quantidades antes e depois da limpeza.

A limpeza segue estas regras:

1. Remove apenas registros completamente duplicados.
2. Converte as colunas numericas e marca valores incompatíveis como ausentes.
3. Exclui voos cancelados e desviados.
4. Exclui registros sem as informacoes essenciais.
5. Exclui mes, dia da semana, horario ou distancia impossiveis.
6. Cria `Atrasado`: 1 quando `ArrDelay >= 15` e 0 nos demais casos.

Os tres graficos apresentam a distribuicao do atraso, o percentual de atrasos por companhia e o percentual de atrasos por periodo do dia. As interpretacoes exibidas sao calculadas a partir do arquivo enviado.

## Variaveis e modelos

O alvo `y` e `Atrasado`. As entradas `X` sao companhia, mes, dia da semana, horario previsto convertido em minutos e distancia. Essas informacoes sao conhecidas antes do voo. `ArrDelay`, cancelamento, desvio e outros dados posteriores ao voo nao entram em `X`.

Foram comparados uma Arvore de Decisao e uma Regressao Logistica. Ambos usam a mesma divisao estratificada de 80% para treino e 20% para teste, com `random_state=42`. A companhia e codificada com `OneHotEncoder`; a Regressao Logistica tambem recebe as variaveis numericas padronizadas. Todo o preparo e ajustado apenas no treino por meio de `Pipeline`.

Na amostra incluida, depois da limpeza restaram 9.813 voos:

| Modelo | Acuracia | Precisao | Recall | F1 |
| --- | ---: | ---: | ---: | ---: |
| Arvore de Decisao | 0,555 | 0,263 | 0,648 | 0,374 |
| Regressao Logistica | 0,590 | 0,270 | 0,583 | 0,369 |

A classe majoritaria representa 79,5% do teste. Como o objetivo e identificar atrasos e existe desequilibrio entre as classes, a escolha usa o maior F1 da classe atrasada. A Arvore de Decisao foi escolhida. Os modelos usam peso balanceado para reduzir a tendencia de prever apenas a classe mais frequente.

## Limitacoes

- A amostra cobre apenas tres meses de voos domesticos dos Estados Unidos.
- Clima, aeroporto, rota e historico recente nao entram no modelo simples.
- O resultado representa uma estimativa academica e nao deve orientar uma viagem real.
- O desempenho pode mudar em outros periodos e companhias.
- Associacoes encontradas nos graficos nao comprovam causa do atraso.

## Roteiro curto da apresentacao

1. Explicar a pergunta, a fonte BTS, as cinco entradas e o alvo de 15 minutos.
2. Enviar o CSV de exemplo e mostrar a validacao, a limpeza e os tres graficos.
3. Comparar as metricas e as matrizes de confusao dos dois modelos.
4. Explicar por que a arvore foi escolhida pelo F1 e realizar uma previsao no formulario.
5. Comentar o desequilibrio das classes e as limitacoes da amostra.

## Referencias e ferramentas

O estilo de organizacao, funcoes e comentarios foi baseado nos trabalhos anteriores do autor: [repositorio da disciplina](https://github.com/FelipeKadanos/up_repo/tree/main/4th_semester/Topicos_Especiais_em_Software) e [projeto de web scraping em Flask](https://github.com/FelipeKadanos/Web_Scrapping_py). A documentacao do Flask, Pandas, Matplotlib e scikit-learn foi consultada para as bibliotecas utilizadas.

Uma ferramenta de inteligencia artificial foi usada para auxiliar na estrutura inicial do codigo, documentacao e verificacao dos testes. A equipe deve revisar e compreender todo o codigo antes da apresentacao.
