# Pandas monta as entradas; scikit-learn prepara, treina e avalia os modelos.
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, mean_absolute_error, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


# Mantemos a mesma ordem das entradas no treinamento e na previsao.
COLUNAS_X = ["Reporting_Airline", "Month", "DayofWeek", "HorarioMinutos", "Distance"]


# Junta o tratamento das colunas ao algoritmo que aprendera com os dados.
def _preparar_modelo(estimador, escalar_numeros=False):
    # Cada modelo recebe seu proprio preparo, ajustado apenas com o treino.
    preparo_numerico = StandardScaler() if escalar_numeros else "passthrough"
    # OneHotEncoder(): transforma companhias em colunas numericas.
    # handle_unknown="ignore": aceita uma categoria que nao apareceu no treino.
    # COLUNAS_X[1:]: seleciona todas as entradas numericas, depois da companhia.
    preparo = ColumnTransformer([
        ("categorias", OneHotEncoder(handle_unknown="ignore"), [COLUNAS_X[0]]),
        ("numeros", preparo_numerico, COLUNAS_X[1:]),
    ])
    # Pipeline(): aplica o mesmo preparo no fit() e no predict(), evitando vazamento.
    return Pipeline([
        ("preparo", preparo),
        ("modelo", estimador),
    ])


# Treina um classificador e compara suas respostas com os valores reais do teste.
def _avaliar(nome, pipeline, X_treino, X_teste, y_treino, y_teste):
    pipeline.fit(X_treino, y_treino)
    previsoes = pipeline.predict(X_teste)
    # Precisao: acertos entre os atrasos previstos. Recall: atrasos reais identificados.
    # F1 combina precisao e recall; zero_division=0 evita divisao por zero.
    # Na matriz, a ordem e 0 (sem atraso) e 1 (com atraso), nas linhas e colunas.
    return {
        "nome": nome,
        "modelo": pipeline,
        "acuracia": accuracy_score(y_teste, previsoes),
        "precisao": precision_score(y_teste, previsoes, zero_division=0),
        "recall": recall_score(y_teste, previsoes, zero_division=0),
        "f1": f1_score(y_teste, previsoes, zero_division=0),
        "matriz": confusion_matrix(y_teste, previsoes, labels=[0, 1]).tolist(),
    }


# Treina os dois modelos com a mesma divisao para permitir uma comparacao justa.
def treinar_modelos(dados):
    # X contem informacoes anteriores ao voo; y contem a resposta conhecida.
    X = dados[COLUNAS_X]
    y = dados["Atrasado"]
    if y.nunique() < 2:
        raise ValueError("A base de treino precisa possuir voos com e sem atraso.")

    # Reservamos 20% para testar. stratify preserva a proporcao das classes.
    # random_state fixo permite repetir a mesma divisao em outras execucoes.
    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    # balanced aumenta o peso da classe menos frequente no treinamento.
    # max_depth limita a profundidade da arvore para reduzir a memorizacao.
    arvore = _preparar_modelo(
        DecisionTreeClassifier(max_depth=6, class_weight="balanced", random_state=42)
    )
    # A regressao logistica recebe numeros padronizados pelo StandardScaler.
    logistica = _preparar_modelo(
        LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42),
        escalar_numeros=True,
    )

    resultados = [
        _avaliar("Arvore de Decisao", arvore, X_treino, X_teste, y_treino, y_teste),
        _avaliar("Regressao Logistica", logistica, X_treino, X_teste, y_treino, y_teste),
    ]
    # Em caso de empate, a arvore aparece primeiro e permanece escolhida.
    escolhido = max(resultados, key=lambda resultado: resultado["f1"])

    # Este modelo adicional estima quantos minutos o voo pode atrasar.
    # A classificacao continua sendo comparada acima, conforme o tema do trabalho.
    # loc seleciona os mesmos registros da divisao anterior, agora com o atraso em minutos.
    y_minutos_treino = dados.loc[X_treino.index, "ArrDelay"]
    y_minutos_teste = dados.loc[X_teste.index, "ArrDelay"]
    # A floresta combina 100 arvores. n_jobs=-1 utiliza os processadores disponiveis.
    modelo_minutos = _preparar_modelo(
        RandomForestRegressor(n_estimators=100, max_depth=10, min_samples_leaf=5, random_state=42, n_jobs=-1)
    )
    modelo_minutos.fit(X_treino, y_minutos_treino)
    minutos_previstos = modelo_minutos.predict(X_teste)

    # Guardamos os modelos e os resultados usados na pagina. MAE e o erro medio em minutos.
    return {
        "modelo": escolhido["modelo"],
        "modelo_minutos": modelo_minutos,
        "mae_minutos": mean_absolute_error(y_minutos_teste, minutos_previstos),
        "nome_escolhido": escolhido["nome"],
        "resultados": resultados,
        "tamanho_treino": len(X_treino),
        "tamanho_teste": len(X_teste),
        "classe_majoritaria": y_teste.value_counts(normalize=True).max(),
        "companhias": sorted(dados["Reporting_Airline"].unique().tolist()),
    }


# Monta uma linha com os campos do formulario e retorna a estimativa em minutos.
def prever_atraso(modelo, companhia, mes, dia_semana, horario_minutos, distancia):
    entrada = pd.DataFrame(
        [[companhia, mes, dia_semana, horario_minutos, distancia]], columns=COLUNAS_X
    )
    return float(modelo.predict(entrada)[0])
