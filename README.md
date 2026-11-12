# Trabalho final - Atraso de voos

Aplicacao Flask que analisa dados de voos e preve se uma chegada tera atraso de 15 minutos ou mais. O trabalho usa dados reais do **Bureau of Transportation Statistics (BTS)** dos Estados Unidos.

## Integrantes

- Felipe Kadanos
- Leonardo Teles
- Marcos Jose Ferrari
- Murilo

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

## Fluxo completo do trabalho

Este roteiro acompanha os dados desde a criacao do CSV ate os resultados no navegador e os testes do programa. Execute os comandos na pasta do projeto.

### 1. Preparar o ambiente

Crie e ative o ambiente virtual e instale as dependencias:

```powershell
python -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

### 2. Gerar o CSV de exemplo

```powershell
python gerar_amostra.py
```

O script `gerar_amostra.py` executa estas etapas:

1. Obtem os ZIPs do BTS de janeiro, fevereiro e marco de 2024. Reutiliza os arquivos presentes em `.dados_bts/` ou baixa pela internet.
2. Le as nove colunas usadas no projeto e renomeia `DayOfWeek` para `DayofWeek`, conforme o formato da aplicacao.
3. Sorteia ate 4.000 registros por mes com sementes fixas de 43, 44 e 45. Junta as amostras e sorteia 10.000 voos com `random_state=42`.
4. Salva `data/voos_bts_2024_amostra.csv`, sem uma coluna extra de indice.

Esta etapa e opcional, pois o CSV ja acompanha o repositorio. Executa-la substitui a amostra existente. Os ZIPs baixados nao sao salvos automaticamente em `.dados_bts/`.

### 3. Iniciar a aplicacao e limpar a base

```powershell
python app.py
```

Na inicializacao, `app.py` le a amostra fixa e chama `limpar_dados()`, de `dados.py`. A funcao trabalha em uma copia e registra tipos, ausencias, duplicatas e quantidades antes e depois da limpeza.

Ela remove duplicatas, converte colunas numericas, exclui voos cancelados, desviados, incompletos ou com valores invalidos e transforma o horario HHMM em minutos desde a meia-noite.

Depois, cria `Atrasado`: **1** para `ArrDelay >= 15` e **0** para chegadas antecipadas ou com atraso inferior a 15 minutos. Na amostra incluida, restam 9.813 voos.

### 4. Treinar, testar e escolher o modelo

A funcao `treinar_modelos()`, de `modelo.py`, recebe os dados limpos:

1. Define `X` com companhia, mes, dia da semana, horario previsto em minutos e distancia. O alvo `y` e `Atrasado`.
2. Divide os registros em 80% para treino e 20% para teste, com `random_state=42` e estratificacao para preservar aproximadamente a proporcao das classes. Na amostra limpa, sao 7.850 registros de treino e 1.963 de teste.
3. Codifica as companhias com `OneHotEncoder` e, para a Regressao Logistica, padroniza os numeros com `StandardScaler`. O preparo e aprendido somente no treino, dentro de `Pipeline`.
4. Treina Arvore de Decisao e Regressao Logistica na mesma divisao. Executa `predict()` no teste e calcula acuracia, precisao, recall, F1 e matriz de confusao.
5. Escolhe o maior F1 da classe atrasada e guarda o modelo, seu preparo e os resultados em memoria. Tambem treina uma Floresta Aleatoria auxiliar para estimar `ArrDelay`, usando as mesmas entradas e divisao de treino/teste. Seu erro absoluto medio (MAE) e mostrado em minutos, considerando chegadas antecipadas como zero atraso.

A pagina apresenta as metricas, matrizes, tamanhos de treino e teste, proporcao da classe majoritaria e modelo escolhido. Na amostra incluida, a Arvore de Decisao vence. Essa avaliacao do aprendizado e diferente dos testes automatizados do codigo, descritos na etapa 8.

### 5. Enviar um CSV para analise

Abra `http://127.0.0.1:5000`, selecione o CSV de exemplo e clique em **Analisar arquivo**. Outros arquivos tambem sao aceitos, desde que respeitem o formato documentado abaixo.

A rota `/analisar` chama `ler_csv()` para verificar extensao, conteudo, UTF-8, separador e colunas obrigatorias. Depois, aplica `limpar_dados()` ao arquivo enviado. Entradas invalidas geram mensagens na pagina.

O upload atualiza as analises e os graficos. O modelo permanece treinado com a amostra fixa da inicializacao. Para usar uma amostra regenerada no treinamento, reinicie a aplicacao.

### 6. Consultar estatisticas, graficos e resultados

A rota usa `resumir_dados()` e `criar_graficos()` para enviar ao template `templates/index.html`:

- Total de voos validos, companhias, percentual de atrasos e distancia media.
- Diagnostico com quantidades antes e depois da limpeza, removidos, duplicatas, ausencias e tipos.
- Amostra dos primeiros dez registros tratados.
- **Histograma dos atrasos:** mostra a distribuicao e informa a mediana. A exibicao limita os extremos entre -60 e 180 minutos, sem alterar os dados dos calculos.
- **Barras por companhia:** compara os percentuais de atrasos e identifica o maior.
- **Barras por periodo do dia:** compara os percentuais entre madrugada, manha, tarde e noite e identifica o maior.

Os graficos sao gerados com Matplotlib e enviados ao HTML como PNG em Base64, sem salvar imagens no disco. As interpretacoes sao calculadas a partir do CSV enviado.

### 7. Fazer uma nova previsao

Em **Prever atraso**, preencha companhia, mes, dia da semana, horario previsto (`13h30`) e distancia em milhas. Clique em **Realizar previsao**.

A rota `/prever` valida os campos e converte o horario para minutos. `prever_atraso()` monta uma linha com as mesmas colunas e ordem do treinamento. Os `Pipeline`s aplicam o preparo e executam `predict()` para obter a classe e a estimativa de minutos.

A pagina apresenta o atraso estimado em horas e minutos (por exemplo, **1 hora e 30 minutos**) e o total em minutos. A mensagem fica verde ate 15 minutos, amarela acima de 15, laranja acima de 30 e vermelha acima de 60. Valores negativos aparecem como **Sem atraso estimado**. A classificacao de atraso de 15 minutos ou mais aparece em uma linha separada. Os dois modelos sao independentes e podem divergir; a duracao e uma estimativa, e o atraso real so e conhecido apos a chegada.

### 8. Executar os testes e conferir a entrega

Em outro terminal, com o ambiente virtual ativado, execute:

```powershell
python -m unittest discover -s tests -v
```

Os testes em `tests/test_aplicacao.py` verificam leitura e rejeicao de CSVs, limpeza, conversao e validacao de horarios, formatacao de horas e minutos, cores por faixa, paginas de erro e integracao do formulario com os modelos. A importacao de `app.py` tambem executa o treinamento inicial. O resultado final deve apresentar `OK`.

No navegador, confira o upload do CSV, os tres graficos e interpretacoes, as metricas e matrizes, uma nova previsao e a mensagem ao enviar um arquivo invalido. Essa conferencia complementa os testes automatizados, que nao verificam a aparencia dos graficos.

```text
BTS / ZIPs -> gerar_amostra.py -> CSV de exemplo
                                  |
                                  v
                    app.py -> limpeza -> X e y
                                  |
                                  v
                    treino/teste -> dois modelos
                                  |
                                  v
                    metricas -> escolha pelo F1 -> formulario -> previsao

CSV enviado -> validacao -> limpeza -> estatisticas + tres graficos -> HTML

unittest -> verifica o codigo e a integracao das rotas
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

O arquivo precisa estar em UTF-8 e usar exatamente os nomes oficiais acima, em qualquer ordem. Pode ter outras colunas. Cabecalhos traduzidos, tabulacao e linhas `sep=` do Excel nao sao aceitos. O limite de upload e 16 MB.

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

O formulario usa o classificador escolhido para prever chegada com atraso de 15 minutos ou mais (classe 1) ou sem esse atraso (classe 0). Tambem usa uma Floresta Aleatoria auxiliar para estimar a duracao do atraso e exibi-la em horas e minutos, com cores por faixa. A regressao aprende os minutos historicos de `ArrDelay`, que continuam excluidos das entradas `X`. O MAE exibido avalia a estimativa com minimo de zero, correspondente ao atraso apresentado ao usuario.

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
