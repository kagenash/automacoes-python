# Relatório de Qualidade de Dados

- **Arquivo:** `train.csv`
- **Gerado em:** 17/07/2026 17:09
- **Dimensões:** 891 linhas x 12 colunas
- **Memória:** 0.28 MB
- **Linhas duplicadas:** 0

## Tipos de dados

| coluna      | tipo    |
|:------------|:--------|
| PassengerId | int64   |
| Survived    | int64   |
| Pclass      | int64   |
| Name        | str     |
| Sex         | str     |
| Age         | float64 |
| SibSp       | int64   |
| Parch       | int64   |
| Ticket      | str     |
| Fare        | float64 |
| Cabin       | str     |
| Embarked    | str     |

## Valores ausentes

| coluna   |   nulos |   pct |
|:---------|--------:|------:|
| Cabin    |     687 | 77.1  |
| Age      |     177 | 19.87 |
| Embarked |       2 |  0.22 |

## Colunas constantes

_Nenhuma._

## Alta cardinalidade (possíveis identificadores)

`Name`

## Outliers numéricos (critério 1,5 x IQR)

| coluna   |   outliers |   pct |   limite_inf |   limite_sup |
|:---------|-----------:|------:|-------------:|-------------:|
| Parch    |        213 | 23.91 |         0    |         0    |
| Fare     |        116 | 13.02 |       -26.72 |        65.63 |
| SibSp    |         46 |  5.16 |        -1.5  |         2.5  |
| Age      |         11 |  1.54 |        -6.69 |        64.81 |
