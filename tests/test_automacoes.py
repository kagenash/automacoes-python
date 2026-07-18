"""Testes unitários das automações de dados (pytest).

Execução, a partir da raiz do projeto:
    pytest -v
"""

import sqlite3
import sys
from pathlib import Path

import pandas as pd
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from etl_csv_para_sqlite import carregar, normalizar_colunas, transformar
from validador_qualidade_dados import (
    analisar_cardinalidade,
    analisar_constantes,
    analisar_duplicatas,
    analisar_nulos,
    analisar_outliers_iqr,
)


@pytest.fixture
def df_sujo() -> pd.DataFrame:
    """DataFrame com problemas conhecidos: duplicata, nulos, espaços e coluna constante."""
    return pd.DataFrame({
        "PassengerId": [1, 2, 2, 4, 5],
        "NomeCompleto": ["  Ana ", "Bruno", "Bruno", "Carla", None],
        "Idade": [30, None, None, 25, 40],
        "Origem": ["arquivo"] * 5,
    }).pipe(lambda d: pd.concat([d, d.iloc[[2]]], ignore_index=True))  # linha 2 duplicada de fato


# ---------------------------------------------------------------- ETL ----
def test_normalizar_colunas_converte_para_snake_case(df_sujo):
    colunas = normalizar_colunas(df_sujo).columns.tolist()
    assert colunas == ["passenger_id", "nome_completo", "idade", "origem"]


def test_transformar_remove_duplicatas_e_espacos(df_sujo):
    resultado = transformar(df_sujo)
    assert resultado.duplicated().sum() == 0
    assert resultado["nome_completo"].iloc[0] == "Ana"
    assert "etl_carregado_em" in resultado.columns


def test_carregar_persiste_no_sqlite(tmp_path, df_sujo):
    db = tmp_path / "teste.db"
    df = transformar(df_sujo)
    total = carregar(df, db, "clientes", if_exists="replace")
    assert total == len(df)

    with sqlite3.connect(db) as conn:
        colunas = [c[1] for c in conn.execute("PRAGMA table_info(clientes)")]
    assert "etl_carregado_em" in colunas


# ---------------------------------------------------- Validador ----------
def test_analisar_nulos_detecta_percentuais(df_sujo):
    nulos = analisar_nulos(df_sujo).set_index("coluna")
    assert nulos.loc["Idade", "nulos"] == 3  # 2 originais + 1 da duplicata
    assert nulos.loc["NomeCompleto", "nulos"] == 1


def test_analisar_duplicatas_conta_linhas_exatas(df_sujo):
    assert analisar_duplicatas(df_sujo) == 2  # 'Bruno' repetido + linha concatenada


def test_analisar_constantes_identifica_coluna_sem_variacao(df_sujo):
    assert analisar_constantes(df_sujo) == ["Origem"]


def test_analisar_cardinalidade_flag_identificadores():
    df = pd.DataFrame({"id_texto": [f"id_{i}" for i in range(100)], "uf": ["SP"] * 100})
    assert analisar_cardinalidade(df) == ["id_texto"]


def test_analisar_outliers_iqr_detecta_valor_extremo():
    df = pd.DataFrame({"valor": [10, 11, 9, 10, 12, 11, 10, 500]})
    outliers = analisar_outliers_iqr(df).set_index("coluna")
    assert outliers.loc["valor", "outliers"] == 1
