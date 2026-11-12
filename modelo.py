import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, confusion_matrix, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier


COLUNAS_X = ["Reporting_Airline", "Month", "DayofWeek", "HorarioMinutos", "Distance"]


def _criar_preparo(escalar_numeros=False):
    categorias = ["Reporting_Airline"]
    numeros = ["Month", "DayofWeek", "HorarioMinutos", "Distance"]
    preparo_numerico = StandardScaler() if escalar_numeros else "passthrough"
    return ColumnTransformer([
        ("categorias", OneHotEncoder(handle_unknown="ignore"), categorias),
        ("numeros", preparo_numerico, numeros),
    ])


def _avaliar(nome, pipeline, X_treino, X_teste, y_treino, y_teste):
    pipeline.fit(X_treino, y_treino)
    previsoes = pipeline.predict(X_teste)
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
    X = dados[COLUNAS_X]
    y = dados["Atrasado"]
    if y.nunique() < 2:
        raise ValueError("A base de treino precisa possuir voos com e sem atraso.")

    X_treino, X_teste, y_treino, y_teste = train_test_split(
        X, y, test_size=0.20, random_state=42, stratify=y
    )

    arvore = Pipeline([
        ("preparo", _criar_preparo()),
        ("modelo", DecisionTreeClassifier(max_depth=6, class_weight="balanced", random_state=42)),
    ])
    logistica = Pipeline([
        ("preparo", _criar_preparo(escalar_numeros=True)),
        ("modelo", LogisticRegression(max_iter=1000, class_weight="balanced", random_state=42)),
    ])

    resultados = [
        _avaliar("Arvore de Decisao", arvore, X_treino, X_teste, y_treino, y_teste),
        _avaliar("Regressao Logistica", logistica, X_treino, X_teste, y_treino, y_teste),
    ]
    # Em caso de empate, a arvore aparece primeiro e permanece escolhida.
    escolhido = max(resultados, key=lambda resultado: resultado["f1"])

    return {
        "modelo": escolhido["modelo"],
        "nome_escolhido": escolhido["nome"],
        "resultados": resultados,
        "tamanho_treino": len(X_treino),
        "tamanho_teste": len(X_teste),
        "classe_majoritaria": y_teste.value_counts(normalize=True).max(),
        "companhias": sorted(dados["Reporting_Airline"].unique().tolist()),
    }


def prever_atraso(modelo, companhia, mes, dia_semana, horario_minutos, distancia):
    entrada = pd.DataFrame([{
        "Reporting_Airline": companhia,
        "Month": mes,
        "DayofWeek": dia_semana,
        "HorarioMinutos": horario_minutos,
        "Distance": distancia,
    }])
    return int(modelo.predict(entrada)[0])
