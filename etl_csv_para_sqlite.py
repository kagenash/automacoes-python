#!/usr/bin/env python3
"""
ETL: CSV -> SQLite
==================
Pipeline de carga que lê um CSV, aplica transformações de limpeza e grava o
resultado em um banco SQLite, com log detalhado de cada etapa e validação
do volume carregado.

Transformações aplicadas:
- Normalização dos nomes de colunas para snake_case;
- Remoção de espaços extras em colunas de texto;
- Remoção de linhas duplicadas exatas;
- Coluna de auditoria ``etl_carregado_em`` com o timestamp da carga.

Uso:
    python etl_csv_para_sqlite.py --input train.csv --db titanic.db --tabela passageiros
    python etl_csv_para_sqlite.py --input vendas.csv --db dw.db --tabela vendas --if-exists append
"""

import argparse
import logging
import re
import sqlite3
import sys
import time
from datetime import datetime
from pathlib import Path

import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-7s | %(message)s",
    handlers=[logging.StreamHandler(), logging.FileHandler("etl.log", encoding="utf-8")],
)
log = logging.getLogger(__name__)


def normalizar_colunas(df: pd.DataFrame) -> pd.DataFrame:
    """Converte os nomes das colunas para snake_case (ex.: 'PassengerId' -> 'passenger_id')."""
    def snake(nome: str) -> str:
        nome = re.sub(r"(.)([A-Z][a-z]+)", r"\1_\2", str(nome).strip())
        nome = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", nome)
        return re.sub(r"[^\w]+", "_", nome).lower().strip("_")

    return df.rename(columns={c: snake(c) for c in df.columns})


def transformar(df: pd.DataFrame) -> pd.DataFrame:
    """Aplica as transformações de limpeza e adiciona a coluna de auditoria."""
    linhas_inicial = len(df)
    df = normalizar_colunas(df)

    # Limpeza de espaços em colunas de texto (seguro para conteúdo misto)
    colunas_texto = [c for c in df.columns
                     if pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])]
    for col in colunas_texto:
        df[col] = df[col].map(lambda v: v.strip() if isinstance(v, str) else v)

    # Remoção de duplicatas exatas
    df = df.drop_duplicates()
    removidas = linhas_inicial - len(df)
    if removidas:
        log.warning("Removidas %d linha(s) duplicada(s)", removidas)

    df["etl_carregado_em"] = datetime.now().isoformat(timespec="seconds")
    return df


def carregar(df: pd.DataFrame, db: Path, tabela: str, if_exists: str) -> int:
    """Grava o DataFrame no SQLite e valida o total de linhas persistidas."""
    with sqlite3.connect(db) as conn:
        df.to_sql(tabela, conn, if_exists=if_exists, index=False)
        total = conn.execute(f'SELECT COUNT(*) FROM "{tabela}"').fetchone()[0]
    return total


def executar_pipeline(entrada: Path, db: Path, tabela: str, if_exists: str) -> None:
    inicio = time.perf_counter()
    log.info("Iniciando ETL | origem=%s | destino=%s.%s", entrada, db, tabela)

    # Extract
    df = pd.read_csv(entrada)
    log.info("Extract: %d linhas x %d colunas lidas", *df.shape)

    # Transform
    df = transformar(df)
    log.info("Transform: %d linhas após limpeza", len(df))

    # Load
    total = carregar(df, db, tabela, if_exists)
    log.info("Load: tabela '%s' contém %d linha(s) após a carga", tabela, total)

    log.info("Pipeline concluído em %.2fs", time.perf_counter() - inicio)


def main() -> None:
    parser = argparse.ArgumentParser(description="ETL de CSV para SQLite com limpeza e auditoria.")
    parser.add_argument("--input", required=True, type=Path, help="Caminho do CSV de origem")
    parser.add_argument("--db", required=True, type=Path, help="Arquivo SQLite de destino")
    parser.add_argument("--tabela", required=True, help="Nome da tabela de destino")
    parser.add_argument(
        "--if-exists",
        choices=["replace", "append", "fail"],
        default="replace",
        help="Comportamento se a tabela já existir (padrão: replace)",
    )
    args = parser.parse_args()

    if not args.input.exists():
        log.error("Arquivo de entrada não encontrado: %s", args.input)
        sys.exit(1)

    try:
        executar_pipeline(args.input, args.db, args.tabela, args.if_exists)
    except Exception as exc:  # noqa: BLE001 - borda do CLI: loga e sai com erro
        log.exception("Falha no pipeline: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
