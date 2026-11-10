# Trabalho final — Atrasos de voos

Plano para quatro integrantes e suas IAs. **Este documento é o plano de implementação; a aplicação ainda não está pronta.** Requisitos oficiais transcritos em [requisitos.md](requisitos.md), a partir de [Trabalho Final.pdf](Trabalho%20Final.pdf).

## Contexto e decisões do projeto

**Tema 7 — classificação de atrasos de voos.** Pergunta: usando informações disponíveis antes da partida, podemos prever se um voo chegará com atraso de pelo menos 15 minutos?

- Fonte: **BTS Airline On-Time Statistics**. Selecionar um mês completo de um ano passado e documentar como obter o recorte.
- X: companhia, mês, dia da semana, horário previsto de partida e distância.
- y: `atrasou = 1` quando `atraso_chegada >= 15`; caso contrário, 0. Atrasos negativos são válidos: significam chegada antecipada.
- Excluir cancelados, desviados e registros sem atraso de chegada conhecido.
- Nunca usar horários reais, atraso na partida, atraso na chegada ou causas do atraso em X. O atraso na chegada serve apenas para construir y e analisar o histórico.
- Modelo treinado uma vez por script e carregado no Flask. **Upload atualiza análises e gráficos, sem retreinar o modelo.** Informar a base e a versão usadas no treino na interface.
- Aplicação local com duas páginas: início com upload e previsão; análise com diagnóstico, gráficos e avaliação dos modelos.

Usar somente Python, Flask, HTML/Jinja, CSS básico, Pandas, Matplotlib, scikit-learn e joblib. Sem banco, login, API separada, mapas, JavaScript obrigatório, Docker, busca de hiperparâmetros ou escolha de modelos pelo usuário. O objetivo é atender todos os critérios com a menor implementação compreensível. A nota também depende da defesa individual.

## Equipe e sequência

Substituir os nomes antes de começar. Cada pessoa implementa sua parte e deve entender o projeto inteiro.

| Pessoa | Nome | Responsabilidade | Cards |
| --- | --- | --- | --- |
| 1 | Leonardo Teles | Fonte, CSV, validação e limpeza | C01, C02 |
| 2 | Murilo | Estatísticas, gráficos e interpretações | C03 |
| 3 | Felipe | Modelos, avaliação e previsão | C04, C05 |
| 4 | Marcos | Flask, HTML, integração e instalação | C06, C07 |
| Todos | Os quatro | Revisão, demonstração e defesa | C08 |

**Ordem:** C01 → C02 → C03 e C04 em paralelo → C05 → conclusão de C06 → C07 → C08. A pessoa 4 pode preparar páginas e rotas desde a publicação dos contratos. A pessoa 2 pode preparar gráficos após C01, conferindo depois com a limpeza real.

Cada pessoa usa sua branch, por exemplo `pessoa1-dados`, com commits pequenos e mensagens claras. Revisar a integração antes de juntar à principal. O responsável atualiza o status do card e registra a evidência de verificação. Combinar mudanças nos contratos antes de alterar funções consumidas pelos colegas.

## Contrato dos dados

### Fonte e recorte: preencher no C01

| Registro | Situação |
| --- | --- |
| Aprovação do tema e dataset pelo professor | Confirmada pelo integrante responsável pela Pessoa 1 |
| Link oficial direto para obtenção | [BTS — janeiro de 2024](https://www.transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2024_1.zip) |
| Período selecionado | Janeiro de 2024 |
| Data de acesso e condições de uso | Download realizado em 09/11/2026. Referência de uso: política geral do DOT, que informa ausência de restrições de copyright e cobrança para suas publicações e solicita citação da fonte. [Política oficial](https://transportation.libanswers.com/faq/156950). |
| Filtros e passos de download/exportação | Descritos nas seções de preparação e reprodução abaixo |
| Mapeamento exato das colunas BTS para nosso CSV | Descrito na tabela abaixo |

#### Mapeamento das colunas

| Coluna original da BTS | Coluna no projeto |
| --- | --- |
| Reporting_Airline | companhia |
| Month | mes |
| DayOfWeek | dia_semana |
| CRSDepTime | hora_prevista |
| Distance | distancia |
| ArrDelay | atraso_chegada |
| Cancelled | cancelado |
| Diverted | desviado |

O horário previsto usa o formato HHMM local, a distância é medida
em milhas e o atraso de chegada em minutos. Atrasos negativos
representam chegadas antecipadas.

O mapeamento e as unidades foram conferidos no dicionário de dados
`readme.html`, incluído no ZIP original da BTS. Esse documento descreve
a tabela `Reporting Carrier On-Time Performance (1987-present)`.

Fonte dos dados: U.S. Department of Transportation, Bureau of
Transportation Statistics (BTS), Reporting Carrier On-Time Performance
(1987-present), janeiro de 2024. Acesso em 09/11/2026.

#### Preparação e tamanho da base

| Etapa | Registros removidos | Registros restantes |
| --- | ---: | ---: |
| Leitura do arquivo original | — | 547.271 |
| Remoção de duplicatas nas oito colunas | 10.858 | 536.413 |
| Exclusão de voos cancelados | 17.709 | 518.704 |
| Exclusão de voos desviados | 1.471 | 517.233 |
| Exclusão de outros registros inválidos ou sem atraso informado | 0 | 517.233 |

Após essas etapas, não foram encontrados atrasos de chegada
ausentes, indicadores inválidos, horários inválidos, meses ou
dias da semana inválidos, distâncias não positivas ou companhias vazias.

Os códigos das companhias foram padronizados em maiúsculas,
sem espaços nas extremidades.

Foi selecionada uma amostra aleatória de 20.000 registros,
sem reposição, com `random_state=42`:
- 15.106 voos com atraso inferior a 15 minutos.
- 4.894 voos com atraso de 15 minutos ou mais.

A amostra foi salva em `data/voos.csv`, com oito colunas,
codificação UTF-8, separador vírgula e sem índice adicional.
O ZIP original foi preservado em `data/brutos/`.

Limitação: registros iguais nas oito colunas podem representar
voos diferentes. A remoção dessas duplicatas segue o contrato
do projeto, mas pode excluir voos legítimos indistinguíveis
nesse recorte.

#### Como reproduzir a base

Execute os comandos abaixo no terminal, dentro da pasta do projeto.

1. Crie o ambiente virtual e instale a versão utilizada do Pandas:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install pandas==3.1.1
```

2. Crie a pasta para o arquivo original e faça o download:

```powershell
New-Item -ItemType Directory -Force data/brutos

curl.exe -f -L -o "data/brutos/bts_2024_01.zip" "https://www.transtats.bts.gov/PREZIP/On_Time_Reporting_Carrier_On_Time_Performance_1987_present_2024_1.zip"
```

3. Execute a preparação:

```powershell
.\.venv\Scripts\python.exe preparar_base.py
```

O script gera `data/voos.csv` com 20.000 registros e oito colunas.
Uma nova execução substitui esse CSV, mas preserva o ZIP original.

Verificação realizada por Leonardo Teles: duas execuções consecutivas
geraram arquivos `data/voos.csv` com o mesmo SHA-256, confirmando
a reprodução da amostra no ambiente utilizado.

CSV conferido: 20.000 registros, oito colunas e ambas as classes
de atraso presentes.

### Formato aceito no upload e no treino

CSV UTF-8, separador vírgula, decimal com ponto e cabeçalho obrigatório. O C01 converte a exportação BTS para este formato. O upload não precisa aceitar todos os formatos originais da BTS. Colunas extras serão ignoradas e informadas no relatório.

| Coluna | Tipo/unidade e validação | Finalidade |
| --- | --- | --- |
| `companhia` | Texto não vazio; remover espaços nas extremidades e converter para maiúsculas | X categórica |
| `mes` | Inteiro de 1 a 12 | X numérica |
| `dia_semana` | Inteiro de 1, segunda, até 7, domingo | X numérica |
| `hora_prevista` | Inteiro HHMM local, 0000–2359, minutos 00–59; normalizar 2400 para 0000 | Converter para minutos em X |
| `distancia` | Número positivo em milhas | X numérica |
| `atraso_chegada` | Número em minutos, pode ser negativo | Construir y; nunca X |
| `cancelado` | Inteiro 0 ou 1 | Filtro; nunca X |
| `desviado` | Inteiro 0 ou 1 | Filtro; nunca X |

Exemplo **ilustrativo**, não é dado real e não substitui a base de treino:

```csv
companhia,mes,dia_semana,hora_prevista,distancia,atraso_chegada,cancelado,desviado
AA,1,1,930,500,20,0,0
DL,1,2,1415,800,-5,0,0
```

O CSV entregue deve conter registros reais e ambas as classes. No formulário, preencher somente os cinco campos de X no formato original; ninguém informa o atraso futuro.

## Estrutura mínima e contratos de integração

Criar os arquivos conforme os cards forem executados:

```text
app.py                   # Pessoa 4: rotas
dados.py                 # Pessoa 1: leitura e limpeza
analise.py               # Pessoa 2: estatísticas e gráficos
treinar.py               # Pessoa 3: treino e comparação
modelo.py                # Pessoa 3: preparo de X e previsão
templates/
    index.html           # Pessoa 4: upload e previsão
    analise.html         # Pessoa 4: análise e avaliação
static/style.css         # Pessoa 4: estilo mínimo
data/voos.csv            # Pessoa 1: base documentada
models/modelo.joblib     # Pessoa 3: pipeline vencedor
models/avaliacao.json    # Pessoa 3: métricas e versão
requirements.txt         # Pessoa 4: dependências validadas
README.md
requisitos.md
```

Não acrescentar camadas ou classes sem necessidade concreta. Gráficos serão PNGs em memória, convertidos para base64 e exibidos no HTML. Não persistir uploads, gráficos nem DataFrames entre páginas. Resolver caminhos com `pathlib` a partir da pasta dos scripts, sem caminhos pessoais absolutos.

### Funções públicas

Estes nomes e retornos são acordos entre as quatro partes. Não importar Flask nos módulos de dados, análise ou modelo. Entradas inválidas geram `ValueError` com mensagem em português; Flask apresenta a mensagem.

```python
# dados.py
def carregar_e_limpar_csv(arquivo):
    """Recebe caminho ou arquivo binário; retorna (df_limpo, relatorio)."""

# analise.py
def analisar_dados(df_limpo):
    """Retorna dict com estatisticas, graficos e achados."""

# modelo.py
COLUNAS_X = ["companhia", "mes", "dia_semana", "minutos_previstos", "distancia"]

def preparar_entradas(df):
    """Valida os cinco campos originais de entrada e retorna X em COLUNAS_X."""

def carregar_modelo(caminho="models/modelo.joblib"):
    """Carrega o pipeline salvo, sem treinar."""

def prever_voo(campos, modelo):
    """Recebe dict do formulário e pipeline; retorna inteiro 0 ou 1."""
```

**Retornos e artefatos:**

- `df_limpo`: oito colunas normalizadas do contrato mais `atrasou` inteiro 0/1. `preparar_entradas` cria `minutos_previstos = (hora_prevista // 100) * 60 + hora_prevista % 100`; ela é usada no treino e na previsão, sem copiar a conversão.
- `relatorio`: dict com `linhas_antes`, `linhas_depois`, `colunas_recebidas`, `tipos_originais`, `ausentes_por_coluna`, `duplicatas_encontradas`, `remocoes` e `avisos`. `remocoes` é lista de dicts com `motivo` e `quantidade`, contadas sequencialmente sem dupla contagem. `avisos` é lista de textos.
- Resultado da análise: `estatisticas` é dict; `graficos` é lista de três dicts com `titulo`, `imagem_base64` e `interpretacao`; `achados` é lista de pelo menos três textos calculados com o CSV atual.
- `avaliacao.json`: `fonte`, `periodo`, `versao_base` (SHA-256 do CSV de treino), `quantidade_registros`, `colunas_x`, `test_size`, `random_state`, `tamanho_treino`, `tamanho_teste`, `distribuicao_classes_treino`, `distribuicao_classes_teste`, `baseline_teste`, `modelos`, `modelo_escolhido`, `justificativa`, `limitacoes`.
- `modelos` é lista com `nome`, `parametros`, `acuracia_treino`, `acuracia_teste`, `precisao`, `recall`, `f1`, `matriz_confusao`. Converter tipos NumPy para tipos JSON comuns.
- Matrizes usam ordem `[0, 1]`, linhas reais e colunas previstas, nomes “Sem atraso de 15 min” e “Com atraso de 15 min”. São adicionais aos três gráficos.

## Padrão de código obrigatório para os cards

1. Quatro espaços; nomes descritivos em português sem acentos e `snake_case`; constantes em maiúsculas.
2. Funções pequenas com uma responsabilidade e docstring curta explicando entrada/saída. Preferir passos explícitos; evitar expressões densas, lambdas desnecessárias, heranças e abstrações genéricas.
3. Comentar decisões e motivos, como exclusões e prevenção de vazamento. Não comentar cada comando óbvio.
4. Mensagens em português com unidades. Não usar exceções silenciosas, `except: pass` ou resultados inventados para esconder falhas.
5. Reutilizar a limpeza no upload/treino e o preparo de X no treino/previsão. Não duplicar regras entre módulos.
6. Treino executável protegido por `if __name__ == "__main__":`. Importar módulo não inicia treino nem servidor.
7. Dependências mínimas, sem notebooks obrigatórios nem arquitetura adicional. Não alterar contratos unilateralmente.
8. Cada integrante precisa conseguir explicar o código entregue; simplicidade tem prioridade sobre otimizações prematuras.

## Cards de execução

### C01 — Fixar fonte, período e base comum

**Pessoa 1 · Dependência: aprovação do professor · Status: [X] Concluído**

**Fazer:**

- Preparar proposta com tema, quatro nomes, fonte, pergunta, X, y, classificação e recorte. Registrar aprovação antes do desenvolvimento, conforme enunciado.
- Preencher a tabela de origem; conferir campos e unidades no dicionário oficial BTS.
- Mapear colunas originais para as oito colunas acordadas e entregar `data/voos.csv`. Se necessário, criar somente um script adicional `preparar_base.py` para reproduzir conversão e amostragem.
- Preservar o original. Documentar obtenção, filtros, amostragem, quantidade de registros e classes. Atualizar `.gitignore` para arquivos brutos grandes.
- Publicar o contrato antes de os colegas dependerem dele. Não deduplicar pelas cinco entradas: voos diferentes podem ter entradas iguais.

**Aceite:** outra pessoa consegue reproduzir o recorte; CSV tem registros reais e formato combinado; origem, condições de uso e aprovação estão registradas.

### C02 — Leitura, validação e limpeza

**Pessoa 1 · Depende de C01 · Arquivo: `dados.py` · Status: [X] Concluído**

**Fazer:**

- Implementar `carregar_e_limpar_csv`. Rejeitar vazio, CSV sem registros, codificação/separador incorretos e colunas obrigatórias ausentes com mensagens compreensíveis.
- Registrar tipos, ausentes e duplicatas. Converter números explicitamente; normalizar companhia e horário conforme o contrato.
- Remover sequencialmente: duplicatas exatas nas oito colunas; indicadores inválidos; cancelados; desviados; demais linhas com entradas ausentes/incompatíveis ou atraso ausente/inválido. Registrar contagem por motivo.
- Explicar a limitação: duplicatas exatas no recorte podem representar voos legítimos indistinguíveis. Não preencher alvo ausente com zero. Para simplificar, excluir linhas inválidas em vez de aprender imputação.
- Criar `atrasou` e retornar o relatório contratado. Se nenhuma linha válida restar, gerar erro amigável. Uma só classe pode ser analisada; treino deve recusá-la.

**Aceite:** conferir CSV válido, vazio, cabeçalho errado, separador ponto e vírgula, número inválido, horário `1260`, horário `2400`, cancelado, desviado, atraso ausente e duplicata. Contagens antes/depois devem fechar, e o original permanece intacto.

#### Verificações realizadas — C02

Responsável: Leonardo Teles.

| Cenário | Resultado |
| --- | --- |
| CSV válido | 20.000 registros e nove colunas, incluindo `atrasou` |
| Arquivo vazio ou somente com cabeçalho | Rejeitado com mensagem compreensível |
| Coluna obrigatória ausente | Nome da coluna informado no erro |
| Separador ponto e vírgula | Rejeitado |
| Codificação inválida e aspas sem fechamento | Rejeitadas com mensagens compreensíveis |
| Coluna extra | Ignorada e registrada no relatório |
| Duplicata | Removida e contabilizada |
| Companhia com espaços e letras minúsculas | Normalizada |
| Número inválido ou infinito | Convertido em ausente para validação |
| Indicador inválido, cancelado e desviado | Removidos na ordem prevista |
| Horário 1260 e distância negativa | Linha removida sem dupla contagem |
| Horário 2400 | Convertido para 0 |
| Atraso de chegada ausente | Linha removida |
| Nenhuma linha válida restante | Erro compreensível |
| Atrasos de -5, 14 e 15 minutos | Classes 0, 0 e 1 |
| Base com uma classe | Mantida para análise, com aviso |
| Contagens de remoção | 7 entradas = 6 removidas + 1 válida |
| Preservação do CSV original | SHA-256 igual antes e depois da limpeza |
| Integração com preparar_base.py | Mesmas contagens e distribuição de classes do C01 |

### C03 — Estatísticas, três gráficos e três achados

**Pessoa 2 · Depende de C02; preparação após C01 · Arquivo: `analise.py` · Status: [ ] Concluído**

**Fazer:**

- Implementar `analisar_dados`. Calcular quantidade de voos, taxa de atraso, resumo de distância/atraso e agrupamentos por companhia.
- **Distribuição:** histograma do atraso de chegada em minutos; interpretar concentração, dispersão e extremos.
- **Comparação:** barras da porcentagem de atrasos por companhia; apresentar também tamanho de cada grupo para contextualizar companhias com poucos registros.
- **Relação:** boxplot da distância em milhas por classe de atraso; explicar diferenças ou sobreposição sem afirmar causalidade.
- Todo gráfico tem título, eixos/unidades e interpretação. Criar pelo menos três achados quantitativos calculados a partir do upload, sem números fixos da base original.
- Usar Matplotlib com backend `Agg`, PNG em memória e base64. Fechar figuras após uso. Tratar dados pequenos e uma só classe sem inventar comparações.

**Aceite:** dois CSVs diferentes geram resultados correspondentes; títulos, eixos e porcentagens corretos; sem acumular figuras abertas. Matriz de confusão não conta entre estes três gráficos.

### C04 — Comparar dois modelos e avaliar

**Pessoa 3 · Depende de C02 · Arquivos: `treinar.py`, preparo em `modelo.py`, `models/avaliacao.json` · Status: [ ] Concluído**

**Fazer:**

- Usar limpeza real e implementar `preparar_entradas`. Justificar cada X. Registrar que um mês isolado não permite aprender diferenças entre meses.
- Pesquisar e citar documentação oficial scikit-learn para **DecisionTreeClassifier** e **LogisticRegression**, explicando funcionamento e adequação.
- Configuração inicial simples: árvore com `max_depth=5, random_state=42`; regressão logística com `max_iter=1000, random_state=42`. Registrar parâmetros e eventuais ajustes necessários por falha de convergência.
- Verificar duas classes e quantidade suficiente por classe. Usar uma única divisão `train_test_split(test_size=0.20, random_state=42, stratify=y)` para ambos.
- Cada modelo usa `Pipeline`/`ColumnTransformer`: companhia com `OneHotEncoder(handle_unknown="ignore")`; quatro entradas numéricas com `StandardScaler`. Ajustar transformações apenas no treino, dentro dos pipelines.
- Avaliar acurácia de treino/teste, precisão, recall e F1 da classe atrasada, tratando divisão por zero. Mostrar tamanho/distribuição do teste e baseline da classe majoritária. Produzir as duas matrizes de confusão.
- Critério principal de escolha: F1 da classe atrasada, equilibrando precisão e recall; em empate preferir regressão logística. Relatar também acurácia exigida, erros e eventual overfitting. Não tentar sucessivos ajustes para decorar o teste.
- Preencher `avaliacao.json` com resultados reais, justificativa, versão da base e limitações. Explicar falsos positivos e falsos negativos no contexto dos voos.

**Aceite:** treino reproduzível; mesma divisão para ambos; nenhum dado pós-voo em X; comparação completa com baseline e matrizes. Não inventar métricas nem prometer desempenho.

### C05 — Persistência e previsão de um voo

**Pessoa 3 · Depende de C04 · Arquivos: `modelo.py`, `models/modelo.joblib` · Status: [ ] Concluído**

**Fazer:**

- Salvar com joblib o pipeline vencedor ajustado no treino avaliado. Nesta versão, não refazer o ajuste na base completa: manter coerência com as métricas exibidas.
- Implementar `carregar_modelo` e `prever_voo`, convertendo e validando campos do formulário; chamar o mesmo preparo de X e depois `predict`.
- Preservar nomes, ordem e tipos. Oferecer no formulário companhias da base treinada; orientar a pessoa 4 a obter as categorias do encoder. Para companhia nova, o encoder aceita, mas a interface deve avisar que ela não foi vista no treino.
- Carregar apenas o artefato produzido pelo projeto, nunca joblib enviado por usuário.

**Aceite:** salvar/recarregar mantém a previsão para a mesma entrada; saída inteira 0/1; companhia vazia, mês 13, horário inválido e distância negativa geram mensagens claras. Importar o módulo não treina.

### C06 — Flask, páginas e integração

**Pessoa 4 · Pode iniciar pelos contratos; conclusão depende de C02, C03 e C05 · Status: [ ] Concluído**

**Arquivos:** `app.py`, `templates/index.html`, `templates/analise.html`, `static/style.css`.

**Fazer:**

- `GET /`: upload, esquema do CSV, formulário dos cinco campos, fonte/período/versão do treino e aviso de que uploads não retreinam o modelo.
- `POST /analisar`: arquivo no campo `arquivo`; validar extensão `.csv` e limite de 10 MB; chamar limpeza/análise e renderizar a página de resultados. Tratar excesso de tamanho e erros esperados em português.
- Na análise: primeiras dez linhas válidas, quantidade de registros/colunas, diagnóstico e remoções, estatísticas, três gráficos, interpretações e três achados.
- Exibir comparação dos modelos e as duas matrizes em tabelas HTML com nomes/eixos, baseline, tamanho/distribuição do teste, justificativa e limitações. Deixar claro que essa avaliação pertence ao treino fixo, não ao upload.
- `POST /prever`: ler os cinco campos, validar no servidor e chamar previsão real. Mostrar na página inicial “Com atraso de 15 min” ou “Sem atraso de 15 min”, como estimativa didática.
- Carregar o modelo uma vez ao iniciar. Se artefatos faltarem, mostrar instrução para executar treino; manter análise de CSV disponível, omitindo avaliação ausente e bloqueando previsão até existir modelo.
- Navegação simples de volta ao início, rótulos/unidades e mensagens amigáveis sem traceback. Não guardar uploads ou DataFrames em variáveis globais.

**Aceite:** upload → diagnóstico → gráficos → voltar → previsão real. Fluxo não usa resultados simulados. Entradas inválidas não derrubam a aplicação.

### C07 — Execução reproduzível e revisão

**Pessoa 4, revisada pelas pessoas 1–3 · Depende de C06 · Status: [ ] Concluído**

**Fazer:**

- Criar `requirements.txt` com versões exatas realmente validadas de Flask, pandas, matplotlib, scikit-learn, joblib e demais dependências diretas usadas.
- Registrar Python/sistema e validar os comandos abaixo. Outro integrante deve instalar e executar do zero usando somente este README.
- Conferir CSV de exemplo, obtenção do original, caminhos relativos e `.gitignore` para ambiente virtual/caches. Complementar README com comparação real, escolha, erros, limitações, fontes, códigos adaptados e uso de IA.
- Registrar verificações numa tabela com cenário, resultado e responsável. Roteiro manual basta para a interface; sem Selenium/Playwright. Verificações pequenas de dados/modelo somente quando detectarem erros reais.

**Aceite:** instalação, treino e aplicação reproduzidos por outro integrante; todos os critérios abaixo têm evidência; nenhum campo obrigatório fica pendente na entrega final.

### C08 — Apresentação e defesa individual

**Todos · Depende de C07 · Status: [ ] Concluído**

**Fazer:**

- Ensaiar: pergunta/fonte → iniciar pelo README → upload válido → limpeza e gráficos → upload inválido tratado → comparação/erros → nova previsão → limitações.
- Todos explicam X/y, limpeza, vazamento, treino/teste, os dois algoritmos, métricas e integração, além da contribuição individual. Localizar o código e explicar em linguagem própria.
- Discutir limitações: mês/amostra restritos, ausência de clima/aeroportos/outras influências e previsão sem garantia de resultado.
- Confirmar prazo/data com o professor; registrar commit final e entregar link do GitHub no Blackboard. Alterações posteriores na versão avaliada exigem autorização do professor.

**Aceite:** quatro integrantes conseguem explicar e executar o projeto. O enunciado prevê zero individual para quem não explicar o código.

## Execução planejada — validar no C07

Comandos pressupõem os arquivos futuros; **ainda não foram validados**:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe treinar.py
.\.venv\Scripts\python.exe app.py
```

Abrir `http://127.0.0.1:5000`. Antes do treino, obter `data/voos.csv` conforme C01. O treino cria `models/` se necessário e grava pipeline e avaliação.

| Registro final | Situação |
| --- | --- |
| Python e sistema testados | Pendente |
| Comandos verificados por | Pendente |
| Modelo escolhido, métricas e interpretação dos erros | Pendente: resumir resultados reais do C04 |
| Fontes e códigos adaptados | Pendente |
| Uso de IA por integrante | Plano deste README elaborado com auxílio do Codex; complementar contribuições reais |
| Commit final de entrega | Pendente |

## Conferência da pontuação

| Critério | Pontos | Evidência | Cards |
| --- | --- | --- | --- |
| Flask e funcionamento | 0,75 | Upload, rotas, mensagens | C02, C06 |
| Tratamento e análise | 0,75 | Diagnóstico, antes/depois, justificativas e achados | C01–C03 |
| Visualizações | 0,50 | Três gráficos legíveis e interpretados | C03, C06 |
| Machine Learning | 1,25 | X/y, divisão, dois modelos, avaliação e escolha | C04 |
| Previsão integrada | 0,50 | Formulário validado e pipeline real | C05, C06 |
| Organização/documentação | 0,25 | Código simples e execução reproduzível | C01, C07 |
| Apresentação/defesa | 1,00 | Demonstração e domínio dos quatro | C08 |
| **Total** | **5,00** | | |

## Como pedir ajuda à IA em cada card

Informar o ID do card e pedir leitura deste README inteiro e dos requisitos relacionados. Exemplo:

> Sou a pessoa 2, responsável pelo C03. Leia README.md e requisitos.md e confira os arquivos existentes. Implemente minha entrega respeitando contratos, padrão simples e critérios de aceite. Não invente dados, métricas ou conclusões nem reescreva a parte dos colegas. Se uma dependência ainda não existir, use o contrato para preparar minha parte e registre integração pendente. Ao concluir, explique arquivos alterados, verificações feitas e o que preciso entender para defender o código.

Marcar um card como concluído somente após conferir seus critérios com as funções reais. Registrar pendências explicitamente; uma simulação não conclui a integração.
