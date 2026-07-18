#!/usr/bin/env python3
"""
Validador de Qualidade de Dados
===============================
Gera um relatório de qualidade (data profiling) em Markdown para qualquer CSV:
estrutura, valores ausentes, duplicatas, colunas constantes, alta cardinalidade
e outliers numéricos pelo critério IQR.

Uso:
    python validador_qualidade_dados.py --input train.csv --output relatorio.md
"""

import argparse
import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


def analisar_nulos(df: pd.DataFrame) -> pd.DataFrame:
    """Retorna contagem e percentual de nulos por coluna (apenas colunas com nulos)."""
    nulos = df.isnull().sum()
    resultado = pd.DataFrame(
        {"coluna": nulos.index, "nulos": nulos.values, "pct": (nulos / len(df) * 100).round(2).values}
    )
    return resultado[resultado["nulos"] > 0].sort_values("pct", ascending=False).reset_index(drop=True)


def analisar_duplicatas(df: pd.DataFrame) -> int:
    """Retorna a quantidade de linhas duplicadas exatas."""
    return int(df.duplicated().sum())


def analisar_constantes(df: pd.DataFrame) -> list[str]:
    """Colunas com um único valor distinto (não agregam informação)."""
    return [c for c in df.columns if df[c].nunique(dropna=False) <= 1]


def analisar_cardinalidade(df: pd.DataFrame, limite: float = 0.9) -> list[str]:
    """Colunas de texto quase únicas por linha (possíveis identificadores)."""
    suspeitas = []
    for c in df.columns:
        eh_texto = pd.api.types.is_object_dtype(df[c]) or pd.api.types.is_string_dtype(df[c])
        if eh_texto and df[c].nunique() / len(df) >= limite:
            suspeitas.append(c)
    return suspeitas


def analisar_outliers_iqr(df: pd.DataFrame) -> pd.DataFrame:
    """Conta outliers por coluna numérica usando o critério 1,5 x IQR."""
    linhas = []
    for c in df.select_dtypes(include="number").columns:
        serie = df[c].dropna()
        if serie.empty:
            continue
        q1, q3 = serie.quantile([0.25, 0.75])
        iqr = q3 - q1
        inf, sup = q1 - 1.5 * iqr, q3 + 1.5 * iqr
        outliers = int(((serie < inf) | (serie > sup)).sum())
        if outliers:
            linhas.append(
                {"coluna": c, "outliers": outliers, "pct": round(outliers / len(serie) * 100, 2),
                 "limite_inf": round(inf, 2), "limite_sup": round(sup, 2)}
            )
    return pd.DataFrame(linhas).sort_values("outliers", ascending=False).reset_index(drop=True) if linhas else pd.DataFrame()


def _tabela_md(df: pd.DataFrame) -> str:
    return df.to_markdown(index=False) if not df.empty else "_Nenhuma ocorrência._"


def gerar_relatorio(df: pd.DataFrame, origem: str) -> str:
    """Monta o relatório completo em Markdown."""
    nulos = analisar_nulos(df)
    duplicatas = analisar_duplicatas(df)
    constantes = analisar_constantes(df)
    alta_card = analisar_cardinalidade(df)
    outliers = analisar_outliers_iqr(df)

    tipos = df.dtypes.astype(str).to_frame("tipo").reset_index(names="coluna")
    memoria_mb = df.memory_usage(deep=True).sum() / 1024**2

    return f"""# Relatório de Qualidade de Dados

- **Arquivo:** `{origem}`
- **Gerado em:** {datetime.now():%d/%m/%Y %H:%M}
- **Dimensões:** {len(df):,} linhas x {df.shape[1]} colunas
- **Memória:** {memoria_mb:.2f} MB
- **Linhas duplicadas:** {duplicatas}

## Tipos de dados

{_tabela_md(tipos)}

## Valores ausentes

{_tabela_md(nulos)}

## Colunas constantes

{"`" + "`, `".join(constantes) + "`" if constantes else "_Nenhuma._"}

## Alta cardinalidade (possíveis identificadores)

{"`" + "`, `".join(alta_card) + "`" if alta_card else "_Nenhuma._"}

## Outliers numéricos (critério 1,5 x IQR)

{_tabela_md(outliers)}
"""


def main() -> None:
    parser = argparse.ArgumentParser(description="Gera relatório de qualidade de dados em Markdown.")
    parser.add_argument("--input", required=True, type=Path, help="CSV a ser analisado")
    parser.add_argument("--output", type=Path, default=Path("relatorio_qualidade.md"), help="Arquivo Markdown de saída")
    args = parser.parse_args()

    if not args.input.exists():
        print(f"[ERRO] Arquivo não encontrado: {args.input}", file=sys.stderr)
        sys.exit(1)

    df = pd.read_csv(args.input)
    args.output.write_text(gerar_relatorio(df, args.input.name), encoding="utf-8")
    print(f"[OK] Relatório gerado: {args.output}")


if __name__ == "__main__":
    main()
